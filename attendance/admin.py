# attendance/admin.py
from django.contrib import admin
from .models import Attendance, TemporaryQRCode

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'status', 'attendance_type')
    list_filter = ('status', 'attendance_type', 'date')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'employee__user__last_name')
    date_hierarchy = 'date'

@admin.register(TemporaryQRCode)
class TemporaryQRCodeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'purpose', 'is_used', 'expiry', 'created_at')
    list_filter = ('is_used', 'purpose')
    search_fields = ('employee__employee_id', 'code')
    date_hierarchy = 'created_at'