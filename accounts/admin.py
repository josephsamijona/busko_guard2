# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Employee, Department, Schedule

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_admin', 'is_employee')
    list_filter = ('is_admin', 'is_employee')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'department', 'position', 'status')
    list_filter = ('status', 'department', 'gender')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'position')
    date_hierarchy = 'date_joined'

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week',)