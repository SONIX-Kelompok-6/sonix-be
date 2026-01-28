from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token # Import Token
from .serializers import UserSerializer, UserProfileSerializer
from .models import UserProfile # Import Model Profile

# --- 1. REGISTER (Tidak Berubah) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User registered successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- 2. LOGIN (DI-UPDATE) ---
@api_view(['POST'])
@permission_classes([AllowAny])
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

# --- 3. USER PROFILE ---
@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_profile(request):
    user = request.user

    # A. GET: Ambil Data Profile (Buat Home/Dashboard nanti)
    if request.method == 'GET':
        try:
            profile = user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    # B. POST: Bikin Profile Baru (Buat CreateProfile.jsx)
    elif request.method == 'POST':
        if hasattr(user, 'profile'):
            return Response({'error': 'Profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # C. PATCH: Update Profile (Opsional, buat fitur edit nanti)
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