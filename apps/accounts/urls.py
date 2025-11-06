from django.urls import path
from .views import (
    LoginView, RefreshTokenView, LogoutView, MeView, AccessRolesView,
    UpdateProfileView, ChangePasswordView
)

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('me/update/', UpdateProfileView.as_view(), name='update_profile'),
    path('me/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('roles/', AccessRolesView.as_view(), name='roles'),
]

