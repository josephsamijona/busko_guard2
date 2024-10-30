# core/urls.py

from django.urls import path, include
from rest_framework import routers
from .views import (
    DepartmentViewSet, UserViewSet, UserProfileViewSet,
    LoginAttemptViewSet, UserSessionViewSet, PasswordResetViewSet, LogEntryViewSet,NFCCardViewSet
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'login-attempts', LoginAttemptViewSet, basename='loginattempt')
router.register(r'user-sessions', UserSessionViewSet, basename='usersession')
router.register(r'password-resets', PasswordResetViewSet, basename='passwordreset')
router.register(r'log-entries', LogEntryViewSet, basename='logentry')
router.register(r'nfc-cards', NFCCardViewSet, basename='nfccard')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
