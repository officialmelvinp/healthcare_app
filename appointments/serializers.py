from rest_framework import serializers
from .models import Appointment, AppointmentFeedback
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class AppointmentSerializer(serializers.ModelSerializer):
    patient = UserSerializer(read_only=True)
    doctor = UserSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(source='doctor', queryset=User.objects.filter(is_doctor=True), write_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'doctor_id', 'date_time', 'status', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        doctor = validated_data.pop('doctor')
        patient = self.context['request'].user
        return Appointment.objects.create(doctor=doctor, patient=patient, **validated_data)

class AppointmentFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentFeedback
        fields = ['id', 'appointment', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']