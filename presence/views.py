# core/views.py

from datetime import datetime
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework import viewsets, permissions, status
import subprocess
from django.contrib.auth.models import User
from .models import (
    Department, UserProfile, NFCCard, AttendanceRule, AttendanceRecord,
    PresenceHistory, Leave, Notification, LogEntry, Report, ReportSchedule,
    NFCReader, AccessPoint, AccessRule,
    LoginAttempt, UserSession, PasswordReset
)
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
    AttendanceRecordSerializer
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
    
    card_uid = request.data.get('card_uid')
    if not card_uid:
        return Response({'error': 'UID de la carte NFC requis.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        card = NFCCard.objects.get(card_uid=card_uid, is_active=True)
    except NFCCard.DoesNotExist:
        return Response({'error': 'Carte NFC invalide ou inactive.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = card.user
    try:
        attendance_rule = AttendanceRule.objects.get(department=user.profile.department, is_active=True)
    except AttendanceRule.DoesNotExist:
        return Response({'error': 'Règle de présence non définie pour ce département.'}, status=status.HTTP_400_BAD_REQUEST)
    
    current_time = timezone.now().time()
    
    # Vérifier les horaires de travail
    if not (attendance_rule.start_time <= current_time <= attendance_rule.end_time):
        return Response({'error': 'Accès en dehors des heures de travail.'}, status=status.HTTP_403_FORBIDDEN)
    
    # Vérifier les règles d'accès
    access_rules = AccessRule.objects.filter(access_point=access_point, is_active=True).order_by('-priority')
    
    access_granted = False
    for rule in access_rules:
        # Vérifier les dates de validité
        if rule.start_date and timezone.now() < rule.start_date:
            continue
        if rule.end_date and timezone.now() > rule.end_date:
            continue
        
        # Vérifier les départements autorisés
        if rule.departments.exists() and user.profile.department not in rule.departments.all():
            continue
        
        # Vérifier selon le type de règle
        if rule.rule_type == AccessRule.RuleType.TIME_BASED:
            start = rule.conditions.get('start_time')
            end = rule.conditions.get('end_time')
            if start and end:
                # Convertir les chaînes en objets time si nécessaire
                try:
                    start_time = datetime.strptime(start, '%H:%M').time()
                    end_time = datetime.strptime(end, '%H:%M').time()
                except ValueError:
                    # Format de temps incorrect
                    continue
                if not (start_time <= current_time <= end_time):
                    continue
        elif rule.rule_type == AccessRule.RuleType.USER_BASED:
            allowed_users = rule.allowed_users.all()
            if user not in allowed_users:
                continue
        elif rule.rule_type == AccessRule.RuleType.TEMPORARY:
            # Implémenter des règles temporaires si nécessaire
            temporary_conditions = rule.conditions.get('temporary_conditions', {})
            # Exemple: vérifier une condition spécifique
            # if not temporary_conditions.get('some_condition'):
            #     continue
            pass
        elif rule.rule_type == AccessRule.RuleType.SPECIAL:
            # Implémenter des conditions spéciales
            special_conditions = rule.conditions.get('special_conditions', {})
            # Exemple: vérifier des flags ou d'autres paramètres
            # if not special_conditions.get('holiday_access', False):
            #     continue
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
        # Enregistrer l'échec d'accès (Départ ou autre action selon le contexte)
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