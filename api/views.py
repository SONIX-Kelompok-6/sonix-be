from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token 
from django.contrib.auth.models import User
from .supabase_client import supabase
# Pastikan 2 baris ini ada (sesuaikan nama file jika beda)
from .models import UserProfile        
from .serializers import UserProfileSerializer 

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


# --- D. MANAGE PROFILE (INI YANG TADI HILANG) ---
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