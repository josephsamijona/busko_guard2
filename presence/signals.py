# core/signals.py

from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import LoginAttempt, UserSession, LogEntry, PasswordReset
from django.utils import timezone
from django.db.models.signals import post_save

from .models import Notification
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings




def get_client_ip(request):
    """Fonction utilitaire pour obtenir l'adresse IP du client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    """Enregistre une tentative de connexion réussie et crée ou met à jour une session utilisateur."""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    LoginAttempt.objects.create(
        user=user,
        ip_address=ip_address,
        success=True,
        user_agent=user_agent
    )
    # Créer ou mettre à jour UserSession
    session_key = request.session.session_key
    UserSession.objects.update_or_create(
        session_key=session_key,
        defaults={
            'user': user,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'last_activity': timezone.now(),
            'is_active': True
        }
    )
    # Créer un LogEntry
    LogEntry.objects.create(
        user=user,
        action='Connexion réussie',
        ip_address=ip_address,
        user_agent=user_agent
    )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Enregistre une tentative de connexion échouée et crée un LogEntry."""
    username = credentials.get('username', None)
    user = None
    if username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    LoginAttempt.objects.create(
        user=user,
        ip_address=ip_address,
        success=False,
        user_agent=user_agent
    )
    # Créer un LogEntry
    LogEntry.objects.create(
        user=user,
        action='Tentative de connexion échouée',
        ip_address=ip_address,
        user_agent=user_agent
    )

@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    """Enregistre une déconnexion et met à jour la session utilisateur."""
    if user:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        LoginAttempt.objects.create(
            user=user,
            ip_address=ip_address,
            success=True,
            user_agent=user_agent
        )
        # Mettre à jour UserSession
        session_key = request.session.session_key
        try:
            session = UserSession.objects.get(session_key=session_key)
            session.is_active = False
            session.save()
        except UserSession.DoesNotExist:
            pass
        # Créer un LogEntry
        LogEntry.objects.create(
            user=user,
            action='Déconnexion',
            ip_address=ip_address,
            user_agent=user_agent
        )

@receiver(post_save, sender=Notification)
def send_notification_email_signal(sender, instance, created, **kwargs):
    if created:
        recipient = instance.recipient
        subject = ""
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = recipient.email
        context = {
            'user': recipient,
            'date': instance.created_at.date(),
            'approver': instance.approved_by,
            'start_date': instance.start_date,
            'end_date': instance.end_date,
            'comments': instance.comments,
            'department': recipient.profile.department if hasattr(recipient, 'profile') else None,
            'message': instance.message,
            'actual_departure_time': getattr(instance, 'actual_departure_time', ''),
            'pause_duration_minutes': getattr(instance, 'pause_duration_minutes', 0),
        }

        # Déterminer le type de notification pour choisir le template et le sujet
        if instance.notification_type == 'missing_presence':
            subject = f"Absence Non Justifiée le {context['date']}"
            body = render_to_string('emails/missing_presence.txt', context)
        elif instance.notification_type == 'anomaly':
            subject = "Anomalie Détectée"
            body = render_to_string('emails/general_message.txt', context)
        elif instance.notification_type == 'general':
            subject = "Message Général"
            body = render_to_string('emails/general_message.txt', context)
        elif instance.notification_type == 'early_departure':
            subject = "Abandon de Poste"
            body = render_to_string('emails/early_departure.txt', context)
        elif instance.notification_type == 'missed_scan':
            subject = "Oubli de Scan"
            body = render_to_string('emails/missed_scan.txt', context)
        elif instance.notification_type == 'extended_break':
            subject = "Pause Prolongée"
            body = render_to_string('emails/extended_break.txt', context)
        else:
            subject = "Notification"
            body = instance.message

        # Créer et envoyer l'email
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email],
        )
        email.send()