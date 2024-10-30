# admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Department, UserProfile, NFCCard, AttendanceRule, AttendanceRecord, PresenceHistory,
    Leave, Notification, LogEntry, Report, ReportSchedule, NFCReader, AccessPoint,
    AccessRule, LoginAttempt, UserSession, PasswordReset, Reportfolder, TemporaryQRCode,
    TwoFactorCode
)

# Inline admin pour UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil Utilisateur'

# Admin personnalisé pour le modèle User
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = BaseUserAdmin.list_display + ('get_matricule', 'get_department', 'role')
    search_fields = BaseUserAdmin.search_fields + ('profile__matricule', 'profile__department__name', 'profile__role')
    list_filter = BaseUserAdmin.list_filter + ('profile__role', 'profile__department')

    def get_matricule(self, obj):
        return obj.profile.matricule
    get_matricule.short_description = 'Matricule'
    get_matricule.admin_order_field = 'profile__matricule'

    def get_department(self, obj):
        return obj.profile.department
    get_department.short_description = 'Département'
    get_department.admin_order_field = 'profile__department__name'

# Réenregistrer le modèle User avec l'admin personnalisé
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Admin pour Department
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'description', 'manager', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'code', 'description', 'manager__username', 'manager__first_name', 'manager__last_name')
    list_filter = ('is_active', 'manager')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'matricule', 'department', 'role', 'phone_number', 'address',
        'emergency_contact', 'emergency_phone', 'profile_image', 'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'matricule', 'department__name', 'role',
        'phone_number', 'emergency_contact', 'emergency_phone'
    )
    list_filter = ('role', 'department', 'is_active')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour NFCCard
@admin.register(NFCCard)
class NFCCardAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'card_uid', 'status', 'issue_date', 'expiry_date',
        'last_used', 'is_active', 'access_level', 'security_hash', 'notes',
        'created_at', 'updated_at'
    )
    search_fields = (
        'card_uid', 'user__username', 'user__first_name', 'user__last_name',
        'status', 'security_hash'
    )
    list_filter = ('status', 'is_active', 'access_level')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour AttendanceRule
@admin.register(AttendanceRule)
class AttendanceRuleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'department', 'start_time', 'end_time',
        'grace_period_minutes', 'minimum_hours', 'is_active', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'department__name')
    list_filter = ('is_active', 'department')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour AttendanceRecord
@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'timestamp', 'action_type', 'location', 'notes',
        'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'action_type', 'location__name'
    )
    list_filter = ('action_type', 'timestamp', 'location')
    ordering = ('-timestamp',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour PresenceHistory
@admin.register(PresenceHistory)
class PresenceHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'attendance_record', 'modified_by', 'modified_at',
        'previous_action_type', 'new_action_type', 'reason', 'created_at', 'updated_at'
    )
    search_fields = (
        'attendance_record__user__username', 'modified_by__username',
        'previous_action_type', 'new_action_type', 'reason'
    )
    list_filter = ('modified_at', 'modified_by')
    ordering = ('-modified_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour Leave
@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'leave_type', 'start_date', 'end_date',
        'status', 'reason', 'approved_by', 'approval_date',
        'comments', 'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'leave_type', 'status', 'reason', 'approved_by__username'
    )
    list_filter = ('leave_type', 'status', 'approved_by')
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour Notification
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'recipient', 'message', 'is_read',
        'notification_type', 'approved_by', 'start_date',
        'end_date', 'comments', 'created_at', 'updated_at'
    )
    search_fields = (
        'recipient__username', 'notification_type', 'message',
        'approved_by__username', 'comments'
    )
    list_filter = ('is_read', 'notification_type', 'start_date', 'end_date')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour LogEntry
@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'action', 'timestamp', 'ip_address', 'user_agent',
        'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'action', 'ip_address', 'user_agent'
    )
    list_filter = ('timestamp', 'user')
    ordering = ('-timestamp',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour Report
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'description', 'report_type', 'format',
        'status', 'created_by', 'file', 'error_message',
        'generation_time', 'created_at', 'updated_at'
    )
    search_fields = (
        'name', 'report_type', 'description', 'created_by__username',
        'status', 'error_message'
    )
    list_filter = ('report_type', 'format', 'status', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour ReportSchedule
@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'report', 'frequency', 'is_active',
        'next_run', 'last_run', 'send_empty',
        'created_at', 'updated_at'
    )
    search_fields = (
        'report__name', 'frequency', 'configuration'
    )
    list_filter = ('frequency', 'is_active', 'next_run', 'last_run')
    ordering = ('next_run',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour NFCReader
@admin.register(NFCReader)
class NFCReaderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'identifier', 'name', 'location', 'reader_type',
        'status', 'ip_address', 'last_maintenance',
        'next_maintenance', 'firmware_version', 'is_online',
        'last_online', 'configuration', 'created_at', 'updated_at'
    )
    search_fields = (
        'identifier', 'name', 'location', 'reader_type',
        'status', 'ip_address', 'firmware_version'
    )
    list_filter = ('reader_type', 'status', 'is_online', 'location')
    ordering = ('location', 'name')
    readonly_fields = ('created_at', 'updated_at')

# Admin pour AccessPoint
@admin.register(AccessPoint)
class AccessPointAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'description', 'reader', 'is_active',
        'required_access_level', 'created_at', 'updated_at'
    )
    search_fields = (
        'name', 'description', 'reader__name', 'required_access_level'
    )
    list_filter = ('is_active', 'reader')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour AccessRule
@admin.register(AccessRule)
class AccessRuleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'rule_type', 'access_point', 'priority',
        'is_active', 'start_date', 'end_date', 'description',
        'created_at', 'updated_at'
    )
    search_fields = (
        'name', 'rule_type', 'access_point__name',
        'description', 'departments__name'
    )
    list_filter = ('rule_type', 'is_active', 'start_date', 'end_date', 'departments')
    ordering = ('-priority', 'name')
    readonly_fields = ('created_at', 'updated_at')

# Admin pour LoginAttempt
@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'ip_address', 'success', 'user_agent',
        'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'ip_address', 'user_agent'
    )
    list_filter = ('success', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour UserSession
@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'session_key', 'ip_address',
        'user_agent', 'last_activity', 'is_active',
        'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'session_key', 'ip_address', 'user_agent'
    )
    list_filter = ('is_active', 'last_activity')
    ordering = ('-last_activity',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour PasswordReset
@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'token', 'used', 'ip_address',
        'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'token', 'ip_address'
    )
    list_filter = ('used', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour Reportfolder
@admin.register(Reportfolder)
class ReportfolderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'report_type', 'file', 'format',
        'status', 'generated_at', 'error_message',
        'created_at', 'updated_at'
    )
    search_fields = (
        'name', 'report_type', 'file', 'format',
        'status', 'error_message'
    )
    list_filter = ('report_type', 'format', 'status', 'generated_at')
    ordering = ('-generated_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour TemporaryQRCode
@admin.register(TemporaryQRCode)
class TemporaryQRCodeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'code', 'created_at', 'expires_at',
        'is_used', 'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'code', 'is_used'
    )
    list_filter = ('is_used', 'expires_at')
    ordering = ('-expires_at',)
    readonly_fields = ('created_at', 'updated_at')

# Admin pour TwoFactorCode
@admin.register(TwoFactorCode)
class TwoFactorCodeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'code', 'created_at', 'is_used',
        'updated_at'
    )
    search_fields = (
        'user__username', 'code', 'is_used'
    )
    list_filter = ('is_used', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
