from rest_framework import serializers
from django.contrib.auth import get_user_model # Cara aman ambil model User
from .models import UserProfile, Shoe

# Ambil model User yang aktif (Custom User kita)
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'], 
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['foot_width', 'arch_type', 'uses_orthotics']

class UserDetailSerializer(serializers.ModelSerializer):
    # Gabungkan data profile ke dalam detail user
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'profile']

class ShoeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shoe
        fields = '__all__'