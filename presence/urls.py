# presence/urls.py

from django.urls import path, include
from django.conf.urls.static import static
from rest_framework import routers
from django.conf import settings
from .views import (
    LoginAttemptViewSet,
    UserSessionViewSet,
    PasswordResetViewSet,
    LogEntryViewSet,
    NFCCardViewSet,
    DepartmentViewSet,
    UserViewSet,
    UserProfileViewSet,
    NFCReaderViewSet,
    AccessPointViewSet,
    AttendanceRuleViewSet,
    AccessRuleViewSet,
    AttendanceRecordViewSet,
    access_point_access,
    LeaveRequestViewSet, 
    LeaveApprovalViewSet, daily_attendance_report, monthly_attendance_report,
    NotificationViewSet,LeaveApprovalViewSetupnotif,
    ReportScheduleViewSet,
    ReportViewSet, PresenceStatisticsView,TemporaryQRCodeViewSet, display_qr_code, download_qr_code, SignupView, LoginView, TwoFactorVerifyView, UserProfileUpdateView
    


    
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'login-attempts', LoginAttemptViewSet, basename='loginattempt')
router.register(r'user-sessions', UserSessionViewSet, basename='usersession')
router.register(r'password-resets', PasswordResetViewSet, basename='passwordreset')
router.register(r'log-entries', LogEntryViewSet, basename='logentry')
router.register(r'nfc-cards', NFCCardViewSet, basename='nfccard')
router.register(r'departments', DepartmentViewSet)
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'nfc-readers', NFCReaderViewSet, basename='nfcreader')
router.register(r'access-points', AccessPointViewSet, basename='accesspoint')
router.register(r'attendance-rules', AttendanceRuleViewSet, basename='attendancerule')
router.register(r'access-rules', AccessRuleViewSet, basename='accessrule')
router.register(r'attendance-records', AttendanceRecordViewSet, basename='attendancerecord')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'leave-approvals', LeaveApprovalViewSet, basename='leaveapproval')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'LeaveApprovalViewSetup', LeaveApprovalViewSetupnotif, basename='LeaveApprovalViewSetup')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'report-schedules', ReportScheduleViewSet, basename='reportschedule')
router.register(r'temporary_qr_codes', TemporaryQRCodeViewSet, basename='temporary_qr_code')




urlpatterns = [
    path('', include(router.urls)),
    path('access-points/<int:access_point_id>/access/', access_point_access, name='access_point_access'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('attendance-report/<int:user_id>/<str:date_str>/', daily_attendance_report, name='daily_attendance_report'),
    path('monthly-attendance-report/<int:user_id>/<int:year>/<int:month>/', monthly_attendance_report, name='monthly_attendance_report'),
    path('statistics/presence/', PresenceStatisticsView.as_view(), name='presence_statistics'),
    path('qr_code_display/', display_qr_code, name='qr_code_display'),
    path('download_qr_code/', download_qr_code, name='download_qr_code'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('two_factor_verify/', TwoFactorVerifyView.as_view(), name='two_factor_verify'),
    path('profile/', UserProfileUpdateView.as_view(), name='profile'),
    
]
