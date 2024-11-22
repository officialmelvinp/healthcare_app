
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Appointment
from django.utils import timezone

@receiver(post_save, sender=Appointment)
def appointment_created_or_updated(sender, instance, created, **kwargs):
    if instance.patient and instance.patient.email:
        subject = 'New Appointment Scheduled' if created else 'Appointment Updated'
        date_time_str = instance.date_time.strftime('%Y-%m-%d at %H:%M') if isinstance(instance.date_time, timezone.datetime) else str(instance.date_time)
        message = (
            f"{'An appointment has been scheduled' if created else 'Your appointment has been updated'} "
            f"with Dr. {instance.doctor.username} on {date_time_str}."
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.patient.email],
            fail_silently=False,
        )
        print(f"Appointment {'created' if created else 'updated'}: {instance}")
    else:
        print(f"Appointment notification failed due to missing user or email: {instance}")

