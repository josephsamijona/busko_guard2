from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Employee, Department, Schedule

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_admin', 'is_employee')
    list_filter = ('is_admin', 'is_employee', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Role'), {'fields': ('is_employee', 'is_admin')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_employee', 'is_admin'),
        }),
    )

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'department', 'position', 'status')
    list_filter = ('status', 'department', 'gender')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'position')
    raw_id_fields = ('user',)
    date_hierarchy = 'date_joined'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'position', 'department')
        }),
        ('Personal Details', {
            'fields': ('gender', 'date_of_birth', 'date_joined', 'status')
        }),
        ('Authentication Methods', {
            'fields': ('nfc_id', 'face_id'),
            'classes': ('collapse',),
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'department')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
    )

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'get_employee_name', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week', 'employee__department')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'employee__user__last_name')
    raw_id_fields = ('employee',)

    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    get_employee_name.short_description = 'Employee Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'employee__user')

    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
        js = ('admin/js/calendar.js', 'admin/js/admin/DateTimeShortcuts.js')