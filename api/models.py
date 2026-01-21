from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # --- 1. BIOMEKANIKA (Data Fisik) ---
    WIDTH_CHOICES = [
        ('Narrow', 'Narrow'),
        ('Regular', 'Regular'),
        ('Wide', 'Wide'),
    ]
    foot_width = models.CharField(max_length=20, choices=WIDTH_CHOICES, default='Regular')
    
    ARCH_CHOICES = [
        ('Flat', 'Flat Foot (Low Arch)'),
        ('Normal', 'Normal Foot (Medium Arch)'),
        ('High', 'Hollow Foot (High Arch)'),
    ]
    arch_type = models.CharField(max_length=20, choices=ARCH_CHOICES, default='Normal')
    
    uses_orthotics = models.BooleanField(default=False, help_text="Do you use custom orthotics?")
    
    injury_history = models.JSONField(default=list, blank=True, help_text="List of past injuries")
    
    # --- 2. BODY STATS (Tambahan Wajib buat ML) ---
    # Berat badan ngaruh ke kebutuhan Cushioning
    weight_kg = models.IntegerField(help_text="Weight in KG", default=50) 
    
    # --- 3. PREFERENSI LARI (Context) ---
    TERRAIN_CHOICES = [
        ('Road', 'Road / Treadmill / Track (Aspal/Lintasan)'), 
        ('Trail', 'Trail (Tanah/Gunung/Off-road)'),
    ]
    preferred_terrain = models.CharField(max_length=20, choices=TERRAIN_CHOICES, default='Road')
    
    PURPOSE_CHOICES = [
        ('Daily', 'Daily Training (Lari Santai/Jogging)'),
        ('Speed', 'Speed/Tempo (Lari Cepat/Interval)'),
        ('Race', 'Racing (Lomba/Marathon)'),
        ('Recovery', 'Recovery (Jalan/Lari Ringan)'),
    ]
    running_purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='Daily')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"