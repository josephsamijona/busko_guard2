# presence/tasks.py
from celery import shared_task

from django.conf import settings
from django.core.files.base import ContentFile
import pandas as pd
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from celery import shared_task
from django.core.mail import send_mail
from .models import User, Leave, AttendanceRecord, Notification, NFCReader,Reportfolder, ReportSchedule, AttendanceRecord, Department, User
from .attendaceutils import calculate_attendance
from pythonping import ping
from django.utils import timezone
from datetime import date, timedelta

@shared_task
def ping_nfc_readers():
    readers = NFCReader.objects.all()
    for reader in readers:
        ip = reader.ip_address
        if not ip:
            continue  # Pas d'adresse IP définie
        try:
            response = ping(ip, count=1, timeout=2)
            if response.success():
                reader.is_online = True
                reader.status = NFCReader.ReaderStatus.ACTIVE
            else:
                reader.is_online = False
                reader.status = NFCReader.ReaderStatus.ERROR
            reader.last_online = timezone.now()
            reader.save()
        except Exception as e:
            reader.is_online = False
            reader.status = NFCReader.ReaderStatus.ERROR
            reader.save()

@shared_task
def detect_early_departures():
    """
    Détecte les abandons de poste (départ avant l'heure prévue).
    """
    today = date.today()
    users = User.objects.all()

    for user in users:
        # Vérifier s'il est en congé aujourd'hui
        on_leave = Leave.objects.filter(
            user=user,
            status=Leave.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today
        ).exists()

        if on_leave:
            continue  # Pas d'abandon si en congé

        # Calculer la présence
        attendance = calculate_attendance(user, today)

        # Définir l'heure de départ prévue (par exemple, 17:00)
        expected_departure_time = timezone.datetime.combine(today, timezone.datetime.strptime('17:00', '%H:%M').time()).time()

        # Obtenir l'heure de départ réelle
        departure_record = AttendanceRecord.objects.filter(
            user=user,
            timestamp__date=today,
            action_type=AttendanceRecord.Status.DEPARTURE
        ).first()

        if departure_record:
            actual_departure_time = departure_record.timestamp.time()
            if actual_departure_time < expected_departure_time:
                # Créer une notification pour abandon de poste
                Notification.objects.create(
                    recipient=user,
                    message=f"Vous avez quitté le poste avant l'heure prévue ({actual_departure_time.strftime('%H:%M')} au lieu de {expected_departure_time.strftime('%H:%M')}).",
                    notification_type='early_departure'
                )

@shared_task
def detect_missed_scans():
    """
    Détecte les oublis de scan (partie sans scanner).
    """
    today = date.today()
    users = User.objects.all()

    for user in users:
        # Vérifier s'il est en congé aujourd'hui
        on_leave = Leave.objects.filter(
            user=user,
            status=Leave.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today
        ).exists()

        if on_leave:
            continue  # Pas de scan si en congé

        # Vérifier les enregistrements de départ
        departure_record = AttendanceRecord.objects.filter(
            user=user,
            timestamp__date=today,
            action_type=AttendanceRecord.Status.DEPARTURE
        ).exists()

        if departure_record:
            # Vérifier s'il y a un enregistrement d'arrivée correspondant
            arrival_record = AttendanceRecord.objects.filter(
                user=user,
                timestamp__date=today,
                action_type=AttendanceRecord.Status.ARRIVAL
            ).exists()

            if not arrival_record:
                # Créer une notification pour oubli de scan
                Notification.objects.create(
                    recipient=user,
                    message=f"Vous avez quitté le poste sans scanner votre carte NFC.",
                    notification_type='missed_scan'
                )

@shared_task
def detect_extended_breaks():
    """
    Détecte les pauses qui ont duré plus longtemps que le temps autorisé.
    """
    today = date.today()
    users = User.objects.all()

    for user in users:
        # Vérifier s'il est en congé aujourd'hui
        on_leave = Leave.objects.filter(
            user=user,
            status=Leave.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today
        ).exists()

        if on_leave:
            continue  # Pas de pause si en congé

        # Obtenir tous les enregistrements de pause pour aujourd'hui
        pause_start_records = AttendanceRecord.objects.filter(
            user=user,
            timestamp__date=today,
            action_type=AttendanceRecord.Status.PAUSE_START
        ).order_by('timestamp')

        for pause_start in pause_start_records:
            # Trouver le correspondant PAUSE_END
            pause_end = AttendanceRecord.objects.filter(
                user=user,
                timestamp__gt=pause_start.timestamp,
                timestamp__date=today,
                action_type=AttendanceRecord.Status.PAUSE_END
            ).first()

            if pause_end:
                pause_duration = pause_end.timestamp - pause_start.timestamp
            else:
                # Si PAUSE_END n'est pas trouvée, calculer jusqu'à maintenant
                pause_duration = timezone.now() - pause_start.timestamp

            # Définir la durée maximale autorisée (par exemple, 30 minutes)
            max_pause_duration = timedelta(minutes=30)

            if pause_duration > max_pause_duration:
                # Créer une notification pour pause prolongée
                Notification.objects.create(
                    recipient=user,
                    message=f"Votre pause a duré plus longtemps que le temps autorisé ({pause_duration}).",
                    notification_type='extended_break'
                )
                
                
@shared_task
def generate_report_task(report_id):
    try:
        report = Reportfolder.objects.get(id=report_id)
        report.status = 'generating'
        report.save()

        # Générer les données en fonction du type de rapport
        if report.report_type == 'presence':
            data = generate_presence_report()
        elif report.report_type == 'department':
            data = generate_department_report()
        elif report.report_type == 'user':
            data = generate_user_report()
        else:
            raise ValueError('Type de rapport inconnu.')

        # Générer le fichier dans le format spécifié
        if report.format == 'csv':
            buffer = BytesIO()
            data.to_csv(buffer, index=False)
            file_content = buffer.getvalue()
            buffer.close()
            file_name = f"{report.name}.csv"

        elif report.format == 'xlsx':
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                data.to_excel(writer, index=False, sheet_name='Rapport')
            file_content = buffer.getvalue()
            buffer.close()
            file_name = f"{report.name}.xlsx"

        elif report.format == 'pdf':
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            textobject = p.beginText(50, 800)
            textobject.setFont("Helvetica", 12)
            for line in generate_pdf_content(data):
                textobject.textLine(line)
            p.drawText(textobject)
            p.showPage()
            p.save()
            file_content = buffer.getvalue()
            buffer.close()
            file_name = f"{report.name}.pdf"

        else:
            raise ValueError('Format de rapport inconnu.')

        # Enregistrer le fichier dans le modèle Report
        report.file.save(file_name, ContentFile(file_content))
        report.status = 'completed'
        report.generated_at = timezone.now()
        report.save()

    except Exception as e:
        report.status = 'failed'
        report.error_message = str(e)
        report.save()

def generate_presence_report():
    """
    Génère un rapport de présence.
    """
    # Exemple d'utilisation des modèles AttendanceRecord et User
    records = AttendanceRecord.objects.select_related('user').all()
    data = []
    for record in records:
        data.append({
            'Utilisateur': record.user.username,
            'Nom': record.user.get_full_name(),
            'Action': record.get_action_type_display(),
            'Timestamp': record.timestamp,
            # Ajoutez d'autres champs si nécessaire
        })
    df = pd.DataFrame(data)
    return df

def generate_department_report():
    """
    Génère un rapport par département.
    """
    departments = Department.objects.all()
    data = []
    for dept in departments:
        users = User.objects.filter(profile__department=dept)
        data.append({
            'Département': dept.name,
            'Nombre d\'utilisateurs': users.count(),
            # Ajoutez d'autres statistiques si nécessaire
        })
    df = pd.DataFrame(data)
    return df

def generate_user_report():
    """
    Génère un rapport par utilisateur.
    """
    users = User.objects.all()
    data = []
    for user in users:
        attendance = AttendanceRecord.objects.filter(user=user)
        data.append({
            'Utilisateur': user.username,
            'Nom': user.get_full_name(),
            'Présences': attendance.filter(action_type=AttendanceRecord.Status.ARRIVAL).count(),
            'Départs': attendance.filter(action_type=AttendanceRecord.Status.DEPARTURE).count(),
            # Ajoutez d'autres statistiques si nécessaire
        })
    df = pd.DataFrame(data)
    return df

def generate_pdf_content(dataframe):
    """
    Génère le contenu textuel pour un rapport PDF à partir d'un DataFrame.
    """
    lines = []
    for index, row in dataframe.iterrows():
        line = ', '.join([f"{key}: {value}" for key, value in row.items()])
        lines.append(line)
    return lines