from rest_framework import serializers
from .models import Attendance, TemporaryQRCode
from accounts.models import Department, Employee
from django.db.models import Count

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

class TemporaryQRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporaryQRCode
        fields = ['employee', 'code', 'purpose', 'expiry', 'is_used']

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'attendance_type', 'status']

class AttendanceHistorySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name')

    class Meta:
        model = Attendance
        fields = ['id', 'employee_name', 'date', 'check_in', 'check_out', 'attendance_type', 'status']

class AttendanceStatsSerializer(serializers.Serializer):
    total_present = serializers.IntegerField()
    total_late = serializers.IntegerField()
    total_absent = serializers.IntegerField()
    attendance_rate = serializers.FloatField()


class AttendanceAnalyticsReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name')
    department_name = serializers.CharField(source='employee.department.name')
    check_in_time = serializers.SerializerMethodField()
    check_out_time = serializers.SerializerMethodField()
    work_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'employee_name', 'department_name', 'date',
            'check_in_time', 'check_out_time', 'status',
            'work_duration', 'attendance_type', 'late_reason'
        ]
    
    def get_check_in_time(self, obj):
        return obj.check_in.strftime('%H:%M') if obj.check_in else None

    def get_check_out_time(self, obj):
        return obj.check_out.strftime('%H:%M') if obj.check_out else None
    
    def get_work_duration(self, obj):
        if obj.check_in and obj.check_out:
            duration = obj.check_out - obj.check_in
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            return f"{hours}h {minutes}min"
        return None

class DepartmentAttendanceAnalyticsSerializer(serializers.ModelSerializer):
    total_employees = serializers.SerializerMethodField()
    present_count = serializers.SerializerMethodField()
    late_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'total_employees', 'present_count',
            'late_count', 'absent_count', 'attendance_rate'
        ]

    def get_total_employees(self, obj):
        return obj.employee_set.filter(status='ACTIVE').count()

    def get_present_count(self, obj):
        date = self.context.get('date')
        return Attendance.objects.filter(
            employee__department=obj,
            date=date,
            status='PRESENT'
        ).count()

    def get_late_count(self, obj):
        date = self.context.get('date')
        return Attendance.objects.filter(
            employee__department=obj,
            date=date,
            status='LATE'
        ).count()

    def get_absent_count(self, obj):
        date = self.context.get('date')
        present_and_late = Attendance.objects.filter(
            employee__department=obj,
            date=date,
            status__in=['PRESENT', 'LATE']
        ).count()
        return self.get_total_employees(obj) - present_and_late

    def get_attendance_rate(self, obj):
        total = self.get_total_employees(obj)
        if total == 0:
            return 0
        present_and_late = self.get_present_count(obj) + self.get_late_count(obj)
        return round((present_and_late / total) * 100, 1)

class MonthlyAnalyticsStatsSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_present = serializers.IntegerField()
    total_late = serializers.IntegerField()
    total_absent = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    department_breakdown = DepartmentAttendanceAnalyticsSerializer(many=True)

class EmployeeAttendanceAnalyticsSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name')
    department_name = serializers.CharField(source='department.name')
    attendance_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'full_name', 'department_name', 'attendance_stats']
    
    def get_attendance_stats(self, obj):
        month = self.context.get('month')
        year = self.context.get('year')
        
        attendances = obj.attendance_set.filter(
            date__year=year,
            date__month=month
        )
        
        total_days = attendances.count()
        present_days = attendances.filter(status='PRESENT').count()
        late_days = attendances.filter(status='LATE').count()
        absent_days = total_days - (present_days + late_days)
        
        return {
            'present_days': present_days,
            'late_days': late_days,
            'absent_days': absent_days,
            'attendance_rate': round(((present_days + late_days) / total_days * 100), 1) if total_days > 0 else 0,
            'total_work_hours': self._calculate_total_work_hours(attendances)
        }
    
    def _calculate_total_work_hours(self, attendances):
        total_seconds = 0
        for attendance in attendances:
            if attendance.check_in and attendance.check_out:
                duration = attendance.check_out - attendance.check_in
                total_seconds += duration.seconds
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}min"