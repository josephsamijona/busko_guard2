# leaves/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Leave, LeaveBalance
from .serializers import LeaveSerializer, LeaveBalanceSerializer
from django.utils import timezone

class LeaveListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        queryset = Leave.objects.all()
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        serializer = LeaveSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LeaveSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        serializer = LeaveSerializer(leave)
        return Response(serializer.data)

    def put(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        serializer = LeaveSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        if leave.status != 'PENDING':
            return Response(
                {'error': 'Cette demande a déjà été traitée'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        leave.status = 'APPROVED'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()

        # Mettre à jour le solde de congés
        balance = LeaveBalance.objects.get(
            employee=leave.employee,
            leave_type=leave.leave_type,
            year=leave.start_date.year
        )
        balance.used_days += leave.days_count()
        balance.save()

        return Response({'status': 'Demande approuvée'})

class LeaveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk)
        if leave.status != 'PENDING':
            return Response(
                {'error': 'Cette demande a déjà été traitée'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        leave.status = 'REJECTED'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()

        return Response({'status': 'Demande rejetée'})

class LeaveBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        balances = LeaveBalance.objects.filter(
            employee_id=employee_id,
            year=timezone.now().year
        )
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)