# leaves/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import Leave, LeaveBalance

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'days_count', 'approved_by')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'reason')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at', 'approved_at')
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'leave_type')
        }),
        ('Leave Details', {
            'fields': ('start_date', 'end_date', 'reason', 'status')
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['APPROVED', 'REJECTED']:
            return [
                'employee', 'leave_type', 'start_date', 'end_date', 
                'created_at', 'updated_at', 'approved_at', 'approved_by'
            ]
        return ['created_at', 'updated_at', 'approved_at']

    def save_model(self, request, obj, form, change):
        # Gérer l'approbation et le rejet
        if change and 'status' in form.changed_data:
            if obj.status in ['APPROVED', 'REJECTED']:
                obj.approved_by = request.user
                obj.approved_at = timezone.now()
                
            # Si le statut change pour "APPROVED", mettre à jour le solde
            if obj.status == 'APPROVED':
                try:
                    balance = LeaveBalance.objects.get(
                        employee=obj.employee,
                        leave_type=obj.leave_type,
                        year=obj.start_date.year
                    )
                    balance.used_days = balance.used_days + obj.days_count()
                    balance.save()
                except LeaveBalance.DoesNotExist:
                    self.message_user(
                        request,
                        f"Warning: No leave balance found for {obj.leave_type} in {obj.start_date.year}",
                        level='WARNING'
                    )
        
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ['APPROVED', 'REJECTED']:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_days', 'used_days', 'remaining_days')
    list_filter = ('leave_type', 'year')
    search_fields = ('employee__employee_id', 'employee__user__first_name')
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'leave_type', 'year')
        }),
        ('Balance Details', {
            'fields': ('total_days', 'used_days')
        })
    )
    
    def remaining_days(self, obj):
        return obj.remaining_days()
    remaining_days.short_description = 'Remaining Days'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # En mode édition
            return ['employee', 'leave_type', 'year']
        return []