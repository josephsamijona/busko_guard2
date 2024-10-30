# presence/utils.py

from datetime import datetime, timedelta
from django.utils import timezone
from .models import AttendanceRecord, Leave

def calculate_attendance(user, date):
    """
    Calcule les heures de présence d'un utilisateur pour une date donnée,
    en tenant compte des congés approuvés.
    
    Args:
        user (User): L'utilisateur dont la présence est calculée.
        date (date): La date pour laquelle calculer la présence.
    
    Returns:
        dict: Un dictionnaire contenant la date, le statut et les heures travaillées.
    """
    # Vérifier s'il y a un congé approuvé pour cette date
    leave_exists = Leave.objects.filter(
        user=user,
        status=Leave.Status.APPROVED,
        start_date__lte=date,
        end_date__gte=date
    ).exists()

    if leave_exists:
        return {
            'date': date,
            'status': 'En congé',
            'hours_worked': 0
        }

    # Obtenir les enregistrements de présence pour la date donnée
    attendance_records = AttendanceRecord.objects.filter(
        user=user,
        timestamp__date=date
    ).order_by('timestamp')

    if not attendance_records.exists():
        return {
            'date': date,
            'status': 'Absence non justifiée',
            'hours_worked': 0
        }

    # Initialiser les variables
    arrival_time = None
    departure_time = None
    total_worked_time = timedelta()
    current_pause_start = None

    for record in attendance_records:
        if record.action_type == AttendanceRecord.Status.ARRIVAL:
            if not arrival_time:
                arrival_time = record.timestamp
        elif record.action_type == AttendanceRecord.Status.DEPARTURE:
            departure_time = record.timestamp
        elif record.action_type == AttendanceRecord.Status.PAUSE_START:
            current_pause_start = record.timestamp
        elif record.action_type == AttendanceRecord.Status.PAUSE_END:
            if current_pause_start:
                pause_duration = record.timestamp - current_pause_start
                total_worked_time -= pause_duration
                current_pause_start = None

    if not arrival_time or not departure_time:
        return {
            'date': date,
            'status': 'Présence incomplète',
            'hours_worked': 0
        }

    # Calculer la durée totale entre l'arrivée et le départ
    worked_time = departure_time - arrival_time

    # Appliquer les pauses
    worked_time += total_worked_time  # total_worked_time est négatif si pauses soustraites

    # Calculer les heures travaillées en décimal
    calculated_hours = round(worked_time.total_seconds() / 3600, 2)

    return {
        'date': date,
        'status': 'Présent',
        'hours_worked': calculated_hours
    }
