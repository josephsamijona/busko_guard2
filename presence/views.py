# core/views.py

from rest_framework import viewsets, permissions, status
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
    LogEntrySerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
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
    queryset = LoginAttempt.objects.all().order_by('-timestamp')
    serializer_class = LoginAttemptSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'success', 'ip_address']
    search_fields = ['user__username', 'ip_address', 'user_agent']


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour visualiser les sessions utilisateur actives.
    Seuls les administrateurs peuvent accéder à cette vue.
    """
    queryset = UserSession.objects.filter(is_active=True).order_by('-last_activity')
    serializer_class = UserSessionSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'ip_address', 'is_active']
    search_fields = ['user__username', 'ip_address', 'user_agent']

    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
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
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'used', 'ip_address']
    search_fields = ['user__username', 'user__email', 'ip_address']


class LogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour visualiser les logs des opérations.
    Seuls les administrateurs peuvent accéder à cette vue.
    """
    queryset = LogEntry.objects.all().order_by('-timestamp')
    serializer_class = LogEntrySerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'action', 'ip_address']
    search_fields = ['user__username', 'action', 'ip_address', 'user_agent']