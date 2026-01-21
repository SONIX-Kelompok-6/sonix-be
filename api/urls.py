from django.urls import path
from .views import register_user, login_user, create_profile

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('profile/create/', create_profile, name='create-profile'),
]