# core/views.py

from datetime import date, datetime
from datetime import datetime, timedelta
from django.db.models import Q

from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework import viewsets, permissions, status
from presence.attendaceutils import calculate_attendance
import subprocess
from django.contrib.auth.models import User
from .models import (
    Department, UserProfile, NFCCard, AttendanceRule, AttendanceRecord,
    PresenceHistory, Leave, Notification, LogEntry, Report, ReportSchedule,
    NFCReader, AccessPoint, AccessRule,
    LoginAttempt, UserSession, PasswordReset
)
# presence/views.py

from presence.nfc_utils import read_card_uid

from .permissions import IsManager, IsRecipient
from .serializers import (
    DepartmentSerializer, 
    UserSerializer, 
    UserCreateSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    LoginAttemptSerializer,
    UserSessionSerializer,
    PasswordResetSerializer,
    LogEntrySerializer,
    NFCCardSerializer,
    AccessPointSerializer,
    NFCReaderSerializer,
    AttendanceRuleSerializer,
    AccessRuleSerializer,
    AttendanceRecordSerializer,
    LeaveApprovalSerializer,
    LeaveRequestSerializer, NotificationUpdateSerializer,NotificationSerializer
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from pythonping import ping           # Ajoutez cette ligne
from django.utils import timezone      # Assurez-vous que timezone est importé
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)



class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permet uniquement aux utilisateurs admin de modifier, tout le monde peut lire.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les départements.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['is_active', 'manager__username']

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les utilisateurs.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=['get', 'put'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request, pk=None):
        """
        Endpoint pour récupérer ou mettre à jour le profil d'un utilisateur.
        Seul l'utilisateur lui-même ou un admin peut accéder à ce profil.
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        
        if not (request.user.is_staff or request.user == user):
            return Response({"detail": "Vous n'avez pas la permission d'accéder à ce profil."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"detail": "Profil utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # Re-sérialiser pour afficher les données complètes après mise à jour
                full_serializer = UserProfileSerializer(profile)
                return Response(full_serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les profils utilisateurs.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'department__name']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

class LoginAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour visualiser les tentatives de connexion.
    Seuls les administrateurs peuvent accéder à cette vue.
    """
    queryset = LoginAttempt.objects.all().order_by('-created_at')  # Utilisez 'created_at' ici
    serializer_class = LoginAttemptSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['user', 'success', 'ip_address']
    search_fields = ['user__username', 'ip_address', 'user_agent']

class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour visualiser les sessions utilisateur actives.
    Seuls les administrateurs peuvent accéder à cette vue.
    """
    queryset = UserSession.objects.filter(is_active=True).order_by('-last_activity')
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['user', 'ip_address', 'is_active']
    search_fields = ['user__username', 'ip_address', 'user_agent']

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAdminUser])
    def terminate(self, request, pk=None):
        """
        Terminer une session utilisateur spécifique.
        """
        try:
            session = self.get_object()
            session.is_active = False
            session.save()
            return Response({'status': 'Session terminée'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les demandes de réinitialisation de mot de passe.
    Seuls les administrateurs peuvent visualiser les demandes.
    Les utilisateurs peuvent créer des demandes via un autre mécanisme (comme un endpoint spécifique).
    """
    queryset = PasswordReset.objects.all().order_by('-created_at')
    serializer_class = PasswordResetSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['user', 'used', 'ip_address']
    search_fields = ['user__username', 'user__email', 'ip_address']

class LogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour visualiser les logs des opérations.
    Seuls les administrateurs peuvent accéder à cette vue.
    """
    queryset = LogEntry.objects.all().order_by('-created_at')  # Utilisez 'created_at' ici
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['user', 'action', 'ip_address']
    search_fields = ['user__username', 'action', 'ip_address', 'user_agent']

class NFCCardViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les cartes NFC.
    """
    queryset = NFCCard.objects.all()
    serializer_class = NFCCardSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['status', 'is_active', 'user__username']
    search_fields = ['card_uid', 'user__username', 'user__first_name', 'user__last_name']

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
        
class NFCReaderViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les lecteurs NFC.
    """
    queryset = NFCReader.objects.all()
    serializer_class = NFCReaderSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['status', 'reader_type', 'is_online']
    search_fields = ['identifier', 'name', 'location', 'ip_address', 'firmware_version']

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def ping_reader(self, request, pk=None):
        """
        Action personnalisée pour pinger le lecteur NFC et mettre à jour son statut.
        """
        reader = self.get_object()
        ip = reader.ip_address
        if not ip:
            return Response(
                {'error': 'Adresse IP non définie pour ce lecteur.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
            return Response(
                {'is_online': reader.is_online, 'status': reader.status},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AccessPointViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les points d'accès.
    """
    queryset = AccessPoint.objects.all()
    serializer_class = AccessPointSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['is_active', 'required_access_level']
    search_fields = ['name', 'description', 'reader__name']
    
class AttendanceRuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les règles de présence.
    """
    queryset = AttendanceRule.objects.select_related('department').all()
    serializer_class = AttendanceRuleSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['department']
    search_fields = ['name', 'department__name']
    
# presence/views.py

class AccessRuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les règles d'accès avancées.
    """
    queryset = AccessRule.objects.select_related('access_point').prefetch_related('departments', 'allowed_users').all()
    serializer_class = AccessRuleSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['rule_type', 'access_point', 'is_active', 'departments']
    search_fields = ['name', 'rule_type', 'access_point__name', 'description']

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def access_point_access(request, access_point_id):
    """
    Endpoint pour traiter l'accès à un point d'accès via une carte NFC.
    """
    access_point = get_object_or_404(AccessPoint, id=access_point_id)
    
    # Lire l'UID de la carte depuis le secteur 5
    card_uid, message = read_card_uid()
    if not card_uid:
        logger.error(f"Erreur lors de la lecture de la carte : {message}")
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
    
    # Rechercher la carte NFC dans la base de données
    try:
        card = NFCCard.objects.get(card_uid=card_uid, is_active=True)
    except NFCCard.DoesNotExist:
        logger.warning(f"Carte NFC non reconnue : UID={card_uid}")
        return Response({'error': 'Carte NFC invalide ou inactive.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = card.user
    # Vérifier si l'utilisateur a un profil avec un département associé
    if not hasattr(user, 'profile') or not user.profile.department:
        logger.warning(f"L'utilisateur {user.username} n'a pas de département associé.")
        return Response({'error': 'Utilisateur sans département associé.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Vérifier les règles de présence
    try:
        attendance_rule = AttendanceRule.objects.get(department=user.profile.department, is_active=True)
    except AttendanceRule.DoesNotExist:
        logger.warning(f"Aucune règle de présence active pour le département {user.profile.department}.")
        return Response({'error': 'Règle de présence non définie pour ce département.'}, status=status.HTTP_400_BAD_REQUEST)
    
    current_time = timezone.now().time()
    
    # Vérifier les horaires de travail
    if not (attendance_rule.start_time <= current_time <= attendance_rule.end_time):
        logger.info(f"Accès en dehors des heures de travail pour l'utilisateur {user.username}.")
        return Response({'error': 'Accès en dehors des heures de travail.'}, status=status.HTTP_403_FORBIDDEN)
    
    # Vérifier les règles d'accès
    access_rules = AccessRule.objects.filter(access_point=access_point, is_active=True).order_by('-priority')
    
    access_granted = False
    for rule in access_rules:
        # Vérifier les dates de validité
        now = timezone.now()
        if rule.start_date and now < rule.start_date:
            continue
        if rule.end_date and now > rule.end_date:
            continue
        
        # Vérifier les départements autorisés
        if rule.departments.exists() and user.profile.department not in rule.departments.all():
            continue
        
        # Vérifier selon le type de règle
        if rule.rule_type == AccessRule.RuleType.TIME_BASED:
            start = rule.conditions.get('start_time')
            end = rule.conditions.get('end_time')
            if start and end:
                try:
                    start_time = datetime.strptime(start, '%H:%M').time()
                    end_time = datetime.strptime(end, '%H:%M').time()
                except ValueError:
                    continue
                if not (start_time <= current_time <= end_time):
                    continue
        elif rule.rule_type == AccessRule.RuleType.USER_BASED:
            allowed_users = rule.allowed_users.all()
            if user not in allowed_users:
                continue
        elif rule.rule_type == AccessRule.RuleType.TEMPORARY:
            # Implémenter des règles temporaires si nécessaire
            pass
        elif rule.rule_type == AccessRule.RuleType.SPECIAL:
            # Implémenter des conditions spéciales
            pass
        else:
            continue
        
        # Si toutes les conditions sont remplies, accorder l'accès
        access_granted = True
        break
    
    if access_granted:
        # Enregistrer l'enregistrement de présence (Arrivée)
        AttendanceRecord.objects.create(
            user=user,
            action_type=AttendanceRecord.Status.ARRIVAL,
            location=access_point,
            notes='Accès autorisé.'
        )
        logger.info(f"Accès autorisé pour {user.username} au point d'accès {access_point.name} à {timezone.now()}")
        return Response({'status': 'Accès autorisé.'}, status=status.HTTP_200_OK)
    else:
        # Enregistrer l'échec d'accès
        AttendanceRecord.objects.create(
            user=user,
            action_type=AttendanceRecord.Status.DEPARTURE,
            location=access_point,
            notes='Accès refusé selon les règles d\'accès.'
        )
        logger.warning(f"Accès refusé pour {user.username} au point d'accès {access_point.name} à {timezone.now()}")
        return Response({'error': 'Accès refusé selon les règles d\'accès.'}, status=status.HTTP_403_FORBIDDEN)
class AttendanceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour visualiser les enregistrements de présence.
    Seuls les administrateurs et les managers peuvent accéder à ces données.
    """
    queryset = AttendanceRecord.objects.select_related('user', 'location').all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAdminUser | IsManager]
    filterset_fields = ['user', 'action_type', 'location']
    search_fields = ['user__username', 'location__name', 'notes']
    ordering = ['-timestamp']
    
class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint permettant aux utilisateurs de créer et consulter leurs demandes de congé.
    """
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Leave.objects.filter(user=self.request.user).order_by('-created_at')
    
class LeaveApprovalViewSet(viewsets.ModelViewSet):
    """
    API endpoint permettant aux responsables d'approuver ou de rejeter les demandes de congé.
    """
    serializer_class = LeaveApprovalSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def get_queryset(self):
        # Le responsable voit les demandes des utilisateurs de son département
        department = self.request.user.profile.department
        return Leave.objects.filter(user__profile__department=department, status=Leave.Status.PENDING)

    def update(self, request, *args, **kwargs):
        # Limiter les champs modifiables
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_attendance_report(request, user_id, date_str):
    """
    Génère un rapport de présence quotidien pour un utilisateur donné.
    
    Args:
        user_id (int): L'ID de l'utilisateur.
        date_str (str): La date au format 'YYYY-MM-DD'.
    
    Returns:
        Response: Un rapport JSON contenant la présence de l'utilisateur.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé.'}, status=404)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Format de date invalide. Utilisez YYYY-MM-DD.'}, status=400)
    
    attendance = calculate_attendance(user, date)
    
    return Response(attendance, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_attendance_report(request, user_id, year, month):
    """
    Génère un rapport de présence mensuel pour un utilisateur donné.
    
    Args:
        user_id (int): L'ID de l'utilisateur.
        year (int): L'année du rapport.
        month (int): Le mois du rapport.
    
    Returns:
        Response: Un rapport JSON contenant la présence de l'utilisateur pour chaque jour du mois.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé.'}, status=404)
    
    try:
        first_day = date(year, month, 1)
    except ValueError:
        return Response({'error': 'Date invalide.'}, status=400)
    
    # Calculer le dernier jour du mois
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    current_date = first_day
    report = []
    
    while current_date <= last_day:
        attendance = calculate_attendance(user, current_date)
        report.append(attendance)
        current_date += timedelta(days=1)
    
    return Response({
        'user': user.username,
        'month': f"{year}-{month:02d}",
        'attendance_report': report
    }, status=200)
    
class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les notifications des utilisateurs.
    """
    queryset = Notification.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsRecipient]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return NotificationUpdateSerializer
        return NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    def perform_update(self, serializer):
        serializer.save()

class LeaveApprovalViewSet(viewsets.ModelViewSet):
    """
    API endpoint permettant aux responsables d'approuver ou de rejeter les demandes de congé.
    """
    serializer_class = LeaveApprovalSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def get_queryset(self):
        # Le responsable voit les demandes des utilisateurs de son département
        department = self.request.user.profile.department
        return Leave.objects.filter(user__profile__department=department, status=Leave.Status.PENDING)

    def update(self, request, *args, **kwargs):
        # Limiter les champs modifiables
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Créer une notification pour l'utilisateur
        status_updated = serializer.validated_data.get('status')
        if status_updated == Leave.Status.APPROVED:
            message = f"Votre demande de congé du {instance.start_date} au {instance.end_date} a été approuvée."
            notification_type = 'general'  # Utiliser 'general' pour les messages approuvés
        else:
            message = f"Votre demande de congé du {instance.start_date} au {instance.end_date} a été rejetée.\nRaison du rejet : {serializer.validated_data.get('comments', '')}"
            notification_type = 'anomaly'  # Utiliser 'anomaly' pour les rejets

        Notification.objects.create(
            recipient=instance.user,
            message=message,
            notification_type=notification_type,
            approved_by=request.user,
            start_date=instance.start_date,
            end_date=instance.end_date,
            comments=serializer.validated_data.get('comments', '')
        )

        return Response(serializer.data)