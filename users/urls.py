from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RequestPasswordResetView, PasswordResetConfirmView, EmailVerificationView
from .viewsets import UserViewSet, DoctorProfileViewSet, PatientProfileViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'patients', PatientProfileViewSet)
router.register(r'doctors', DoctorProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('password-reset/', RequestPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('verify-email/<uidb64>/<token>/', EmailVerificationView.as_view(), name='verify-email'),
]
