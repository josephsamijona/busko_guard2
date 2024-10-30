# presence/urls.py

from django.urls import path, include
from rest_framework import routers
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
    access_point_access
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

urlpatterns = [
    path('', include(router.urls)),
    path('access-points/<int:access_point_id>/access/', access_point_access, name='access_point_access'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
