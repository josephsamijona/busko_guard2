# leaves/serializers.py
from rest_framework import serializers
from .models import Leave, LeaveBalance
from attendance.models import Attendance
class LeaveSerializer(serializers.ModelSerializer):
    days_requested = serializers.IntegerField(source='days_count', read_only=True)
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)

    class Meta:
        model = Leave
        fields = ['id', 'employee', 'employee_name', 'leave_type', 'start_date', 
                 'end_date', 'reason', 'status', 'days_requested', 'created_at']

class LeaveBalanceSerializer(serializers.ModelSerializer):
    remaining_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = LeaveBalance
        fields = ['leave_type', 'total_days', 'used_days', 'remaining_days']

class DashboardStatsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    present_today = serializers.IntegerField()
    present_percentage = serializers.FloatField()
    total_late = serializers.IntegerField()
    late_percentage = serializers.FloatField()
    total_absent = serializers.IntegerField()
    absent_percentage = serializers.FloatField()
    on_leave = serializers.IntegerField()
    leave_percentage = serializers.FloatField()

class WeeklyAttendanceSerializer(serializers.Serializer):
    day = serializers.CharField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()

class AlertSerializer(serializers.Serializer):
    type = serializers.CharField()  # 'absence', 'late', 'leave'
    message = serializers.CharField()
    department = serializers.CharField()
    date = serializers.DateTimeField()
    count = serializers.IntegerField()