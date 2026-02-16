from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Shoe, Review

# 1. Daftarkan Custom User dengan UserAdmin bawaan
# Ini supaya password ter-enkripsi dengan benar di dashboard admin
admin.site.register(User, UserAdmin)

# 2. Daftarkan UserProfile
admin.site.register(UserProfile)