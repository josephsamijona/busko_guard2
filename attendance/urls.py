# attendance/urls.py
from django.urls import path
from .views import ValidateAttendanceView,  DailyReportView,AttendanceStatsView,CheckInView, CheckOutView ,AttendanceCheckViewqr,SaveQRCodeView,    AttendanceHistoryView, MonthlyReportView
from attendance.views import (
    DailyAnalyticsView,
    MonthlyAnalyticsView,
    AttendanceTrendsAnalyticsView
)

urlpatterns = [
    path('attendance/validate/', ValidateAttendanceView.as_view()),
    path('attendance/check-in/', CheckInView.as_view()),
    path('attendance/check-out/', CheckOutView.as_view()),
    path('qr/save/', SaveQRCodeView.as_view(), name='save_qr'),
    path('attendance/check/', AttendanceCheckViewqr.as_view(), name='attendance_check'),
    path('attendance/history/', AttendanceHistoryView.as_view(), name='attendance_history'),
    path('attendance/stats/', AttendanceStatsView.as_view(), name='attendance_stats'),
    path('attendance/daily-report/', DailyReportView.as_view(), name='daily_report'),
    path('attendance/monthly-report/', MonthlyReportView.as_view(), name='monthly_report'),
        # Rapports journaliers
    path('analytics/daily/', 
         DailyAnalyticsView.as_view(), 
         name='attendance-daily-analytics'),
    
    # Rapports mensuels
    path('analytics/monthly/', 
         MonthlyAnalyticsView.as_view(), 
         name='attendance-monthly-analytics'),
    
    # Tendances
    path('analytics/trends/', 
         AttendanceTrendsAnalyticsView.as_view(), 
         name='attendance-trends-analytics'),
]