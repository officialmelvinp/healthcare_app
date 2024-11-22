from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import PatientProfile, DoctorProfile
from .serializers import UserSerializer, PatientProfileSerializer, DoctorProfileSerializer, UserProfileSerializer
from .permissions import IsOwnerOrReadOnly, IsDoctorOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import logging


User = get_user_model()
logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'update_profile']:
            return UserProfileSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def profile(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response({"message": "Profile retrieved successfully", "data": serializer.data})

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_user = serializer.save()
                updated_serializer = self.get_serializer(updated_user)
                return Response({"message": "Profile updated successfully", "data": updated_serializer.data})
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'])
    def set_role(self, request):
        user = request.user
        role = request.data.get("role")
        
        if role not in ["patient", "doctor"]:
            return Response({"error": "Invalid role. Choose either 'patient' or 'doctor'."}, status=status.HTTP_400_BAD_REQUEST)

        if (role == "patient" and user.is_doctor) or (role == "doctor" and user.is_patient):
            return Response({"error": "You cannot change your role once it's set."}, status=status.HTTP_400_BAD_REQUEST)

        if role == "patient":
            user.is_patient = True
            user.is_doctor = False
            PatientProfile.objects.get_or_create(user=user)
        elif role == "doctor":
            user.is_doctor = True
            user.is_patient = False
            DoctorProfile.objects.get_or_create(user=user)
        
        user.save()
        return Response({"message": "Role updated successfully", "role": role})


class PatientProfileViewSet(viewsets.ModelViewSet):
    queryset = PatientProfile.objects.all()
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return PatientProfile.objects.all()
        return PatientProfile.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        return Response(
            {"error": "Patient profile is automatically created with user. Use update instead."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({"message": "Patient profile updated successfully", "data": serializer.data})
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class DoctorProfileViewSet(viewsets.ModelViewSet):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return DoctorProfile.objects.all()
        return DoctorProfile.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if DoctorProfile.objects.filter(user=request.user).exists():
            return Response(
                {"error": "Doctor profile already exists for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({"message": "Doctor profile created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({"message": "Doctor profile updated successfully", "data": serializer.data})



