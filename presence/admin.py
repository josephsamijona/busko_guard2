# core/admin.py

from django.contrib import admin
from .models import (
    Department, UserProfile, NFCCard, AttendanceRule, AttendanceRecord,
    PresenceHistory, Leave, Notification, LogEntry, Report, ReportSchedule,
    NFCReader, AccessPoint, AccessRule,
    LoginAttempt, UserSession, PasswordReset
)
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'manager', 'is_active')
    search_fields = ('code', 'name', 'manager__username', 'manager__first_name', 'manager__last_name')
    list_filter = ('is_active',)
    ordering = ('name',)
    fields = ('code', 'name', 'description', 'manager', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'matricule', 'department', 'role', 'phone_number')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'matricule', 'phone_number')
    list_filter = ('role', 'department')
    fields = (
        'user', 'matricule', 'department', 'role', 'phone_number', 'address',
        'emergency_contact', 'emergency_phone', 'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(NFCCard)
class NFCCardAdmin(admin.ModelAdmin):
    list_display = ('card_uid', 'user', 'status', 'issue_date', 'expiry_date', 'last_used', 'is_active')
    search_fields = ('card_uid', 'user__username', 'user__first_name', 'user__last_name')
    list_filter = ('status', 'is_active')
    fields = (
        'user', 'card_uid', 'status', 'issue_date', 'expiry_date', 'last_used',
        'is_active', 'access_level', 'security_hash', 'notes', 'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AttendanceRule)
class AttendanceRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'start_time', 'end_time', 'is_active')
    search_fields = ('name', 'department__name')
    list_filter = ('department', 'is_active')
    fields = (
        'name', 'department', 'start_time', 'end_time', 'grace_period_minutes',
        'minimum_hours', 'is_active', 'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'action_type', 'location')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'location__name')
    list_filter = ('action_type', 'timestamp')
    date_hierarchy = 'timestamp'
    fields = ('user', 'timestamp', 'action_type', 'location', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PresenceHistory)
class PresenceHistoryAdmin(admin.ModelAdmin):
    list_display = ('attendance_record', 'modified_by', 'modified_at', 'previous_action_type', 'new_action_type')
    search_fields = (
        'attendance_record__user__username', 'attendance_record__user__first_name',
        'attendance_record__user__last_name', 'modified_by__username', 'modified_by__first_name', 'modified_by__last_name'
    )
    list_filter = ('modified_at',)
    date_hierarchy = 'modified_at'
    fields = (
        'attendance_record', 'modified_by', 'modified_at', 'previous_action_type',
        'new_action_type', 'reason', 'created_at', 'updated_at'
    )
    readonly_fields = ('modified_at', 'created_at', 'updated_at')

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by', 'approval_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'approved_by__username')
    list_filter = ('leave_type', 'status', 'start_date')
    date_hierarchy = 'start_date'
    fields = (
        'user', 'leave_type', 'start_date', 'end_date', 'status', 'reason',
        'approved_by', 'approval_date', 'comments', 'created_at', 'updated_at'
    )
    readonly_fields = ('approval_date', 'created_at', 'updated_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'recipient__first_name', 'recipient__last_name', 'message')
    list_filter = ('notification_type', 'is_read', 'created_at')
    date_hierarchy = 'created_at'
    fields = ('recipient', 'message', 'is_read', 'notification_type', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'action', 'ip_address')
    list_filter = ('timestamp',)
    date_hierarchy = 'timestamp'
    fields = ('user', 'action', 'timestamp', 'ip_address', 'user_agent', 'created_at', 'updated_at')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'format', 'status', 'created_by', 'created_at')
    search_fields = ('name', 'created_by__username', 'created_by__first_name', 'created_by__last_name')
    list_filter = ('report_type', 'format', 'status')
    date_hierarchy = 'created_at'
    fields = (
        'name', 'description', 'report_type', 'format', 'status', 'parameters',
        'created_by', 'file', 'error_message', 'generation_time', 'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('report', 'frequency', 'is_active', 'next_run', 'last_run')
    search_fields = ('report__name',)
    list_filter = ('frequency', 'is_active')
    date_hierarchy = 'next_run'
    fields = (
        'report', 'frequency', 'is_active', 'next_run', 'last_run', 'recipients',
        'send_empty', 'configuration', 'created_at', 'updated_at'
    )
    readonly_fields = ('last_run', 'created_at', 'updated_at')

@admin.register(NFCReader)
class NFCReaderAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'name', 'location', 'reader_type', 'status', 'is_online', 'last_online')
    search_fields = ('identifier', 'name', 'location')
    list_filter = ('reader_type', 'status', 'is_online')
    fields = (
        'identifier', 'name', 'location', 'reader_type', 'status', 'ip_address',
        'last_maintenance', 'next_maintenance', 'firmware_version', 'is_online',
        'last_online', 'configuration', 'created_at', 'updated_at'
    )
    readonly_fields = ('last_online', 'created_at', 'updated_at')

@admin.register(AccessPoint)
class AccessPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'reader', 'is_active', 'required_access_level')
    search_fields = ('name', 'reader__name')
    list_filter = ('is_active',)
    fields = (
        'name', 'description', 'reader', 'is_active', 'required_access_level',
        'allowed_departments', 'schedule', 'special_rules', 'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('allowed_departments',)

@admin.register(AccessRule)
class AccessRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'access_point', 'priority', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'access_point__name')
    list_filter = ('rule_type', 'is_active')
    date_hierarchy = 'start_date'
    fields = (
        'name', 'rule_type', 'access_point', 'priority', 'conditions', 'is_active',
        'start_date', 'end_date', 'departments', 'description', 'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('departments',)
@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'success', 'created_at', 'user_agent')  # Remplacez 'timestamp' par 'created_at'
    search_fields = ('user__username', 'ip_address', 'user_agent')
    list_filter = ('success', 'created_at')  # Remplacez 'timestamp' par 'created_at'
    ordering = ('-created_at',)  # Remplacez 'timestamp' par 'created_at'
    readonly_fields = ('user', 'ip_address', 'success', 'created_at', 'user_agent')  # Remplacez 'timestamp' par 'created_at'

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'ip_address', 'user_agent', 'last_activity', 'is_active')
    search_fields = ('user__username', 'ip_address', 'user_agent')
    list_filter = ('is_active', 'last_activity')
    ordering = ('-last_activity',)
    readonly_fields = ('user', 'session_key', 'ip_address', 'user_agent', 'last_activity', 'is_active')

@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'used', 'ip_address', 'created_at')
    search_fields = ('user__username', 'token', 'ip_address')
    list_filter = ('used', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'token', 'used', 'ip_address', 'created_at')