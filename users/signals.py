from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PatientProfile, DoctorProfile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create or update a user's profile when a User instance is saved.
    """
    if created:
        if instance.is_patient and not hasattr(instance, 'patient_profile'):
            PatientProfile.objects.get_or_create(user=instance)
        elif instance.is_doctor and not hasattr(instance, 'doctor_profile'):
            DoctorProfile.objects.get_or_create(user=instance)

