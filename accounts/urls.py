# accounts/urls.py
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    CustomTokenObtainPairView, 
    LogoutView,  
    EmployeeViewSet, 
    DepartmentViewSet,
    get_employee_dashboard,
    get_leave_balance,
    get_attendance_status
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'departments', DepartmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Auth endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    
    # Dashboard endpoints
    path('dashboard/', get_employee_dashboard, name='employee-dashboard'),
    path('leaves/balance/', get_leave_balance, name='leave-balance'),
    path('attendance/status/', get_attendance_status, name='attendance-status'),
]