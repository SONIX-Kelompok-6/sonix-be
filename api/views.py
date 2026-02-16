from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token 
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .supabase_client import supabase
from .models import UserProfile, Shoe
# 👇 UPDATE IMPORT: Pastikan UserDetailSerializer ada di sini
from .serializers import UserProfileSerializer, ShoeSerializer, UserDetailSerializer       

# --- A. REGISTER (Trigger OTP via Supabase) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    # 1. Validasi Input Dasar
    if not username or not email or not password:
        return Response({'error': 'All fields are required.'}, status=400)
        
    # 2. Cek apakah Username ATAU Email sudah ada di Django (PENTING!)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'This username is already taken.'}, status=400)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'This email is already registered.'}, status=400)

    try:
        # 3. Minta Supabase kirim OTP (Sign Up)
        # Kita tidak peduli user di Supabase Auth, kita cuma butuh OTP-nya.
        res = supabase.auth.sign_up({
            "email": email,
            "password": password, # Password ini cuma buat syarat Supabase, yg asli nanti di Django
        })

        # Cek response spesifik Supabase kalau user double
        if res.user and getattr(res.user, 'identities', []) == []:
             return Response({'error': 'This email is already registered in OTP system.'}, status=400)

        return Response({'message': 'OTP sent to email!'}, status=201)

    except Exception as e:
        # Tangkap error dari Supabase
        return Response({'error': str(e)}, status=400)


# --- B. VERIFY OTP (Validate & Save to Django) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    username = request.data.get('username')
    email = request.data.get('email')
    token = request.data.get('otp')      
    password = request.data.get('password') # Password dari Frontend

    if not username or not email or not token or not password:
        return Response({'error': 'Missing required fields.'}, status=400)

    try:
        # 1. Verifikasi OTP ke Supabase
        res = supabase.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "signup"
        })

        # 2. Validasi Terakhir Sebelum Simpan ke Django
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username was taken during verification.'}, status=400)

        # 3. SIMPAN USER KE DJANGO (The Real Database)
        # Fungsi create_user otomatis nge-hash password pakai PBKDF2 (Aman untuk Login nanti)
        if not User.objects.filter(email=email).exists():
            User.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            return Response({'message': 'Verification successful & User created!'}, status=201)
        else:
            return Response({'error': 'User with this email already exists in Database.'}, status=400)

    except Exception as e:
        return Response({'error': 'Invalid OTP code or expired.'}, status=400)


# --- C. LOGIN (Proxy Login) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    # 1. TANGKAP DATA (Support 'username' atau 'identifier' dari frontend)
    # Frontend kamu tadi ngirimnya key 'username', jadi kita ambil itu.
    input_ident = request.data.get('username') or request.data.get('identifier')
    password = request.data.get('password')

    if not input_ident or not password:  
        return Response({'error': 'Please provide both username/email and password.'}, status=400)

    # 2. LOGIKA CEK EMAIL vs USERNAME
    # Kita harus cari tahu 'username' aslinya apa buat dikasih ke fungsi authenticate
    username_to_auth = input_ident

    if '@' in input_ident:
        # Kalau user login pakai EMAIL, kita cari dulu username aslinya di DB
        try:
            user_obj = User.objects.get(email=input_ident)
            username_to_auth = user_obj.username
        except User.DoesNotExist:
            # Kalau email gak ketemu, biarin lanjut biar nanti ditolak sama authenticate (security practice)
            pass
    
    # 3. AUTENTIKASI PAKAI DJANGO (Bukan Supabase Client)
    # Fungsi ini otomatis ngecek password hash PBKDF2 punya Django
    user = authenticate(username=username_to_auth, password=password)

    if user is not None:
        # --- LOGIN SUKSES ---
        
        # Cek apakah user aktif
        if not user.is_active:
             return Response({'error': 'User account is disabled.'}, status=401)

        # Bikin/Ambil Token
        token, created = Token.objects.get_or_create(user=user)

        # Cek Profile
        has_profile = hasattr(user, 'profile')

        return Response({
            'message': 'Login successful!',
            'token': token.key, 
            'email': user.email, 
            'username': user.username,
            'has_profile': has_profile
        }, status=200)

    else:
        # --- LOGIN GAGAL ---
        return Response({'error': 'Invalid username/email or password.'}, status=401)


# --- D. MANAGE PROFILE (UPDATED) ---
# 👇 INI BAGIAN PENTING YANG DI-UPDATE AGAR USERNAME MUNCUL DI ACCOUNT
@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_profile(request):
    user = request.user 

    # 1. GET: Ambil Data User LENGKAP (Username + Profile)
    if request.method == 'GET':
        # Pakai UserDetailSerializer supaya dapat username & email
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)

    # 2. POST: Bikin Profile Baru
    elif request.method == 'POST':
        if hasattr(user, 'profile'):
            return Response({'error': 'Profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            # Return full data agar frontend langsung update state
            full_data = UserDetailSerializer(user).data
            return Response(full_data, status=status.HTTP_201_CREATED)
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
            # Return full data agar frontend langsung update state
            full_data = UserDetailSerializer(user).data
            return Response(full_data)
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
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful!'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Something went wrong during logout.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# --- I. SEARCH SHOES (SINKRON DENGAN FAVORITE & RATING) ---
@api_view(['GET'])
@permission_classes([AllowAny])
def search_shoes(request):
    query = request.GET.get('q', '')

    if not query:
        return Response([])

    try:
        # 1. Tarik data sepatu dari Supabase
        res = supabase.table('shoes').select('*').or_(f"name.ilike.%{query}%,brand.ilike.%{query}%").execute()
        shoes_data = res.data

        # 2. Ambil daftar favorit user (jika user sedang login)
        user_favorites = []
        if request.user.is_authenticated:
            try:
                fav_res = supabase.table('favorites').select('shoe_id').eq('user_id', request.user.id).execute()
                user_favorites = [item['shoe_id'] for item in fav_res.data]
            except Exception as e:
                print("Error fetch fav in search:", str(e))

        # 3. Gabungkan data: Tambahkan isFavorite dan Hitung Rating Rata-rata
        final_results = []
        for shoe in shoes_data:
            s_id = shoe.get('shoe_id')
            
            # Hitung Rating Rata-rata dari tabel reviews
            try:
                rev_res = supabase.table('reviews').select('rating').eq('shoe_id', s_id).execute()
                if rev_res.data:
                    avg_rating = sum(r['rating'] for r in rev_res.data) / len(rev_res.data)
                    avg_rating = round(avg_rating, 1)
                else:
                    avg_rating = 0
            except:
                avg_rating = 0

            final_results.append({
                'id': shoe.get('id'),
                'shoe_id': s_id,
                'name': shoe.get('name'),
                'brand': shoe.get('brand'),
                'img_url': shoe.get('img_url'),
                'slug': shoe.get('slug'),
                'rating': avg_rating,
                'isFavorite': s_id in user_favorites # TRUE jika ada di daftar favorit user
            })
        
        return Response(final_results, status=status.HTTP_200_OK)

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
@permission_classes([AllowAny]) 
def get_shoe_detail(request, slug):
    try:
        shoe = Shoe.objects.get(slug=slug)
        serializer = ShoeSerializer(shoe)
        
        response_data = serializer.data
        response_data['mainImage'] = shoe.img_url
        response_data['model'] = shoe.name
        
        # --- FIX: FAVORITE LOGIC AGAR TIDAK HILANG SAAT REFRESH ---
        response_data['isFavorite'] = False 
        
        # Kita cek apakah user sedang login
        if request.user.is_authenticated:
            try:
                # Cari di tabel favorites: apakah ada data dengan user_id DAN shoe_id ini?
                cek_fav = supabase.table('favorites') \
                    .select('*') \
                    .eq('user_id', request.user.id) \
                    .eq('shoe_id', shoe.shoe_id) \
                    .execute()
                
                # Jika datanya ketemu (panjangnya > 0), berarti statusnya True
                if len(cek_fav.data) > 0:
                    response_data['isFavorite'] = True
            except Exception as e:
                print(f"Gagal verifikasi status favorit: {str(e)}")
        
        response_data['explore'] = []
        
        # --- 2. LOGIC TO FETCH REVIEWS & CALCULATE AVERAGE RATING ---
        try:
            # Get all comments for this shoe from the reviews table
            reviews_db = supabase.table('reviews').select('*').eq('shoe_id', shoe.shoe_id).order('created_at', desc=True).execute()
            
            formatted_reviews = []
            total_rating = 0 # Variable to accumulate all ratings
            
            for rv in reviews_db.data:
                raw_date = rv.get('created_at', '')
                clean_date = raw_date[:10] if raw_date else "Just now"
                current_rating = rv.get('rating', 0)
                user_id = rv.get('user_id')

                # Fetch actual username/email from Django's User model
                try:
                    user_obj = User.objects.get(id=user_id)
                    # Use email prefix if available, otherwise fallback to username
                    display_name = user_obj.email.split('@')[0] if user_obj.email else user_obj.username
                except User.DoesNotExist:
                    display_name = f"User {user_id}"

                # Add to total rating for average calculation
                total_rating += current_rating

                formatted_reviews.append({
                    'id': rv.get('id'),
                    'user': display_name,
                    'avatar': f"https://api.dicebear.com/7.x/avataaars/svg?seed={display_name}", 
                    'date': clean_date,
                    'text': rv.get('review_text', ''),
                    'rating': current_rating
                })
                
            response_data['reviews'] = formatted_reviews
            
            # Calculate the average rating for the top UI
            if len(reviews_db.data) > 0:
                average = total_rating / len(reviews_db.data)
                response_data['rating'] = round(average, 1) # Rounds to 1 decimal point (e.g., 4.5)
            else:
                response_data['rating'] = 0
            
        except Exception as e:
            print("Failed to fetch reviews from Supabase:", str(e))
            response_data['reviews'] = []
            response_data['rating'] = 0 
        # -------------------------------------------------

        return Response(response_data, status=status.HTTP_200_OK)
    
    except Shoe.DoesNotExist:
        return Response({'error': 'Shoe not found'}, status=status.HTTP_404_NOT_FOUND)

# --- M. ADD REVIEW (User Menambahkan Review ke Sepatu) ---     
@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Wajib login buat komen
def add_review(request):
    user_id = request.user.id
    shoe_id = request.data.get('shoe_id')
    rating = request.data.get('rating')
    review_text = request.data.get('text')

    if not shoe_id or not rating or not review_text:
        return Response({'error': 'All data (shoe_id, rating, text) must be provided!'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Insert new review data into the reviews table in Supabase
        supabase.table('reviews').insert({
            'shoe_id': shoe_id,
            'user_id': user_id,
            'rating': int(rating),
            'review_text': review_text
        }).execute()

        return Response({'message': 'Review successfully added!'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Error add review:", str(e))
        return Response({'error': 'Failed to add review.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- N. GET ALL SHOES (Untuk Fitur Compare & Recommendation) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def get_all_shoes(request):
    try:
        # Kita select '*' agar semua kolom spesifikasi (weight, drop, arch, dll) terambil
        response = supabase.table('shoes').select('*').execute()
        
        if response.data:
            return Response(response.data, status=status.HTTP_200_OK)
        else:
            return Response([], status=status.HTTP_200_OK)

    except Exception as e:
        print("Error fetching all shoes for compare:", str(e))
        return Response(
            {'error': 'Gagal mengambil data sepatu dari server.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )