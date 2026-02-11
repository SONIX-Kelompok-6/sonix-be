from django.urls import path
from . import views
from .views import register_user, verify_otp, login_user, manage_profile

urlpatterns = [
    path('register/', register_user, name='register'),
    path('verify-otp/', verify_otp, name='verify-otp'), 
    path('login/', login_user, name='login'),
    path('profile/', manage_profile, name='user-profile'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password_confirm, name='reset_password_confirm'),
    path('logout/', views.logout_user, name='logout'),
    path('shoes/search/', views.search_shoes, name='search_shoes'),
]