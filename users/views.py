
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from .serializers import UserSerializer, serializers
from rest_framework_simplejwt.authentication import JWTAuthentication
import jwt
from .serializers import PasswordResetSerializer
from .serializers import UserProfileSerializer

User = get_user_model()
logger = logging.getLogger(__name__)

class ProfileSelectionSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['patient', 'doctor'])



class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_url = request.build_absolute_uri(
            reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
        )

        send_mail(
            'Email Verification',
            f'Click the link to verify your email: {verification_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        user.refresh_from_db()
        headers = self.get_success_headers(serializer.data)
        return Response({"message": "User created successfully. Please check your email to verify your account.", "data": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)





class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

            subject = 'Password Reset Request'
            message = f'Click the link to reset your password: {reset_url}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            logger.info(f"Attempting to send password reset email to {email}")
            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                logger.info(f"Password reset email sent successfully to {email}")
            except Exception as e:
                logger.error(f"Failed to send password reset email to {email}. Error: {str(e)}")
                return Response(
                    {"detail": "Failed to send password reset email. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.info(f"Password reset requested for non-existent email: {email}")

        return Response(
            {"detail": "If an account with this email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.data.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                return Response({"detail": "Password has been reset."}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)





class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.email_verified = True
            user.save()
            return Response({"detail": "Email has been verified successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, uidb64, token):
        return self.get(request, uidb64, token)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def google_auth_callback(request):
    if request.method == 'GET':
        code = request.GET.get('code')
        if code:
            logger.info(f"Received authorization code: {code[:10]}...")
            cache.set('google_auth_code', code, timeout=300)  # Store for 5 minutes
            return JsonResponse({'message': 'Authorization code received'})
        else:
            logger.warning("GET request received without authorization code")
            return JsonResponse({'error': 'No authorization code received'}, status=400)
    elif request.method == 'POST':
        code = cache.get('google_auth_code')
        if code:
            logger.info(f"Returning stored authorization code: {code[:10]}...")
            cache.delete('google_auth_code')
            return JsonResponse({'code': code})
        else:
            logger.warning("POST request received, but no authorization code found in cache")
            return JsonResponse({'error': 'No authorization code available'}, status=400)
    
    logger.error(f"Invalid request method: {request.method}")
    return JsonResponse({'error': 'Invalid request'}, status=400)


class GoogleSignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            userid = idinfo['sub']
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            user, created = User.objects.get_or_create(email=email)
            
            if created:
                user.username = email
                user.first_name = first_name
                user.last_name = last_name
                user.email_verified = True
                user.save()

            # Check if the user already has a role (patient or doctor)
            if not user.is_patient and not user.is_doctor:
                # If no role assigned, ask the user to select their role
                return Response({
                    'message': 'Please select a role: patient or doctor.',
                    'role_selection_required': True
                }, status=status.HTTP_200_OK)

            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.error(f"Token validation failed: {str(e)}")
            return Response({'error': f'Invalid token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"An error occurred during Google Sign In: {str(e)}")
            return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SetUserRoleView(APIView):
    permission_classes = [AllowAny]  # Temporarily allow any request for debugging

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        
        if not token:
            return Response({"detail": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)

            # Get user email from the verified token
            email = idinfo['email']

            # Fetch or create the user
            user, created = User.objects.get_or_create(email=email)
            
            # Check if a role is provided
            role = request.data.get('role')
            if not role or role not in ['patient', 'doctor']:
                return Response({"detail": "Valid role ('patient' or 'doctor') is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Assign the role to the user
            if role == 'patient':
                user.is_patient = True
                user.is_doctor = False
            else:
                user.is_doctor = True
                user.is_patient = False
            user.save()

            return Response({"detail": "Role updated successfully.", "role": role}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'error': f'Invalid token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)