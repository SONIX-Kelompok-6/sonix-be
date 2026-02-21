from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # Penting untuk mereferensikan User model kita
from django.utils.text import slugify

# --- 1. Custom User Model (BARU) ---
class User(AbstractUser):    
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
    # --- 1. Identitas Utama ---
    shoe_id = models.CharField(max_length=50, primary_key=True)
    brand = models.CharField(max_length=100, blank=True, null=True) # Tambahkan Brand!
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    img_url = models.URLField(max_length=500, blank=True, null=True)
    
    # --- 2. Spesifikasi Fisik (Measurements) ---
    weight_lab_oz = models.FloatField(blank=True, null=True)
    drop_lab_mm = models.FloatField(blank=True, null=True)
    heel_lab_mm = models.FloatField(blank=True, null=True)
    forefoot_lab_mm = models.FloatField(blank=True, null=True)
    lug_dept_mm = models.FloatField(blank=True, null=True)

    # --- 3. Fitur Boolean (0 atau 1) ---
    lightweight = models.IntegerField(blank=True, null=True)
    rocker = models.IntegerField(blank=True, null=True)
    removable_insole = models.IntegerField(blank=True, null=True)
    waterproof = models.IntegerField(blank=True, null=True)
    water_repellent = models.IntegerField(blank=True, null=True)

    # --- 4. Pace / Kegunaan ---
    pace_daily_running = models.IntegerField(blank=True, null=True)
    pace_tempo = models.IntegerField(blank=True, null=True)
    pace_competition = models.IntegerField(blank=True, null=True)

    # --- 5. Terrain ---
    terrain_light = models.IntegerField(blank=True, null=True)
    terrain_moderate = models.IntegerField(blank=True, null=True)
    terrain_technical = models.IntegerField(blank=True, null=True)

    # --- 6. Arch Type ---
    arch_neutral = models.IntegerField(blank=True, null=True)
    arch_stability = models.IntegerField(blank=True, null=True)

    # --- 7. Plate ---
    plate_rock_plate = models.IntegerField(blank=True, null=True)
    plate_carbon_plate = models.IntegerField(blank=True, null=True)

    # --- 8. Lab Scores (Durability, Flexibility, etc) ---
    stiffness_scaled = models.IntegerField(blank=True, null=True)
    torsional_rigidity = models.IntegerField(blank=True, null=True)
    heel_stiff = models.IntegerField(blank=True, null=True)
    midsole_softness = models.IntegerField(blank=True, null=True)
    shock_absorption = models.IntegerField(blank=True, null=True)
    energy_return = models.IntegerField(blank=True, null=True)
    traction_scaled = models.IntegerField(blank=True, null=True)

    # --- 9. Durability Specifics ---
    toebox_durability = models.IntegerField(blank=True, null=True)
    heel_durability = models.IntegerField(blank=True, null=True)
    outsole_durability = models.IntegerField(blank=True, null=True)
    breathability_scaled = models.IntegerField(blank=True, null=True) # Kadang namanya breathability

    # --- 10. Fit & Width ---
    width_fit = models.IntegerField(blank=True, null=True)
    toebox_width = models.IntegerField(blank=True, null=True)

    # --- 11. Season ---
    season_summer = models.IntegerField(blank=True, null=True)
    season_winter = models.IntegerField(blank=True, null=True)
    season_all = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'shoes'
        managed = False  # Django tidak akan utak-atik tabel asli di Supabase

    def __str__(self):
        return f"{self.brand} - {self.name}"
    

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
    

# --- 5. Favorite (BARU) ---
class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    shoe_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites' 
        managed = False # Django tidak akan utak-atik tabel asli di Supabase
        unique_together = ('user', 'shoe_id') # Mencegah 1 user memfavoritkan sepatu yang sama berkali-kali

    def __str__(self):
        return f"User {self.user.username} favorited {self.shoe_id}"