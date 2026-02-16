from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token 
from django.contrib.auth.models import update_last_login # PENTING: Untuk update jam login
from django.contrib.auth import authenticate
from .supabase_client import supabase
# Import model User custom kita dan model lainnya
from .models import User, UserProfile, Shoe, Review 
from .serializers import UserProfileSerializer, ShoeSerializer, UserDetailSerializer       

# ============================================================================
# BAGIAN A: AUTHENTICATION (REGISTER, LOGIN, OTP)
# ============================================================================

# --- 1. REGISTER (Minta OTP ke Supabase) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Fungsi ini cuma buat memicu pengiriman OTP ke email via Supabase.
    Data user BELUM disimpan ke database Django di sini.
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    # A. Validasi Input Dasar
    if not username or not email or not password:
        return Response({'error': 'Username, email, dan password wajib diisi.'}, status=400)
        
    # B. Cek apakah Username ATAU Email sudah ada di Django (PENTING!)
    # Kita cek dulu di DB kita biar gak bentrok nanti pas verify
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username ini sudah terpakai.'}, status=400)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email ini sudah terdaftar.'}, status=400)

    try:
        # C. Minta Supabase kirim OTP (Sign Up)
        res = supabase.auth.sign_up({
            "email": email,
            "password": password, 
        })

        # Cek jika email sudah terdaftar di sistem OTP Supabase tapi belum verified
        if res.user and getattr(res.user, 'identities', []) == []:
             return Response({'error': 'Email ini sudah terdaftar di sistem OTP.'}, status=400)

        return Response({'message': 'Kode OTP telah dikirim ke email!'}, status=201)

    except Exception as e:
        return Response({'error': str(e)}, status=400)


# --- 2. VERIFY OTP (Simpan User ke Django) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Fungsi ini memverifikasi OTP. Kalau benar, BARU user disimpan ke Database Django.
    """
    # FIX: Ambil username dari request (kemarin error disini karena lupa diambil)
    username = request.data.get('username') 
    email = request.data.get('email')
    token = request.data.get('otp')      
    password = request.data.get('password') 

    if not username or not email or not token or not password:
        return Response({'error': 'Data tidak lengkap (username/email/otp/password).'}, status=400)

    try:
        # A. Verifikasi OTP ke Supabase
        res = supabase.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "signup"
        })

        # B. Validasi Terakhir (Takutnya username diambil orang lain pas lagi nunggu OTP)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username sudah diambil orang lain.'}, status=400)

        # C. SIMPAN USER KE DATABASE DJANGO (FINAL)
        if not User.objects.filter(email=email).exists():
            # create_user otomatis mengenkripsi password (hashing)
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            
            # Opsional: Update last_login biar data di DB rapi
            update_last_login(None, user)
            
            return Response({'message': 'Verifikasi berhasil! Akun telah dibuat.'}, status=201)
        else:
            return Response({'error': 'User sudah ada di database.'}, status=400)

    except Exception as e:
        return Response({'error': 'Kode OTP salah atau sudah kadaluarsa.'}, status=400)


# --- 3. LOGIN (Login & Dapat Token) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login menggunakan Username ATAU Email.
    """
    # Bisa terima 'username' atau 'identifier' dari frontend
    input_ident = request.data.get('username') or request.data.get('identifier')
    password = request.data.get('password')

    if not input_ident or not password:  
        return Response({'error': 'Mohon isi username/email dan password.'}, status=400)

    # A. Logika Cek Email vs Username
    # Kita harus cari tahu 'username' aslinya apa buat dikasih ke fungsi authenticate Django
    username_to_auth = input_ident
    if '@' in input_ident:
        try:
            user_obj = User.objects.get(email=input_ident)
            username_to_auth = user_obj.username
        except User.DoesNotExist:
            pass # Biarkan lanjut biar ditolak di bawah (keamanan)
    
    # B. Autentikasi User
    user = authenticate(username=username_to_auth, password=password)

    if user is not None:
        if not user.is_active:
             return Response({'error': 'Akun ini sedang dinonaktifkan.'}, status=401)

        # FIX: Update kolom last_login di Supabase (biar gak Null)
        update_last_login(None, user)

        # C. Generate Token Login
        token, created = Token.objects.get_or_create(user=user)
        has_profile = hasattr(user, 'profile')

        return Response({
            'message': 'Login berhasil!',
            'token': token.key, 
            'email': user.email, 
            'username': user.username,
            'user_id': user.id, # Sekarang ini isinya ANGKA (1, 2, 3...)
            'has_profile': has_profile
        }, status=200)

    else:
        return Response({'error': 'Username/Email atau Password salah.'}, status=401)


# ============================================================================
# BAGIAN B: USER PROFILE
# ============================================================================

# --- 4. MANAGE PROFILE (Get, Create, Update) ---
@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_profile(request):
    user = request.user 

    # A. GET: Ambil data profile lengkap
    if request.method == 'GET':
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)

    # B. POST: Bikin profile baru (biasanya pas onboarding)
    elif request.method == 'POST':
        if hasattr(user, 'profile'):
            return Response({'error': 'Profile sudah ada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            full_data = UserDetailSerializer(user).data
            return Response(full_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # C. PATCH: Update sebagian data profile
    elif request.method == 'PATCH':
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile belum dibuat.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            full_data = UserDetailSerializer(user).data
            return Response(full_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# BAGIAN C: FITUR TAMBAHAN (Resend OTP, Forgot Password, Logout)
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    email = request.data.get('email')
    try:
        supabase.auth.resend({"type": "signup", "email": email})
        return Response({'message': 'OTP berhasil dikirim ulang!'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    if not email: return Response({'error': 'Email wajib diisi.'}, status=400)
    try:
        # Arahkan ke halaman frontend React kamu buat reset
        redirect_url = 'http://localhost:5173/update-password'
        supabase.auth.reset_password_email(email, options={'redirect_to': redirect_url})
        return Response({'message': 'Link reset password telah dikirim ke email.'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    access_token = request.data.get('access_token')
    new_password = request.data.get('new_password')
    if not access_token or not new_password:
        return Response({'error': 'Token dan password baru wajib diisi.'}, status=400)
    try:
        # 1. Update di Supabase (Sistem Auth)
        supabase.auth.set_session(access_token, request.data.get('refresh_token', '')) 
        attributes = {"password": new_password}
        res = supabase.auth.update_user(attributes)
        
        # 2. Sinkronisasi ke Database Django (Penting!)
        try:
            django_user = User.objects.get(email=res.user.email)
            django_user.set_password(new_password)
            django_user.save()
        except User.DoesNotExist:
            pass
        return Response({'message': 'Password berhasil diubah.'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        # Hapus token dari database biar gak bisa dipake lagi
        request.user.auth_token.delete()
        return Response({'message': 'Logout berhasil!'}, status=200)
    except Exception:
        return Response({'error': 'Gagal logout.'}, status=500)


# ============================================================================
# BAGIAN D: FITUR SEPATU (Search, Detail, Rating, Review)
# ============================================================================

# --- 1. SEARCH SHOES (Include Rating & Favorite Status) ---
@api_view(['GET'])
@permission_classes([AllowAny])
def search_shoes(request):
    query = request.GET.get('q', '')
    if not query: return Response([])
    try:
        # A. Cari di Supabase
        res = supabase.table('shoes').select('*').or_(f"name.ilike.%{query}%,brand.ilike.%{query}%").execute()
        shoes_data = res.data
        
        # B. Cek Favorit User (Kalau login)
        user_favorites = []
        if request.user.is_authenticated:
            try:
                # user.id sekarang adalah INTEGER (misal: 1, 2, 5)
                fav_res = supabase.table('favorites').select('shoe_id').eq('user_id', request.user.id).execute()
                user_favorites = [item['shoe_id'] for item in fav_res.data]
            except Exception: pass

        final_results = []
        for shoe in shoes_data:
            s_id = shoe.get('shoe_id')
            
            # C. Hitung Rating Rata-rata
            try:
                rev_res = supabase.table('reviews').select('rating').eq('shoe_id', s_id).execute()
                avg_rating = round(sum(r['rating'] for r in rev_res.data) / len(rev_res.data), 1) if rev_res.data else 0
            except: avg_rating = 0

            final_results.append({
                'id': shoe.get('id'), # ID unik sepatu
                'shoe_id': s_id,      # ID string sepatu (misal 'nike-pegasus')
                'name': shoe.get('name'),
                'brand': shoe.get('brand'),
                'img_url': shoe.get('img_url'),
                'slug': shoe.get('slug'),
                'rating': avg_rating,
                'isFavorite': s_id in user_favorites # True/False
            })
        return Response(final_results, status=200)
    except Exception as e:
        return Response({'error': 'Gagal mencari sepatu.'}, status=500)

# --- 2. GET SHOE DETAIL (Lengkap dengan Review) ---
@api_view(['GET'])
@permission_classes([AllowAny]) 
def get_shoe_detail(request, slug):
    try:
        # A. Ambil Data Sepatu dari Django
        shoe = Shoe.objects.get(slug=slug)
        serializer = ShoeSerializer(shoe)
        response_data = serializer.data
        
        # Tambahan field manual
        response_data['mainImage'] = shoe.img_url
        response_data['model'] = shoe.name
        
        # B. Cek Status Favorit
        response_data['isFavorite'] = False 
        if request.user.is_authenticated:
            try:
                cek_fav = supabase.table('favorites').select('*').eq('user_id', request.user.id).eq('shoe_id', shoe.shoe_id).execute()
                if len(cek_fav.data) > 0: response_data['isFavorite'] = True
            except: pass
        
        # C. Ambil Reviews dari Supabase & Map ke Username
        try:
            reviews_db = supabase.table('reviews').select('*').eq('shoe_id', shoe.shoe_id).order('created_at', desc=True).execute()
            formatted_reviews = []
            total_rating = 0
            
            for rv in reviews_db.data:
                user_id_reviewer = rv.get('user_id') # Ini Angka (misal: 5)
                try:
                    # Cari username di Django berdasarkan ID Integer
                    user_obj = User.objects.get(id=user_id_reviewer) 
                    display_name = user_obj.username
                except User.DoesNotExist:
                    display_name = f"User {user_id_reviewer}"
                
                total_rating += rv.get('rating', 0)
                formatted_reviews.append({
                    'id': rv.get('id'),
                    'user': display_name, # Username asli
                    'avatar': f"https://api.dicebear.com/7.x/avataaars/svg?seed={display_name}", 
                    'date': rv.get('created_at', '')[:10],
                    'text': rv.get('review_text', ''),
                    'rating': rv.get('rating', 0)
                })
            
            response_data['reviews'] = formatted_reviews
            response_data['rating'] = round(total_rating / len(reviews_db.data), 1) if reviews_db.data else 0
        except: 
            response_data['reviews'] = []
            response_data['rating'] = 0

        return Response(response_data, status=200)
    except Shoe.DoesNotExist:
        return Response({'error': 'Sepatu tidak ditemukan.'}, status=404)


# ============================================================================
# BAGIAN E: INTERAKSI USER (Favorite, Add Review)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request):
    user_id = request.user.id # Ambil ID Integer user
    shoe_id = request.data.get('shoe_id')
    if not shoe_id: return Response({'error': 'shoe_id wajib diisi.'}, status=400)

    try:
        # Cek apakah sudah ada di favorit
        cek_fav = supabase.table('favorites').select('*').eq('user_id', user_id).eq('shoe_id', shoe_id).execute()
        
        if len(cek_fav.data) > 0:
            # Kalau ada, HAPUS
            supabase.table('favorites').delete().eq('user_id', user_id).eq('shoe_id', shoe_id).execute()
            return Response({'message': 'Dihapus dari favorit', 'is_favorite': False}, status=200)
        else:
            # Kalau tidak ada, TAMBAH
            supabase.table('favorites').insert({'user_id': user_id, 'shoe_id': shoe_id}).execute()
            return Response({'message': 'Ditambahkan ke favorit', 'is_favorite': True}, status=201)
    except Exception:
        return Response({'error': 'Gagal update database.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_favorites(request):
    user_id = request.user.id
    try:
        # Ambil list ID sepatu favorit user
        fav_res = supabase.table('favorites').select('shoe_id').eq('user_id', user_id).execute()
        shoe_ids = [item['shoe_id'] for item in fav_res.data]
        
        if not shoe_ids: return Response([], status=200)
        
        # Ambil detail sepatunya
        shoes_res = supabase.table('shoes').select('*').in_('shoe_id', shoe_ids).execute()
        return Response(shoes_res.data, status=200)
    except Exception:
        return Response({'error': 'Gagal mengambil data favorit.'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_review(request):
    user_id = request.user.id
    shoe_id = request.data.get('shoe_id')
    rating = request.data.get('rating')
    text = request.data.get('text')

    if not shoe_id or not rating or not text:
        return Response({'error': 'Data review tidak lengkap.'}, status=400)
    try:
        # Simpan review ke Supabase
        supabase.table('reviews').insert({
            'shoe_id': shoe_id,
            'user_id': user_id, # Integer
            'rating': int(rating),
            'review_text': text
        }).execute()
        return Response({'message': 'Review berhasil ditambahkan!'}, status=201)
    except Exception:
        return Response({'error': 'Gagal menyimpan review.'}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny]) 
def get_all_shoes(request):
    try:
        response = supabase.table('shoes').select('*').execute()
        return Response(response.data if response.data else [], status=200)
    except Exception:
        return Response({'error': 'Gagal mengambil data sepatu.'}, status=500)