from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
import os

@deconstructible
class GenerateProfileImagePath:
    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        if hasattr(instance, 'user'):
            identifier = instance.user.id
        else:
            identifier = instance.id
        path = f'accounts/{identifier}/images/'
        name = f'profile_image.{ext}'
        return os.path.join(path, name)

user_profile_image_path = GenerateProfileImagePath()

class User(AbstractUser):
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

    def clean(self):
        if self.is_patient and self.is_doctor:
            raise ValidationError("A user cannot be both a patient and a doctor.")
        
    def save(self, *args, **kwargs):
        self.clean()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            if self.is_patient:
                PatientProfile.objects.get_or_create(user=self)
            elif self.is_doctor:
                DoctorProfile.objects.get_or_create(user=self)

    def __str__(self):
        return self.username

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    image = models.ImageField(upload_to=user_profile_image_path, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Patient Profile: {self.user.username}"

class DoctorProfile(models.Model):
    SPECIALIZATION_CHOICES = [
        ('GP', 'General Practitioner'),
        ('CARD', 'Cardiologist'),
        ('DERM', 'Dermatologist'),
        ('ORTH', 'Orthopedic'),
        ('NEUR', 'Neurologist'),
        ('DENT', 'Dental'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    image = models.ImageField(upload_to=user_profile_image_path, null=True, blank=True)
    specialization = models.CharField(max_length=5, choices=SPECIALIZATION_CHOICES)
    availability = models.BooleanField(default=True)

    def __str__(self):
        return f"Doctor Profile: {self.user.username} - {self.get_specialization_display()}"

