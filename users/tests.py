import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from .serializers import UserSerializer, PatientProfileSerializer, DoctorProfileSerializer
from .models import PatientProfile, DoctorProfile

User = get_user_model()

class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_patient)
        self.assertFalse(user.is_doctor)

    def test_create_patient(self):
        user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='patientpass123',
            is_patient=True
        )
        self.assertTrue(user.is_patient)
        self.assertFalse(user.is_doctor)
        self.assertTrue(hasattr(user, 'patient_profile'))

    def test_create_doctor(self):
        user = User.objects.create_user(
            username='doctor',
            email='doctor@example.com',
            password='doctorpass123',
            is_doctor=True
        )
        self.assertTrue(user.is_doctor)
        self.assertFalse(user.is_patient)
        self.assertTrue(hasattr(user, 'doctor_profile'))

    def test_user_str(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser')

class UserAPITests(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        self.register_url = reverse('user-register')
        self.google_signin_url = reverse('google_signin')
        self.set_role_url = reverse('set-role')

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_user_registration_password_mismatch(self):
        self.user_data['password_confirm'] = 'wrongpass123'
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_signin(self, mock_verify_token):
        mock_verify_token.return_value = {
            'email': 'googleuser@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'sub': '12345'
        }
        response = self.client.post(self.google_signin_url, {'token': 'fake_token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['role_selection_required'])

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_set_user_role(self, mock_verify_token):
        mock_verify_token.return_value = {
            'email': 'googleuser@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'sub': '12345'
        }
        response = self.client.post(self.set_role_url, {'token': 'fake_token', 'role': 'patient'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email='googleuser@example.com')
        self.assertTrue(user.is_patient)
        self.assertFalse(user.is_doctor)

class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_patient_profile_creation(self):
        patient_profile = PatientProfile.objects.create(
            user=self.user,
            date_of_birth='1990-01-01'
        )
        self.assertEqual(patient_profile.user, self.user)
        self.assertEqual(str(patient_profile.date_of_birth), '1990-01-01')

    def test_doctor_profile_creation(self):
        doctor_profile = DoctorProfile.objects.create(
            user=self.user,
            specialization='GP'
        )
        self.assertEqual(doctor_profile.user, self.user)
        self.assertEqual(doctor_profile.specialization, 'GP')

class SerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.serializer_data = {
            **self.user_data,
            'password_confirm': 'testpass123'
        }

    def test_user_serializer(self):
        serializer = UserSerializer(data=self.serializer_data)
        self.assertTrue(serializer.is_valid())

    def test_patient_profile_serializer(self):
        user = User.objects.create_user(**self.user_data)
        profile_data = {
            'user': user.id,
            'date_of_birth': '1990-01-01'
        }
        serializer = PatientProfileSerializer(data=profile_data)
        self.assertTrue(serializer.is_valid())

    def test_doctor_profile_serializer(self):
        user = User.objects.create_user(**self.user_data)
        profile_data = {
            'user': user.id,
            'specialization': 'GP',
            'availability': True
        }
        serializer = DoctorProfileSerializer(data=profile_data)
        self.assertTrue(serializer.is_valid())

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from .models import PatientProfile, DoctorProfile
from .serializers import UserSerializer, PatientProfileSerializer, DoctorProfileSerializer
import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

# ... (keep other test classes unchanged)

class ViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_patient=True
        )
        self.client.force_authenticate(user=self.user)

    def create_test_image(self):
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file

    def test_patient_profile_viewset_update(self):
        url = reverse('patientprofile-detail', kwargs={'pk': self.user.patient_profile.pk})
        image = self.create_test_image()
        data = {
            'date_of_birth': '1990-01-01',
            'image': SimpleUploadedFile(image.name, image.getvalue(), content_type='image/png')
        }
        
        response = self.client.patch(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Expected 200, got {response.status_code}. Response data: {response.data}")
        
        profile = PatientProfile.objects.get(user=self.user)
        self.assertEqual(str(profile.date_of_birth), '1990-01-01')
        self.assertIsNotNone(profile.image)

    def test_patient_profile_viewset_create_fails(self):
        url = reverse('patientprofile-list')
        data = {'date_of_birth': '1990-01-01'}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PatientProfile.objects.count(), 1)  # Count should not increase


