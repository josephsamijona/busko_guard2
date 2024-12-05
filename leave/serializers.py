# leaves/serializers.py
from rest_framework import serializers
from .models import Leave, LeaveBalance

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
