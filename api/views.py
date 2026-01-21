from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer

@api_view(['POST'])
def register_user(request):
    # 1. Ambil data yang dikirim React
    serializer = UserSerializer(data=request.data)
    
    # 2. Cek apakah datanya valid? (Format email benar? Belum terdaftar?)
    if serializer.is_valid():
        serializer.save() # Simpan ke Database
        return Response({'message': 'User registered successfully!'}, status=status.HTTP_201_CREATED)
    
    # 3. Kalau error, balikin errornya ke React
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    # Validasi input kosong
    if not email or not password:
        return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)

    # Cek ke database
    # Perhatikan: Kita pakai parameter 'username=email' karena di register tadi
    # kita menyimpan email ke dalam kolom username.
    user = authenticate(username=email, password=password)

    if user is not None:
        # Login Sukses!
        # Nanti kita bisa upgrade pakai Token, tapi sekarang kita return data user dulu.
        serializer = UserSerializer(user)
        return Response({
            'message': 'Login successful!',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    else:
        # Login Gagal
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)