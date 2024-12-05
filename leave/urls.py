# leaves/urls.py
from django.urls import path
from .views import (
    LeaveListCreateView,
    LeaveDetailView,
    LeaveApproveView,
    LeaveRejectView,
    LeaveBalanceView
)

urlpatterns = [
    path('leaves/', LeaveListCreateView.as_view(), name='leave-list-create'),
    path('leaves/<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),
    path('leaves/<int:pk>/approve/', LeaveApproveView.as_view(), name='leave-approve'),
    path('leaves/<int:pk>/reject/', LeaveRejectView.as_view(), name='leave-reject'),
    path('leaves/balance/<int:employee_id>/', LeaveBalanceView.as_view(), name='leave-balance'),
]
