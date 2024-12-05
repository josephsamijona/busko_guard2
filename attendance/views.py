# attendance/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from attendance.serializers import AttendanceSerializer,AttendanceStatsSerializer, AttendanceHistorySerializer
from accounts.models import Employee, Schedule
from attendance.models import Attendance
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import calendar

from datetime import datetime

class ValidateAttendanceView(APIView):
    def post(self, request):
        auth_type = request.data.get('type')  # 'QR', 'NFC', 'FACE'
        auth_data = request.data.get('data')
        
        if auth_type == 'QR':
            # Validation du QR déjà fait côté client
            employee_id = auth_data.get('employee_id')
        elif auth_type == 'NFC':
            employee_id = auth_data.get('nfc_id')
        elif auth_type == 'FACE':
            employee_id = auth_data.get('face_id')
        else:
            return Response({'error': 'Invalid authentication type'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=employee_id)
            return Response({
                'employee_id': employee.id,
                'name': employee.user.get_full_name(),
                'valid': True
            })
        except Employee.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, 
                          status=status.HTTP_404_NOT_FOUND)

class CheckInView(APIView):
    def post(self, request):
        employee_id = request.data.get('employee_id')
        attendance_type = request.data.get('type')

        try:
            employee = Employee.objects.get(id=employee_id)
            
            # Vérifier s'il n'y a pas déjà un check-in aujourd'hui
            today = timezone.now().date()
            existing_attendance = Attendance.objects.filter(
                employee=employee,
                date=today
            ).first()

            if existing_attendance and existing_attendance.check_in:
                return Response({
                    'error': 'Already checked in today'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Calculer le statut (en retard ou non)
            schedule = Schedule.objects.get(
                employee=employee,
                day_of_week=today.weekday()
            )
            
            now = timezone.now()
            status = 'PRESENT'
            if now.time() > schedule.start_time:
                status = 'LATE'

            # Créer ou mettre à jour l'attendance
            attendance = existing_attendance or Attendance.objects.create(
                employee=employee,
                date=today
            )
            
            attendance.check_in = now
            attendance.attendance_type = attendance_type
            attendance.status = status
            attendance.save()

            return Response(AttendanceSerializer(attendance).data)

        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        except Schedule.DoesNotExist:
            return Response({'error': 'No schedule found for today'}, 
                          status=status.HTTP_404_NOT_FOUND)

class CheckOutView(APIView):
    def post(self, request):
        employee_id = request.data.get('employee_id')
        
        try:
            employee = Employee.objects.get(id=employee_id)
            today = timezone.now().date()
            attendance = Attendance.objects.get(
                employee=employee,
                date=today
            )

            if attendance.check_out:
                return Response({
                    'error': 'Already checked out today'
                }, status=status.HTTP_400_BAD_REQUEST)

            attendance.check_out = timezone.now()
            attendance.save()

            return Response(AttendanceSerializer(attendance).data)

        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        except Attendance.DoesNotExist:
            return Response({'error': 'No check-in found for today'}, 
                          status=status.HTTP_404_NOT_FOUND)
            
            
# attendance/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .serializers import TemporaryQRCodeSerializer, AttendanceSerializer
from .models import TemporaryQRCode, Attendance

class SaveQRCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TemporaryQRCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AttendanceCheckViewqr(APIView):
    def post(self, request):
        try:
            # Récupérer le QR code
            qr_code = TemporaryQRCode.objects.get(code=request.data['code'])
            
            # Créer l'attendance
            attendance_data = {
                'employee': qr_code.employee.id,
                'attendance_type': 'QR',
                'status': 'PRESENT'
            }
            
            if qr_code.purpose == 'check-in':
                attendance_data['check_in'] = timezone.now()
            else:
                attendance_data['check_out'] = timezone.now()

            # Sauvegarder l'attendance
            serializer = AttendanceSerializer(data=attendance_data)
            if serializer.is_valid():
                serializer.save()
                
                # Marquer le QR code comme utilisé
                qr_code.is_used = True
                qr_code.used_at = timezone.now()
                qr_code.save()
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except TemporaryQRCode.DoesNotExist:
            return Response(
                {'error': 'QR Code invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
            
###########
class AttendanceHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = Attendance.objects.all()

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        queryset = queryset.order_by('-date')
        serializer = AttendanceHistorySerializer(queryset, many=True)
        return Response(serializer.data)

class AttendanceStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date', timezone.now().date())
        end_date = request.query_params.get('end_date', timezone.now().date())
        employee_id = request.query_params.get('employee_id')

        queryset = Attendance.objects.filter(date__range=[start_date, end_date])
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        stats = {
            'total_present': queryset.filter(status='PRESENT').count(),
            'total_late': queryset.filter(status='LATE').count(),
            'total_absent': queryset.filter(status='ABSENT').count(),
        }
        
        total = sum(stats.values())
        stats['attendance_rate'] = (stats['total_present'] / total * 100) if total > 0 else 0

        serializer = AttendanceStatsSerializer(stats)
        return Response(serializer.data)

class DailyReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.query_params.get('date', timezone.now().date())
        department_id = request.query_params.get('department_id')

        queryset = Attendance.objects.filter(date=date)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)

        report = {
            'date': date,
            'total_employees': queryset.count(),
            'present': queryset.filter(status='PRESENT').count(),
            'late': queryset.filter(status='LATE').count(),
            'absent': queryset.filter(status='ABSENT').count(),
            'by_department': queryset.values('employee__department__name').annotate(
                count=Count('id'),
                present=Count('id', filter=Q(status='PRESENT')),
                late=Count('id', filter=Q(status='LATE')),
                absent=Count('id', filter=Q(status='ABSENT'))
            )
        }
        return Response(report)

class MonthlyReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        employee_id = request.query_params.get('employee_id')

        # Obtenir le premier et dernier jour du mois
        _, last_day = calendar.monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, last_day)

        queryset = Attendance.objects.filter(date__range=[start_date, end_date])
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        report = {
            'year': year,
            'month': month,
            'total_days': last_day,
            'total_employees': queryset.values('employee').distinct().count(),
            'attendance_by_day': queryset.values('date').annotate(
                present=Count('id', filter=Q(status='PRESENT')),
                late=Count('id', filter=Q(status='LATE')),
                absent=Count('id', filter=Q(status='ABSENT'))
            ).order_by('date')
        }
        return Response(report)