# leaves/views.py
from datetime import datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Leave, LeaveBalance
from .serializers import LeaveSerializer, LeaveBalanceSerializer
from django.utils import timezone


class LeaveCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Récupérer l'employé à partir de l'utilisateur connecté
            employee = request.user.employee
            
            # Parser les dates
            try:
                start_date = datetime.strptime(
                    request.data.get('start_date'), 
                    '%Y-%m-%d'
                ).date()
                end_date = datetime.strptime(
                    request.data.get('end_date'), 
                    '%Y-%m-%d'
                ).date()
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Format de date invalide. Utilisez YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Créer la demande de congé
            leave = Leave.objects.create(
                employee=employee,
                leave_type=request.data.get('leave_type'),
                start_date=start_date,
                end_date=end_date,
                reason=request.data.get('reason', ''),
                status='PENDING'
            )

            # Calculer le nombre de jours
            days_requested = (end_date - start_date).days + 1

            # Sérialiser et renvoyer la réponse
            serializer = LeaveSerializer(leave)
            return Response(
                {
                    'message': 'Demande de congé créée avec succès',
                    'leave': serializer.data,
                    'days_requested': days_requested
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )











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