# attendance/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from attendance.serializers import AttendanceSerializer,AttendanceStatsSerializer, AttendanceHistorySerializer,TemporaryQRCodeSerializer
from accounts.models import Employee, Schedule
from attendance.serializers import (
    AttendanceAnalyticsReportSerializer,
    DepartmentAttendanceAnalyticsSerializer,
    MonthlyAnalyticsStatsSerializer,
    EmployeeAttendanceAnalyticsSerializer
)
from accounts.models import Employee, Department
from attendance.models import Attendance, TemporaryQRCode
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import uuid
import calendar



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
            
            


class SaveQRCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # L'employé est automatiquement obtenu via l'utilisateur connecté
            employee = request.user.employee
            
            # Génération d'un code unique
            unique_code = str(uuid.uuid4())
            
            # Création du QR code avec timezone
            expiry = timezone.now() + timezone.timedelta(seconds=30)
            
            # Désactiver les anciens QR codes de l'employé
            TemporaryQRCode.objects.filter(
                employee=employee,
                is_used=False,
                expiry__gt=timezone.now()
            ).update(is_used=True)
            
            # Créer le nouveau QR code
            qr_code = TemporaryQRCode.objects.create(
                employee=employee,
                code=unique_code,
                purpose='check-in',
                expiry=expiry,
                is_used=False
            )

            return Response({
                'status': 'success',
                'message': 'QR Code créé avec succès',
                'data': {
                    'code': qr_code.code,
                    'expiry': qr_code.expiry.isoformat(),
                    'expiry_seconds': 30
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

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
    
class DailyAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date')
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
        except ValueError:
            return Response(
                {'error': 'Format de date invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        department_id = request.query_params.get('department')
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search', '').strip()

        queryset = Attendance.objects.filter(date=date)

        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(
                Q(employee__user__first_name__icontains=search) |
                Q(employee__user__last_name__icontains=search) |
                Q(employee__employee_id__icontains=search)
            )

        total_employees = Employee.objects.filter(status='ACTIVE').count()
        total_present = queryset.filter(status='PRESENT').count()
        total_late = queryset.filter(status='LATE').count()
        total_absent = total_employees - (total_present + total_late)

        departments = Department.objects.all()
        department_stats = DepartmentAttendanceAnalyticsSerializer(
            departments,
            many=True,
            context={'date': date}
        ).data

        attendance_details = AttendanceAnalyticsReportSerializer(
            queryset,
            many=True
        ).data

        return Response({
            'date': date,
            'summary': {
                'total_employees': total_employees,
                'present': total_present,
                'late': total_late,
                'absent': total_absent,
                'attendance_rate': round(((total_present + total_late) / total_employees * 100), 1)
            },
            'department_breakdown': department_stats,
            'attendance_details': attendance_details
        })

class MonthlyAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        department_id = request.query_params.get('department')

        _, last_day = calendar.monthrange(year, month)
        departments = Department.objects.all()
        if department_id:
            departments = departments.filter(id=department_id)

        daily_stats = []
        for day in range(1, last_day + 1):
            date = datetime(year, month, day).date()
            if date <= timezone.now().date():
                attendances = Attendance.objects.filter(date=date)
                total_employees = Employee.objects.filter(
                    status='ACTIVE',
                    date_joined__lte=date
                ).count()

                if total_employees > 0:
                    present = attendances.filter(status='PRESENT').count()
                    late = attendances.filter(status='LATE').count()
                    absent = total_employees - (present + late)

                    department_breakdown = DepartmentAttendanceAnalyticsSerializer(
                        departments,
                        many=True,
                        context={'date': date}
                    ).data

                    daily_stats.append({
                        'date': date,
                        'total_present': present,
                        'total_late': late,
                        'total_absent': absent,
                        'attendance_rate': round(((present + late) / total_employees * 100), 1),
                        'department_breakdown': department_breakdown
                    })

        employee_stats = EmployeeAttendanceAnalyticsSerializer(
            Employee.objects.filter(status='ACTIVE'),
            many=True,
            context={'year': year, 'month': month}
        ).data

        sorted_employees = sorted(
            employee_stats,
            key=lambda x: x['attendance_stats']['attendance_rate'],
            reverse=True
        )

        return Response({
            'year': year,
            'month': month,
            'daily_stats': daily_stats,
            'best_attendance': sorted_employees[:5],
            'worst_attendance': sorted_employees[-5:] if len(sorted_employees) > 5 else []
        })

class AttendanceTrendsAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trends_data = []
        current_date = start_date

        while current_date <= end_date:
            attendances = Attendance.objects.filter(date=current_date)
            total_employees = Employee.objects.filter(
                status='ACTIVE',
                date_joined__lte=current_date
            ).count()

            if total_employees > 0:
                present = attendances.filter(status='PRESENT').count()
                late = attendances.filter(status='LATE').count()
                absent = total_employees - (present + late)

                trends_data.append({
                    'date': current_date,
                    'attendance_rate': round(((present + late) / total_employees * 100), 1),
                    'present': present,
                    'late': late,
                    'absent': absent
                })

            current_date += timedelta(days=1)

        department_trends = []
        for department in Department.objects.all():
            dept_attendances = Attendance.objects.filter(
                date__range=[start_date, end_date],
                employee__department=department
            )
            total_possible = Employee.objects.filter(
                department=department,
                status='ACTIVE'
            ).count() * days

            if total_possible > 0:
                present_late = dept_attendances.filter(
                    status__in=['PRESENT', 'LATE']
                ).count()
                
                department_trends.append({
                    'department': department.name,
                    'average_attendance': round((present_late / total_possible * 100), 1)
                })

        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days
            },
            'daily_trends': trends_data,
            'department_trends': sorted(
                department_trends,
                key=lambda x: x['average_attendance'],
                reverse=True
            )
        })