from django.contrib.auth import authenticate
from rest_framework import serializers
from . models import CustomUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from barber import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.contrib.auth import get_user_model



USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')




class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    def validate(self, attrs):
        username=attrs.get('username','')
        password=attrs.get('password','')
        user=authenticate(username=username,password=password)
        if not user:
            raise serializers.ValidationError({'invalid credentials'})
        if not user.is_active:
            raise serializers.ValidationError({'This is not a user'})
        
        refresh = RefreshToken.for_user(user)
        tokens={
            'refresh' : str(refresh),
            'access': str(refresh.access_token),
            'username' : user.username
            }
        return tokens
 

class UserLogoutSerializer(serializers.ModelSerializer):
    refresh = serializers.CharField()
    class Meta:
        model = CustomUser
        fields = ['refresh']
        
        default_error_messages = {
        'bad_token': 'The refresh token is invalid or has already been blacklisted.'
    }
    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs
    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
           raise serializers.ValidationError(self.error_messages['bad_token'])


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data
    

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Optional validation logic for email."""
        User = get_user_model()
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email not found.")
        return value
        