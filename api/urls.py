from django.urls import path
from . import views
# from .views import register_user, verify_otp, login_user, manage_profile

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('verify-otp/', views.verify_otp, name='verify-otp'), 
    path('login/', views.login_user, name='login'),
    path('profile/', views.manage_profile, name='user-profile'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password_confirm, name='reset_password_confirm'),
    path('logout/', views.logout_user, name='logout'),
    path('shoes/search/', views.search_shoes, name='search_shoes'),
    path('favorites/toggle/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.get_user_favorites, name='get_user_favorites'),
    path('shoes/<slug:slug>/', views.get_shoe_detail, name='shoe-detail'),
    path('add-review/', views.add_review, name='add_review'),
    path('shoes/', views.get_all_shoes, name='get_all_shoes'),
]