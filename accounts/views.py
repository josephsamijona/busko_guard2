# accounts/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import Department
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from accounts.models import Employee
from attendance.models import Attendance
from leave.models import Leave,LeaveBalance
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from accounts.serializers import CustomTokenObtainPairSerializer ,DepartmentSerializer, EmployeeSerializer,UserSerializer,LoginSerializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)
        
        # Récupérer l'ID de l'employé si disponible
        employee_id = None
        if hasattr(user, 'employee'):
            employee_id = user.employee.id

        response_data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }
        
        if employee_id:
            response_data['employee_id'] = employee_id

        return Response(response_data)
    
    return Response(
        {'error': 'Identifiants invalides'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Le refresh token est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Création d'un objet token et révocation manuelle
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Déconnexion réussie'},
                status=status.HTTP_200_OK
            )
            
        except TokenError:
            return Response(
                {'error': 'Le token est invalide ou expiré'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=True, methods=['post'])
    def nfc(self, request, pk=None):
        employee = self.get_object()
        nfc_id = request.data.get('nfc_id')
        
        if not nfc_id:
            return Response(
                {'error': 'NFC ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        employee.nfc_id = nfc_id
        employee.save()
        return Response(EmployeeSerializer(employee).data)

    @action(detail=True, methods=['post'])
    def face(self, request, pk=None):
        employee = self.get_object()
        face_id = request.data.get('face_id')
        
        if not face_id:
            return Response(
                {'error': 'Face ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        employee.face_id = face_id
        employee.save()
        return Response(EmployeeSerializer(employee).data)
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employee_dashboard(request):
    """
    Vue pour obtenir toutes les statistiques du dashboard employé :
    - Présences du mois
    - Retards
    - Solde de congés
    - Dernières demandes de congés
    """
    employee = request.user.employee
    today = timezone.now().date()
    current_year = today.year
    first_day_of_month = today.replace(day=1)
    last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # 1. Statistiques de présence du mois en cours
    monthly_attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[first_day_of_month, last_day_of_month]
    )

    present_days = monthly_attendance.filter(
        status='PRESENT'
    ).count()

    late_days = monthly_attendance.filter(
        status='LATE'
    ).count()

    # Calculer les jours ouvrés du mois (en excluant les weekends)
    total_working_days = sum(1 for day in (first_day_of_month + timedelta(n) for n in range((last_day_of_month - first_day_of_month).days + 1))
                           if day.weekday() < 5)  # 0-4 représentent Lundi-Vendredi

    # 2. Solde des congés
    leave_balances = LeaveBalance.objects.filter(
        employee=employee,
        year=current_year
    )

    leaves_summary = {
        balance.leave_type: {
            'total': balance.total_days,
            'used': balance.used_days,
            'remaining': balance.remaining_days()
        }
        for balance in leave_balances
    }

    # 3. Dernières demandes de congés
    recent_leaves = Leave.objects.filter(
        employee=employee
    ).order_by('-created_at')[:5]

    return Response({
        'attendance_stats': {
            'present_days': present_days,
            'total_working_days': total_working_days,
            'late_count': late_days,
        },
        'leaves_balance': leaves_summary,
        'recent_leaves': [{
            'id': leave.id,
            'type': leave.get_leave_type_display(),
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'days': leave.days_count(),
            'status': leave.get_status_display(),
            'created_at': leave.created_at
        } for leave in recent_leaves]
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leave_balance(request):
    """
    Vue pour obtenir uniquement le solde des congés
    """
    employee = request.user.employee
    current_year = timezone.now().year

    balances = LeaveBalance.objects.filter(
        employee=employee,
        year=current_year
    )

    return Response({
        leave_balance.leave_type: {
            'total': leave_balance.total_days,
            'used': leave_balance.used_days,
            'remaining': leave_balance.remaining_days()
        }
        for leave_balance in balances
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance_status(request):
    """
    Vue pour obtenir le statut de présence du jour
    """
    employee = request.user.employee
    today = timezone.now().date()

    try:
        attendance = Attendance.objects.get(
            employee=employee,
            date=today
        )
        return Response({
            'date': attendance.date,
            'status': attendance.get_status_display(),
            'check_in': attendance.check_in,
            'check_out': attendance.check_out,
            'attendance_type': attendance.get_attendance_type_display()
        })
    except Attendance.DoesNotExist:
        return Response({
            'date': today,
            'status': 'Not checked in',
            'check_in': None,
            'check_out': None
        })
