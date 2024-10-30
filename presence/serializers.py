# core/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Department, UserProfile, NFCCard, AttendanceRule, AttendanceRecord,
    PresenceHistory, Leave, Notification, LogEntry, Report, ReportSchedule,
    NFCReader, AccessPoint, AccessRule,
    LoginAttempt, UserSession, PasswordReset
)
from django.contrib.auth.password_validation import validate_password

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            'id',
            'name',
            'code',
            'description',
            'manager',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser'
        ]
        read_only_fields = ['id', 'is_superuser', 'is_staff']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'password2',
            'email',
            'first_name',
            'last_name'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), 
        source='department', 
        write_only=True, 
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',
            'matricule',
            'department',
            'department_id',
            'role',
            'phone_number',
            'address',
            'emergency_contact',
            'emergency_phone',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'matricule', 'created_at', 'updated_at']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), 
        source='department', 
        write_only=True, 
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'phone_number',
            'address',
            'emergency_contact',
            'emergency_phone',
            'department_id',
            'role',
        ]

class LoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempt
        fields = [
            'id',
            'user',
            'ip_address',
            'timestamp',
            'success',
            'user_agent',
        ]
        read_only_fields = ['id', 'user', 'timestamp', 'success', 'user_agent']


class UserSessionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = UserSession
        fields = [
            'id',
            'user',
            'session_key',
            'ip_address',
            'user_agent',
            'last_activity',
            'created_at',
            'is_active',
        ]
        read_only_fields = ['id', 'user', 'session_key', 'ip_address', 'user_agent', 'last_activity', 'created_at']


class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = [
            'id',
            'user',
            'token',
            'created_at',
            'used',
            'ip_address',
        ]
        read_only_fields = ['id', 'user', 'token', 'created_at', 'used', 'ip_address']


class LogEntrySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LogEntry
        fields = [
            'id',
            'user',
            'action',
            'timestamp',
            'ip_address',
            'user_agent',
        ]
        read_only_fields = ['id', 'user', 'action', 'timestamp', 'ip_address', 'user_agent']