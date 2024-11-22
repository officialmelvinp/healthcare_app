from rest_framework import viewsets, permissions, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg
from .models import Appointment, AppointmentFeedback
from .serializers import AppointmentSerializer, AppointmentFeedbackSerializer
from .permissions import IsPatientOrDoctorOrAdmin, CanViewAppointment, CanEditAppointment

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsPatientOrDoctorOrAdmin]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['status', 'doctor__username', 'patient__username']
    ordering_fields = ['status', 'date_time']
    filterset_fields = ['status', 'date_time']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Appointment.objects.all()
        elif user.is_patient:
            return Appointment.objects.filter(patient=user)
        elif user.is_doctor:
            return Appointment.objects.filter(doctor=user)
        return Appointment.objects.none()

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            permission_classes = [IsPatientOrDoctorOrAdmin, CanViewAppointment]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsPatientOrDoctorOrAdmin, CanEditAppointment]
        else:
            permission_classes = [IsPatientOrDoctorOrAdmin]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_patient:
            raise serializers.ValidationError("Only patients can book appointments.")
        serializer.save()
        
        
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if request.user.is_doctor and appointment.doctor != request.user:
            return Response({'error': 'You can only cancel your own appointments.'}, status=status.HTTP_403_FORBIDDEN)
        appointment.status = 'CANCELLED'
        appointment.save()
        return Response({'status': 'appointment cancelled'})

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        if request.user.is_doctor and appointment.doctor != request.user:
            return Response({'error': 'You can only reschedule your own appointments.'}, status=status.HTTP_403_FORBIDDEN)
        new_date_time = request.data.get('new_date_time')
        if not new_date_time:
            return Response({'error': 'New date and time are required.'}, status=status.HTTP_400_BAD_REQUEST)
        appointment.date_time = new_date_time
        appointment.save()
        return Response({'status': 'appointment rescheduled'})

class AppointmentFeedbackViewSet(viewsets.ModelViewSet):
    queryset = AppointmentFeedback.objects.all()
    serializer_class = AppointmentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AppointmentFeedback.objects.all()
        elif user.is_patient:
            return AppointmentFeedback.objects.filter(appointment__patient=user)
        elif user.is_doctor:
            return AppointmentFeedback.objects.filter(appointment__doctor=user)
        return AppointmentFeedback.objects.none()

    def perform_create(self, serializer):
        appointment = serializer.validated_data['appointment']
        if self.request.user != appointment.patient:
            raise serializers.ValidationError("You can only provide feedback for your own appointments.")
        serializer.save()

    @action(detail=False, methods=['get'])
    def doctor_average_rating(self, request):
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response({'error': 'doctor_id is required'}, status=400)
        
        average_rating = self.get_queryset().filter(appointment__doctor_id=doctor_id).aggregate(Avg('rating'))
        return Response({'average_rating': average_rating['rating__avg']})

