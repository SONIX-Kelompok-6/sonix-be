from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # Penting untuk mereferensikan User model kita
from django.utils.text import slugify

# --- 1. Custom User Model (BARU) ---
class User(AbstractUser):
    # ID tidak perlu ditulis, Django otomatis pakai AutoField (Angka 1, 2, 3...)
    
    # Hapus kolom nama depan & belakang (Biar database bersih)
    first_name = None
    last_name = None
    
    # Email jadi Wajib & Unik
    email = models.EmailField(unique=True)

    # Kolom password, is_staff, is_superuser sudah otomatis ada dari AbstractUser

    def __str__(self):
        return self.username

# --- 2. User Profile (UPDATED) ---
class UserProfile(models.Model):
    # Gunakan settings.AUTH_USER_MODEL agar mengarah ke model User di atas
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Field Profile lainnya tetap sama
    FOOT_WIDTH_CHOICES = [
        ('Narrow', 'Narrow'),
        ('Regular', 'Regular'),
        ('Wide', 'Wide'),
    ]
    foot_width = models.CharField(max_length=10, choices=FOOT_WIDTH_CHOICES)
    
    ARCH_TYPE_CHOICES = [
        ('Flat', 'Flat'),
        ('Normal', 'Normal'),
        ('High', 'High'),
    ]
    arch_type = models.CharField(max_length=10, choices=ARCH_TYPE_CHOICES)
    
    uses_orthotics = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# --- 3. Shoe (TETAP SAMA) ---
class Shoe(models.Model):
    shoe_id = models.CharField(max_length=50, primary_key=True)
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    weight_lab_oz = models.FloatField(blank=True, null=True)
    img_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'shoes'
        managed = False 

    def __str__(self):
        return f"{self.brand} {self.name}"

# --- 4. Review (TETAP SAMA) ---
class Review(models.Model):
    shoe_id = models.CharField(max_length=50) 
    # user_id integer cocok dengan ID user kita yang sekarang angka (1, 2, 3)
    user_id = models.IntegerField() 
    rating = models.IntegerField(default=0)
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        managed = False 

    def __str__(self):
        return f"Review by User {self.user_id} on Shoe {self.shoe_id}"