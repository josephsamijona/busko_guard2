# accounts/views.py
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import Department
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Employee
from accounts.serializers import CustomTokenObtainPairSerializer ,DepartmentSerializer, EmployeeSerializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=True, methods=['post'])
    def nfc(self, request, pk=None):
        employee = self.get_object()
        nfc_id = request.data.get('nfc_id')
        
        if not nfc_id:
            return Response(
                {'error': 'NFC ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        employee.nfc_id = nfc_id
        employee.save()
        return Response(EmployeeSerializer(employee).data)

    @action(detail=True, methods=['post'])
    def face(self, request, pk=None):
        employee = self.get_object()
        face_id = request.data.get('face_id')
        
        if not face_id:
            return Response(
                {'error': 'Face ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        employee.face_id = face_id
        employee.save()
        return Response(EmployeeSerializer(employee).data)