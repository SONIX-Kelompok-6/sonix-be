from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token # Import Token
from .serializers import UserSerializer, UserProfileSerializer
from .models import UserProfile # Import Model Profile

# --- 1. REGISTER (Tidak Berubah) ---
@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User registered successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- 2. LOGIN (DI-UPDATE) ---
@api_view(['POST'])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=email, password=password)

    if user is not None:
        # A. Bikin/Ambil Token (Tiket Masuk)
        token, _ = Token.objects.get_or_create(user=user)

        # B. Cek apakah user sudah punya profile?
        # Kita pakai try-except karena kalau belum punya, user.profile akan error
        try:
            profile = user.profile
            has_profile = True
        except UserProfile.DoesNotExist:
            has_profile = False

        # C. Kirim response lengkap (Token + Status Profile)
        return Response({
            'message': 'Login successful!',
            'token': token.key,        # <--- KUNCI UTAMA
            'email': user.email,
            'has_profile': has_profile # <--- SINYAL BUAT REDIRECT
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

# --- 3. CREATE PROFILE (BARU) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated]) # <--- GEMBOK: Cuma user login yg bisa akses
def create_profile(request):
    user = request.user # User didapat otomatis dari Token yang dikirim React
    
    # Cek apakah user ini sudah punya profile? (Biar gak dobel)
    if hasattr(user, 'profile'):
        return Response({'error': 'Profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validasi & Simpan
    serializer = UserProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=user) # Tempelkan profile ke user yang login
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)