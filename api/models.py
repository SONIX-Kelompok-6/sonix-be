from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

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


class Shoe(models.Model):
    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=200) # Cth: "Nike Winflo 10"
    slug = models.SlugField(unique=True, blank=True, null=True) # Cth: "nike-winflo-10"
    weight = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    image_url = models.URLField(max_length=500, blank=True, null=True)

    # Otomatis membuat slug saat data disimpan
    def save(self, *args, **kwargs):
        if not self.slug and self.model_name:
            self.slug = slugify(self.model_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} {self.model_name}"