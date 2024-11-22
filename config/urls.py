from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import UserRegistrationView, LogoutView, GoogleSignInView, google_auth_callback, SetUserRoleView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/google-signin/', GoogleSignInView.as_view(), name='google_signin'),
    path('api/set-role/', SetUserRoleView.as_view(), name='set-role'),
    path('api/auth/google/callback/', google_auth_callback, name='google_callback'),

    # Include allauth URLs
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


