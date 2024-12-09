# leaves/urls.py
from django.urls import path
from .views import (
    LeaveListCreateView,
    LeaveDetailView,
    LeaveApproveView,
    LeaveRejectView,
    LeaveBalanceView,LeaveCreateView,   DashboardStatsView,
    WeeklyAttendanceStatsView,
    RecentAlertsView
)

urlpatterns = [
    path('leaves/', LeaveListCreateView.as_view(), name='leave-list-create'),
    path('leaves/create/', LeaveCreateView.as_view(), name='leave-create'),
    path('leaves/<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),
    path('leaves/<int:pk>/approve/', LeaveApproveView.as_view(), name='leave-approve'),
    path('leaves/<int:pk>/reject/', LeaveRejectView.as_view(), name='leave-reject'),
    path('leaves/balance/<int:employee_id>/', LeaveBalanceView.as_view(), name='leave-balance'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/weekly-attendance/', WeeklyAttendanceStatsView.as_view(), name='weekly-attendance'),
    path('dashboard/alerts/', RecentAlertsView.as_view(), name='recent-alerts'),
]
