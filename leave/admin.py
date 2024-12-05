# leaves/admin.py
from django.contrib import admin
from .models import Leave, LeaveBalance

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'reason')
    date_hierarchy = 'start_date'
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['APPROVED', 'REJECTED']:
            return ['employee', 'leave_type', 'start_date', 'end_date']
        return []

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_days', 'used_days', 'remaining_days')
    list_filter = ('leave_type', 'year')
    search_fields = ('employee__employee_id', 'employee__user__first_name')