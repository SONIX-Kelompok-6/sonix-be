from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 1. Berat Badan (Tetap Wajib)
    # weight_kg = models.IntegerField()
    
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
    # injury_history = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Shoe(models.Model):
    shoe_id = models.CharField(max_length=50, primary_key=True)
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=200) # Cth: "Nike Winflo 10"
    slug = models.SlugField(unique=True, blank=True, null=True) # Cth: "nike-winflo-10"
    description = models.TextField(blank=True, null=True)
    weight_lab_oz = models.FloatField(blank=True, null=True)
    # rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    img_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        # 1. Kasih tau nama tabel asli kamu di Supabase (misal namanya 'shoes')
        db_table = 'shoes' 
        
        # 2. Kasih tau Django untuk TIDAK membuat ulang tabel ini
        managed = False 

    def __str__(self):
        return f"{self.brand} {self.name}"
    
class Review(models.Model):
    # Nama kolom harus sama persis dengan yang di Supabase ya!
    shoe_id = models.CharField(max_length=50) 
    user_id = models.IntegerField()
    rating = models.IntegerField(default=0)
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        managed = False 

    def __str__(self):
        return f"Review by User {self.user_id} on Shoe {self.shoe_id}"