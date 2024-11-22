from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Appointment, AppointmentFeedback
from .serializers import AppointmentSerializer, AppointmentFeedbackSerializer
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class AppointmentModelTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username='patient', email='patient@example.com', password='testpass123', is_patient=True)
        self.doctor = User.objects.create_user(username='doctor', email='doctor@example.com', password='testpass123', is_doctor=True)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date_time=timezone.now() + timedelta(days=1),
            status='SCHEDULED'
        )

    def test_appointment_creation(self):
        self.assertTrue(isinstance(self.appointment, Appointment))
        self.assertEqual(str(self.appointment), f"Appointment with Dr. {self.doctor.username} for {self.patient.username} on {self.appointment.date_time}")

    def test_appointment_status(self):
        self.assertEqual(self.appointment.status, 'SCHEDULED')
        self.appointment.status = 'COMPLETED'
        self.appointment.save()
        self.assertEqual(self.appointment.status, 'COMPLETED')

class AppointmentFeedbackModelTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username='patient', email='patient@example.com', password='testpass123', is_patient=True)
        self.doctor = User.objects.create_user(username='doctor', email='doctor@example.com', password='testpass123', is_doctor=True)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date_time=timezone.now() + timedelta(days=1),
            status='SCHEDULED'
        )
        self.feedback = AppointmentFeedback.objects.create(
            appointment=self.appointment,
            rating=5,
            comment="Great service!"
        )

    def test_feedback_creation(self):
        self.assertTrue(isinstance(self.feedback, AppointmentFeedback))
        self.assertEqual(str(self.feedback), f"Feedback for appointment {self.appointment.id}")

    def test_feedback_rating(self):
        self.assertEqual(self.feedback.rating, 5)
        self.feedback.rating = 4
        self.feedback.save()
        self.assertEqual(self.feedback.rating, 4)

class AppointmentSerializerTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username='patient', email='patient@example.com', password='testpass123', is_patient=True)
        self.doctor = User.objects.create_user(username='doctor', email='doctor@example.com', password='testpass123', is_doctor=True)
        self.appointment_data = {
            'doctor_id': self.doctor.id,
            'date_time': timezone.now() + timedelta(days=1),
            'status': 'SCHEDULED'
        }

    def test_appointment_serializer_create(self):
        context = {'request': type('obj', (object,), {'user': self.patient})}
        serializer = AppointmentSerializer(data=self.appointment_data, context=context)
        self.assertTrue(serializer.is_valid())
        appointment = serializer.save()
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)

    

class AppointmentFeedbackSerializerTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username='patient', email='patient@example.com', password='testpass123', is_patient=True)
        self.doctor = User.objects.create_user(username='doctor', email='doctor@example.com', password='testpass123', is_doctor=True)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date_time=timezone.now() + timedelta(days=1),
            status='SCHEDULED'
        )
        self.feedback_data = {
            'appointment': self.appointment.id,
            'rating': 5,
            'comment': "Excellent service!"
        }

    def test_feedback_serializer_create(self):
        serializer = AppointmentFeedbackSerializer(data=self.feedback_data)
        self.assertTrue(serializer.is_valid())
        feedback = serializer.save()
        self.assertEqual(feedback.appointment, self.appointment)
        self.assertEqual(feedback.rating, 5)

class AppointmentViewSetTests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username='patient', email='patient@example.com', password='testpass123', is_patient=True)
        self.doctor = User.objects.create_user(username='doctor', email='doctor@example.com', password='testpass123', is_doctor=True)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date_time=timezone.now() + timedelta(days=1),
            status='SCHEDULED'
        )
        self.client.force_authenticate(user=self.patient)

    def test_list_appointments(self):
        url = reverse('appointment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_appointment(self):
        url = reverse('appointment-list')
        data = {
            'doctor_id': self.doctor.id,
            'date_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'status': 'SCHEDULED'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 2)
        self.assertEqual(response.data['patient']['id'], self.patient.id)
        self.assertEqual(response.data['doctor']['id'], self.doctor.id)
        
        
    def test_cancel_appointment(self):
        url = reverse('appointment-cancel', kwargs={'pk': self.appointment.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CANCELLED')

    def test_reschedule_appointment(self):
        url = reverse('appointment-reschedule', kwargs={'pk': self.appointment.pk})
        new_date_time = timezone.now() + timedelta(days=3)
        data = {'new_date_time': new_date_time.isoformat()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.date_time, new_date_time)
        
        
    def test_doctor_cannot_create_appointment(self):
        self.client.force_authenticate(user=self.doctor)
        url = reverse('appointment-list')
        data = {
            'doctor_id': self.doctor.id,
            'date_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'status': 'SCHEDULED'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Appointment.objects.count(), 1)

class AppointmentFeedbackViewSetTests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username='patient', email='patient@example.com', password='testpass123', is_patient=True)
        self.doctor = User.objects.create_user(username='doctor', email='doctor@example.com', password='testpass123', is_doctor=True)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date_time=timezone.now() + timedelta(days=1),
            status='SCHEDULED'
        )
        self.client.force_authenticate(user=self.patient)

    def test_create_feedback(self):
        url = reverse('appointmentfeedback-list')
        data = {
            'appointment': self.appointment.id,
            'rating': 5,
            'comment': "Great service!"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AppointmentFeedback.objects.count(), 1)

    def test_list_feedback(self):
        AppointmentFeedback.objects.create(
            appointment=self.appointment,
            rating=5,
            comment="Excellent service!"
        )
        url = reverse('appointmentfeedback-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_doctor_average_rating(self):
        AppointmentFeedback.objects.create(
            appointment=self.appointment,
            rating=5,
            comment="Excellent service!"
        )
        url = reverse('appointmentfeedback-doctor-average-rating')
        response = self.client.get(url, {'doctor_id': self.doctor.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['average_rating'], 5.0)

