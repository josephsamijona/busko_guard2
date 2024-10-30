# core/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .nfc_utils import write_card_uid
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
            'success',
            'created_at',  # Remplacez 'timestamp' par 'created_at'
            'user_agent',
        ]
        read_only_fields = ['id', 'user', 'ip_address', 'success', 'created_at', 'user_agent']

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
        read_only_fields = ['id', 'user', 'session_key', 'ip_address', 'user_agent', 'last_activity', 'created_at', 'is_active']

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
            'created_at',  # Remplacez 'timestamp' par 'created_at'
            'ip_address',
            'user_agent',
        ]
        read_only_fields = ['id', 'user', 'action', 'created_at', 'ip_address', 'user_agent']
        
class NFCCardSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user_full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NFCCard
        fields = [
            'id',
            'user',
            'user_full_name',
            'card_uid',
            'status',
            'issue_date',
            'expiry_date',
            'last_used',
            'is_active',
            'access_level',
            'security_hash',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_full_name', 'security_hash']

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()

    def validate_expiry_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("La date d'expiration ne peut pas être dans le passé.")
        return value

    def create(self, validated_data):
        # Générer le security_hash, qui peut être un hash de card_uid et d'une clé secrète
        card_uid = validated_data.get('card_uid')
        security_hash = self.generate_security_hash(card_uid)
        validated_data['security_hash'] = security_hash

        # Écrire le card_uid sur la carte physique
        success, message = write_card_uid(card_uid)
        if not success:
            raise serializers.ValidationError({"card_uid": f"Échec de l'écriture sur la carte : {message}"})

        return super().create(validated_data)

    def generate_security_hash(self, card_uid):
        import hashlib
        secret = "votre_clé_secrète"
        return hashlib.sha256((card_uid + secret).encode('utf-8')).hexdigest()

class NFCReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFCReader
        fields = [
            'id',
            'identifier',
            'name',
            'location',
            'reader_type',
            'status',
            'ip_address',
            'last_maintenance',
            'next_maintenance',
            'firmware_version',
            'is_online',
            'last_online',
            'configuration',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_online', 'last_online', 'created_at', 'updated_at']

class AccessPointSerializer(serializers.ModelSerializer):
    reader = serializers.PrimaryKeyRelatedField(queryset=NFCReader.objects.all())
    allowed_departments = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        many=True
    )

    class Meta:
        model = AccessPoint
        fields = [
            'id',
            'name',
            'description',
            'reader',
            'is_active',
            'required_access_level',
            'allowed_departments',
            'schedule',
            'special_rules',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']