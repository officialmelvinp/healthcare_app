from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, AppointmentFeedbackViewSet

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'feedback', AppointmentFeedbackViewSet, basename='appointmentfeedback')

urlpatterns = [
    path('', include(router.urls)),
]

