from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 1. Berat Badan (Tetap Wajib)
    weight_kg = models.IntegerField()
    
    # 2. Foot Width
    FOOT_WIDTH_CHOICES = [
        ('Narrow', 'Narrow'),
        ('Regular', 'Regular'),
        ('Wide', 'Wide'),
    ]
    foot_width = models.CharField(max_length=10, choices=FOOT_WIDTH_CHOICES)
    
    # 3. Arch Type
    ARCH_TYPE_CHOICES = [
        ('Flat', 'Flat'),
        ('Normal', 'Normal'),
        ('High', 'High'),
    ]
    arch_type = models.CharField(max_length=10, choices=ARCH_TYPE_CHOICES)
    
    # 4. Orthotics (Baru: Yes/No)
    uses_orthotics = models.BooleanField(default=False)
    
    # 5. Injuries (Baru: List of strings)
    # Contoh isi: ["Knee Pain", "Toe Injury"]
    injury_history = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"