from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token 
from django.contrib.auth.models import User
from django.conf import settings
from .supabase_client import supabase
<<<<<<< HEAD
from .models import UserProfile,Shoe
from .serializers import UserProfileSerializer,ShoeSerializer         
=======

# Pastikan 2 baris ini ada 
from .models import UserProfile        
from .serializers import UserProfileSerializer 
>>>>>>> develop

# --- A. REGISTER (Trigger OTP) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        if res.user and getattr(res.user, 'identities', []) == []:
             return Response({'error': 'Email is already registered.'}, status=400)

        return Response({'message': 'OTP sent to email!'}, status=201)

    except Exception as e:
        print("ERROR SUPABASE:", str(e))
        return Response({'error': str(e)}, status=400)


# --- B. VERIFY OTP (Validate & Sync to Django) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    token = request.data.get('otp')      
    password = request.data.get('password') 

    try:
        res = supabase.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "signup"
        })

        if not User.objects.filter(username=email).exists():
            User.objects.create_user(username=email, email=email, password=password)
        
        return Response({'message': 'Verification successful & User saved to Django!'}, status=201)

    except Exception as e:
        return Response({'error': 'Invalid or expired OTP.'}, status=400)


# --- C. LOGIN (Proxy Login) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        # 1. Django Login ke Supabase (Cuma buat cek password benar/salah)
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # 2. Kalau password benar, cari user di database Django
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            user = User.objects.create_user(username=email, email=email, password=password)
        
        # 3. BIKIN TOKEN DJANGO (Kartu Member Resmi)
        token, created = Token.objects.get_or_create(user=user)

        # 4. Cek Profile
        has_profile = hasattr(user, 'profile')

        return Response({
            'message': 'Login successful!',
            'token': token.key, 
            'email': email,
            'has_profile': has_profile
        }, status=200)

    except Exception as e:
        return Response({'error': 'Invalid email or password.'}, status=401)


# --- D. MANAGE PROFILE ---
@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_profile(request):
    user = request.user 

    # 1. GET: Ambil Data Profile
    if request.method == 'GET':
        try:
            profile = user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    # 2. POST: Bikin Profile Baru
    elif request.method == 'POST':
        if hasattr(user, 'profile'):
            return Response({'error': 'Profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 3. PATCH: Update Profile
    elif request.method == 'PATCH':
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# --- E. RESEND OTP ---
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    email = request.data.get('email')
    try:
        supabase.auth.resend({
            "type": "signup",
            "email": email,
        })
        return Response({'message': 'OTP resent successfully!'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    
# --- F. FORGOT PASSWORD (Send Email Link) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email is required'}, status=400)

    try:
        # Arahkan ke URL Frontend React lokal kamu
        redirect_url = 'http://localhost:5173/update-password'
        
        supabase.auth.reset_password_email(email, options={
            'redirect_to': redirect_url
        })
        
        return Response({'message': 'Password reset link sent to your email.'})
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)


# --- G. RESET PASSWORD (Set New Password) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    # Endpoint ini dipanggil SETELAH user klik link di email
    # Frontend akan mengirimkan 'access_token' (dari URL) dan 'new_password'
    
    access_token = request.data.get('access_token')
    new_password = request.data.get('new_password')
    
    if not access_token or not new_password:
        return Response({'error': 'Token and new password are required'}, status=400)

    try:
        # 1. Update password di Supabase menggunakan token user
        # Kita butuh session user yg valid untuk update password
        # Supabase Python client update_user butuh session yg aktif
        
        # Set session manual pakai access_token dari URL
        supabase.auth.set_session(access_token, request.data.get('refresh_token', '')) 
        
        # 2. Update user
        attributes = {"password": new_password}
        res = supabase.auth.update_user(attributes)
        
        # 3. Sinkronisasi password ke database Django 
        # Ambil email dari user yg baru saja diupdate
        user_email = res.user.email
        try:
            django_user = User.objects.get(username=user_email)
            django_user.set_password(new_password)
            django_user.save()
        except User.DoesNotExist:
            pass # Kalau user ga ada di Django, skip aja

        return Response({'message': 'Password has been reset successfully.'})

    except Exception as e:
        return Response({'error': str(e)}, status=400)
    
# --- H. LOGOUT (Invalidate Token) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        # Hapus token user dari database Django
        # Ini bikin token yang disimpan di frontend jadi "sampah" (gak guna lagi)
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful!'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Something went wrong during logout.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# --- I. SEARCH SHOES (VIA SUPABASE API) ---
@api_view(['GET'])
@permission_classes([AllowAny])
def search_shoes(request):
    query = request.GET.get('q', '')

    if not query:
        return Response([])

    try:
        # Langsung nembak ke tabel 'shoes' di Supabase
        # Asumsi: nama kolomnya 'name' dan 'brand'. (Kalau beda, tinggal ganti kata name/brand di bawah ini)
        res = supabase.table('shoes').select('*').or_(f"name.ilike.%{query}%,brand.ilike.%{query}%").execute()
        
        # Datanya dari Supabase udah otomatis bentuk JSON, jadi bisa langsung dilempar ke React
        return Response(res.data, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error search Supabase:", str(e))
        return Response({'error': 'Gagal mencari sepatu'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# --- J. TOGGLE FAVORITE ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request):
    # Ambil ID user dari database Django (int4 sesuai tabel lu)
    user_id = request.user.id 
    shoe_id = request.data.get('shoe_id')

    if not shoe_id:
        return Response({'error': 'shoe_id wajib disertakan.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Cek di tabel favorites pakai user_id (bukan email)
        cek_fav = supabase.table('favorites').select('*').eq('user_id', user_id).eq('shoe_id', shoe_id).execute()

        if len(cek_fav.data) > 0:
            # 2a. Kalau ada, hapus
            supabase.table('favorites').delete().eq('user_id', user_id).eq('shoe_id', shoe_id).execute()
            return Response({
                'message': 'Berhasil dihapus dari favorit',
                'is_favorite': False
            }, status=status.HTTP_200_OK)
        else:
            # 2b. Kalau tidak ada, masukkan pakai user_id
            supabase.table('favorites').insert({
                'user_id': user_id, 
                'shoe_id': shoe_id
            }).execute()
            return Response({
                'message': 'Berhasil ditambahkan ke favorit',
                'is_favorite': True
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Error toggle favorite:", str(e))
        return Response({'error': 'Terjadi kesalahan pada database.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# --- K. GET ALL FAVORITES (Ambil Semua Sepatu Favorit User) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_favorites(request):
    user_id = request.user.id

    try:
        # 1. Ambil list ID sepatu yang di-favorit user ini
        fav_res = supabase.table('favorites').select('shoe_id').eq('user_id', user_id).execute()
        
        shoe_ids = [item['shoe_id'] for item in fav_res.data]

        if not shoe_ids:
            return Response([], status=status.HTTP_200_OK)

        # 2. Tarik detail sepatunya pakai filter .in_()
        shoes_res = supabase.table('shoes').select('*').in_('shoe_id', shoe_ids).execute()

        return Response(shoes_res.data, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error get favorites:", str(e))
        return Response({'error': 'Gagal mengambil daftar favorit'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# --- L. SHOE DETAIL (Ambil data sepatu berdasarkan slug) ---
@api_view(['GET'])
@permission_classes([AllowAny]) # Siapapun bisa lihat detail sepatu, tidak perlu login
def get_shoe_detail(request, slug):
    try:
        shoe = Shoe.objects.get(slug=slug)
        serializer = ShoeSerializer(shoe)
        
        # Karena di frontend kamu butuh data tambahan (explore, isFavorite, dll),
        # kita modifikasi sedikit bentuk response-nya
        response_data = serializer.data
        
        # Kita sesuaikan key-nya agar cocok dengan frontend yang sudah kita buat
        response_data['mainImage'] = shoe.image_url
        response_data['model'] = shoe.model_name
        response_data['isFavorite'] = False # Default false (nanti bisa diubah pakai logika User)
        
        # Dummy data untuk 'explore' dan 'reviews' (karena tabelnya belum ada)
        response_data['explore'] = []
        response_data['reviews'] = []

        return Response(response_data, status=status.HTTP_200_OK)
    
    except Shoe.DoesNotExist:
        return Response({'error': 'Sepatu tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)
