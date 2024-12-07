# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from accounts.models import Employee ,Department

from attendance.models import Attendance
from leave.models import Leave,LeaveBalance
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone_number', 'is_employee')

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Identifiants incorrects")
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = UserSerializer(user).data
        return data
    
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        
        
class LeaveSerializerr(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display')
    leave_type_display = serializers.CharField(source='get_leave_type_display')
    days = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = ['id', 'leave_type', 'leave_type_display', 'start_date', 
                 'end_date', 'status', 'status_display', 'days', 'created_at']

    def get_days(self, obj):
        return obj.days_count()

class AttendanceSerializerr(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display')
    attendance_type_display = serializers.CharField(source='get_attendance_type_display')

    class Meta:
        model = Attendance
        fields = ['id', 'date', 'check_in', 'check_out', 'status', 
                 'status_display', 'attendance_type', 'attendance_type_display']

class LeaveBalanceSerializerr(serializers.ModelSerializer):
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ['leave_type', 'total_days', 'used_days', 'remaining']

    def get_remaining(self, obj):
        return obj.remaining_days()