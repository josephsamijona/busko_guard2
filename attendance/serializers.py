from rest_framework import serializers
from .models import Attendance, TemporaryQRCode
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
