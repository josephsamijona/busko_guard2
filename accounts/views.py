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
from django.db import transaction
from attendance.models import Attendance
from leave.models import Leave,LeaveBalance
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from accounts.serializers import  EmployeeNFCSerializer,EmployeeFaceIDSerializer,  EmployeeBasicInfoSerializer, CustomTokenObtainPairSerializer ,EmployeeManagementCreateSerializer, DepartmentManagementSerializer,DepartmentSerializer, EmployeeSerializer,UserSerializer,LoginSerializer,    EmployeeManagementListSerializer, DepartmentDetailSerializer, DepartmentCreateUpdateSerializer ,  UserCreationSerializer
    
    
    
    
    
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


class EmployeeManagementViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EmployeeManagementCreateSerializer
        return EmployeeManagementListSerializer

    def get_queryset(self):
        queryset = Employee.objects.select_related('user', 'department')
        
        # Recherche
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(position__icontains=search)
            )

        # Filtrage par département
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)

        # Filtrage par statut
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Tri
        ordering = self.request.query_params.get('ordering', '-date_joined')
        if ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        employee = self.get_object()
        employee.status = 'ACTIVE'
        employee.save()
        return Response({'status': 'employee activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        employee = self.get_object()
        employee.status = 'INACTIVE'
        employee.save()
        return Response({'status': 'employee deactivated'})

    @action(detail=True, methods=['post'])
    def set_nfc(self, request, pk=None):
        employee = self.get_object()
        nfc_id = request.data.get('nfc_id')
        if not nfc_id:
            return Response(
                {'error': 'NFC ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if Employee.objects.filter(nfc_id=nfc_id).exclude(pk=employee.pk).exists():
            return Response(
                {'error': 'NFC ID already in use'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        employee.nfc_id = nfc_id
        employee.save()
        return Response({'status': 'NFC ID updated'})

    @action(detail=True, methods=['post'])
    def set_face_id(self, request, pk=None):
        employee = self.get_object()
        face_id = request.data.get('face_id')
        if not face_id:
            return Response(
                {'error': 'Face ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if Employee.objects.filter(face_id=face_id).exclude(pk=employee.pk).exists():
            return Response(
                {'error': 'Face ID already in use'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        employee.face_id = face_id
        employee.save()
        return Response({'status': 'Face ID updated'})

class DepartmentManagementViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentManagementSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        queryset = Department.objects.all()
        
        # Recherche
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
class CreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = UserCreationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user_id': user.id,
                'message': 'Utilisateur créé avec succès'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateEmployeeBasicInfoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({
                'error': 'ID utilisateur requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = EmployeeBasicInfoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                employee = serializer.save(user_id=user_id)
                return Response({
                    'employee_id': employee.id,
                    'message': 'Informations de base enregistrées'
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateEmployeeNFCView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employé non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeNFCSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'NFC ID enregistré avec succès'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateEmployeeFaceIDView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employé non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeFaceIDSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Face ID enregistré avec succès'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ValidateNFCIDView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        nfc_id = request.data.get('nfc_id')
        if not nfc_id:
            return Response({
                'error': 'NFC ID requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        exists = Employee.objects.filter(nfc_id=nfc_id).exists()
        return Response({
            'valid': not exists
        })
        
        
class DepartmentListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Récupérer le paramètre de recherche
        search_query = request.query_params.get('search', '')
        ordering = request.query_params.get('ordering', 'name')

        # Construire la requête
        queryset = Department.objects.all()

        # Appliquer la recherche si un terme est fourni
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Appliquer le tri
        if ordering:
            # Vérifier si c'est un tri descendant
            if ordering.startswith('-'):
                ordering = ordering[1:]
                queryset = queryset.order_by(f'-{ordering}')
            else:
                queryset = queryset.order_by(ordering)

        serializer = DepartmentDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DepartmentCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_department(self, pk):
        try:
            return Department.objects.get(pk=pk)
        except Department.DoesNotExist:
            return None

    def get(self, request, pk):
        department = self.get_department(pk)
        if not department:
            return Response(
                {'error': 'Département non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DepartmentDetailSerializer(department)
        return Response(serializer.data)

    def put(self, request, pk):
        department = self.get_department(pk)
        if not department:
            return Response(
                {'error': 'Département non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DepartmentCreateUpdateSerializer(
            department,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        department = self.get_department(pk)
        if not department:
            return Response(
                {'error': 'Département non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DepartmentCreateUpdateSerializer(
            department,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        department = self.get_department(pk)
        if not department:
            return Response(
                {'error': 'Département non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier si le département a des employés
        if department.employee_set.exists():
            return Response(
                {'error': 'Impossible de supprimer un département qui contient des employés'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DepartmentStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        department = Department.objects.get(pk=pk)
        employee_count = department.employee_set.filter(status='ACTIVE').count()
        
        # Stats de présence
        today = timezone.now().date()
        present_count = department.employee_set.filter(
            attendance__date=today,
            attendance__status__in=['PRESENT', 'LATE']
        ).count()
        
        # Stats des congés
        on_leave_count = department.employee_set.filter(
            status='ON_LEAVE'
        ).count()

        stats = {
            'total_employees': employee_count,
            'present_today': present_count,
            'on_leave': on_leave_count,
            'attendance_rate': (present_count / employee_count * 100) if employee_count > 0 else 0
        }

        return Response(stats)