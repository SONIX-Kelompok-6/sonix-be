from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Shoe

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Kita pakai 'email' sebagai username juga biar simpel
        user = User.objects.create_user(
            username=validated_data['email'], 
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['foot_width', 'arch_type', 'uses_orthotics']

class UserDetailSerializer(serializers.ModelSerializer):
    # Kita masukkan profile ke dalam user
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'date_joined', 'profile']

class ShoeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shoe
        fields = '__all__'