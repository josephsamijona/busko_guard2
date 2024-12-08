# leaves/admin.py
from django.contrib import admin
from django.utils import timezone
from django.contrib.admin.models import LogEntry
from .models import Leave, LeaveBalance

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'days_count', 'approved_by')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'reason')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at', 'approved_at')

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une nouvelle création
            obj.created_by = request.user
        if 'status' in form.changed_data and obj.status in ['APPROVED', 'REJECTED']:
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
        obj.save()

    def log_addition(self, request, object, message):
        """
        Override pour gérer l'enregistrement des logs d'ajout
        """
        try:
            return super().log_addition(request, object, message)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log d'ajout: {e}")
            return None

    def log_change(self, request, object, message):
        """
        Override pour gérer l'enregistrement des logs de modification
        """
        try:
            return super().log_change(request, object, message)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log de modification: {e}")
            return None

    def log_deletion(self, request, object, object_repr):
        """
        Override pour gérer l'enregistrement des logs de suppression
        """
        try:
            return super().log_deletion(request, object, object_repr)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log de suppression: {e}")
            return None

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_days', 'used_days', 'get_remaining_days')
    list_filter = ('leave_type', 'year')
    search_fields = ('employee__employee_id', 'employee__user__first_name')

    def get_remaining_days(self, obj):
        return obj.remaining_days()
    get_remaining_days.short_description = 'Remaining Days'

    def save_model(self, request, obj, form, change):
        obj.save()

    def log_addition(self, request, object, message):
        try:
            return super().log_addition(request, object, message)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log d'ajout: {e}")
            return None

    def log_change(self, request, object, message):
        try:
            return super().log_change(request, object, message)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log de modification: {e}")
            return None

    def log_deletion(self, request, object, object_repr):
        try:
            return super().log_deletion(request, object, object_repr)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log de suppression: {e}")
            return None

    def has_delete_permission(self, request, obj=None):
        if obj and obj.used_days > 0:
            return False
        return super().has_delete_permission(request, obj)