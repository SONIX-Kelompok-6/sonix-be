from django.urls import path
from .views import register_user, login_user, manage_profile

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('profile/', manage_profile, name='user-profile'),
]