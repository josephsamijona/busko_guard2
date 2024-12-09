# accounts/serializers.py
from datetime import timezone
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
    
    
class EmployeeUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number')

class DepartmentManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'description')

class EmployeeManagementListSerializer(serializers.ModelSerializer):
    user = EmployeeUserSerializer()
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Employee
        fields = (
            'id', 
            'employee_id', 
            'user',
            'full_name',
            'department',
            'department_name',
            'position',
            'status',
            'gender',
            'date_joined',
            'nfc_id',
            'face_id'
        )

class EmployeeManagementCreateSerializer(serializers.ModelSerializer):
    user = EmployeeUserSerializer()
    
    class Meta:
        model = Employee
        fields = (
            'id', 
            'employee_id', 
            'user',
            'department',
            'position',
            'status',
            'gender',
            'date_of_birth',
            'date_joined',
            'nfc_id',
            'face_id'
        )

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone_number=user_data.get('phone_number', ''),
            password='password123'  # Mot de passe temporaire
        )
        
        # Créer l'employé
        employee = Employee.objects.create(user=user, **validated_data)
        return employee

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        return super().update(instance, validated_data)
    
    
    
class UserCreationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'confirm_password', 
                 'is_employee', 'is_admin', 'first_name', 'last_name')
        extra_kwargs = {
            'is_employee': {'default': True},
            'is_admin': {'default': False}
        }

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_employee=validated_data.get('is_employee', True),
            is_admin=validated_data.get('is_admin', False),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class EmployeeBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('employee_id', 'department', 'position', 'gender', 
                 'date_of_birth', 'date_joined')

class EmployeeNFCSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('nfc_id',)

    def validate_nfc_id(self, value):
        if Employee.objects.filter(nfc_id=value).exists():
            raise serializers.ValidationError("Cet identifiant NFC est déjà utilisé")
        return value

class EmployeeFaceIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('face_id',)

    def validate_face_id(self, value):
        if Employee.objects.filter(face_id=value).exists():
            raise serializers.ValidationError("Cet identifiant facial est déjà utilisé")
        return value
    
class DepartmentDetailSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ('id', 'name', 'description', 'employee_count', 'attendance_rate', 'created_at')

    def get_employee_count(self, obj):
        return Employee.objects.filter(department=obj, status='ACTIVE').count()

    def get_attendance_rate(self, obj):
        total_employees = self.get_employee_count(obj)
        if total_employees == 0:
            return 0
        present_employees = Employee.objects.filter(
            department=obj,
            status='ACTIVE',
            attendance__status__in=['PRESENT', 'LATE'],
            attendance__date=timezone.now().date()
        ).count()
        return round((present_employees / total_employees) * 100, 1) if total_employees > 0 else 0

class DepartmentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'description')