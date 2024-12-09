# leaves/views.py
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Leave, LeaveBalance
from attendance.models import Attendance
from django.db.models import Count, Q
from accounts.models import Employee, Department
from .serializers import LeaveSerializer, LeaveBalanceSerializer,DashboardStatsSerializer, WeeklyAttendanceSerializer, AlertSerializer
from django.utils import timezone


class LeaveCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Récupérer l'employé à partir de l'utilisateur connecté
            employee = request.user.employee
            
            # Parser les dates
            try:
                start_date = datetime.strptime(
                    request.data.get('start_date'), 
                    '%Y-%m-%d'
                ).date()
                end_date = datetime.strptime(
                    request.data.get('end_date'), 
                    '%Y-%m-%d'
                ).date()
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Format de date invalide. Utilisez YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Créer la demande de congé
            leave = Leave.objects.create(
                employee=employee,
                leave_type=request.data.get('leave_type'),
                start_date=start_date,
                end_date=end_date,
                reason=request.data.get('reason', ''),
                status='PENDING'
            )

            # Calculer le nombre de jours
            days_requested = (end_date - start_date).days + 1

            # Sérialiser et renvoyer la réponse
            serializer = LeaveSerializer(leave)
            return Response(
                {
                    'message': 'Demande de congé créée avec succès',
                    'leave': serializer.data,
                    'days_requested': days_requested
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )











class LeaveListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        queryset = Leave.objects.all()
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        serializer = LeaveSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LeaveSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        serializer = LeaveSerializer(leave)
        return Response(serializer.data)

    def put(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        serializer = LeaveSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        if leave.status != 'PENDING':
            return Response(
                {'error': 'Cette demande a déjà été traitée'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        leave.status = 'APPROVED'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()

        # Mettre à jour le solde de congés
        balance = LeaveBalance.objects.get(
            employee=leave.employee,
            leave_type=leave.leave_type,
            year=leave.start_date.year
        )
        balance.used_days += leave.days_count()
        balance.save()

        return Response({'status': 'Demande approuvée'})

class LeaveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        if leave.status != 'PENDING':
            return Response(
                {'error': 'Cette demande a déjà été traitée'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        leave.status = 'REJECTED'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()

        return Response({'status': 'Demande rejetée'})

class LeaveBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        balances = LeaveBalance.objects.filter(
            employee_id=employee_id,
            year=timezone.now().year
        )
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)
    
    
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        # Récupérer les statistiques de base
        total_employees = Employee.objects.filter(status='ACTIVE').count()
        
        # Présences du jour
        today_attendance = Attendance.objects.filter(date=today)
        present_count = today_attendance.filter(
            Q(status='PRESENT') | Q(status='LATE')
        ).count()
        
        late_count = today_attendance.filter(status='LATE').count()
        absent_count = total_employees - present_count
        
        # Employés en congé
        on_leave_count = Leave.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='APPROVED'
        ).count()

        # Calculer les pourcentages
        stats = {
            'total_employees': total_employees,
            'present_today': present_count,
            'present_percentage': (present_count / total_employees * 100) if total_employees > 0 else 0,
            'total_late': late_count,
            'late_percentage': (late_count / total_employees * 100) if total_employees > 0 else 0,
            'total_absent': absent_count,
            'absent_percentage': (absent_count / total_employees * 100) if total_employees > 0 else 0,
            'on_leave': on_leave_count,
            'leave_percentage': (on_leave_count / total_employees * 100) if total_employees > 0 else 0,
        }

        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

class WeeklyAttendanceStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        dates = [week_start + timedelta(days=i) for i in range(5)]  # Lundi à Vendredi

        weekly_stats = []
        for date in dates:
            total_employees = Employee.objects.filter(status='ACTIVE').count()
            day_attendance = Attendance.objects.filter(date=date)
            present_count = day_attendance.filter(
                Q(status='PRESENT') | Q(status='LATE')
            ).count()
            absent_count = total_employees - present_count

            weekly_stats.append({
                'day': date.strftime('%a'),  # Abréviation du jour
                'present': present_count,
                'absent': absent_count
            })

        serializer = WeeklyAttendanceSerializer(weekly_stats, many=True)
        return Response(serializer.data)

class RecentAlertsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        # Alertes pour les absences
        absence_alerts = []
        departments = Department.objects.all()
        for dept in departments:
            absent_count = Attendance.objects.filter(
                employee__department=dept,
                date=today,
                status='ABSENT'
            ).count()
            
            if absent_count > 0:
                absence_alerts.append({
                    'type': 'absence',
                    'message': f'{absent_count} absences non justifiées',
                    'department': dept.name,
                    'date': timezone.now(),
                    'count': absent_count
                })

        # Alertes pour les retards
        late_alerts = []
        for dept in departments:
            late_count = Attendance.objects.filter(
                employee__department=dept,
                date=today,
                status='LATE'
            ).count()
            
            if late_count > 0:
                late_alerts.append({
                    'type': 'late',
                    'message': f'{late_count} retards signalés',
                    'department': dept.name,
                    'date': timezone.now(),
                    'count': late_count
                })

        all_alerts = absence_alerts + late_alerts
        all_alerts.sort(key=lambda x: x['count'], reverse=True)
        
        serializer = AlertSerializer(all_alerts, many=True)
        return Response(serializer.data)
