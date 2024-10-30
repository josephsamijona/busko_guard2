# presence/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from .models import User, Leave, AttendanceRecord, Notification, NFCReader
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