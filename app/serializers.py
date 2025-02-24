from django.contrib.auth import authenticate
from rest_framework import serializers
from . models import CustomUser 
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from barber import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Booking,Service
from decimal import Decimal




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
        print(value)
        User = get_user_model()
        print(User)
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email not found.")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

class UserProfileSerializer(serializers.ModelSerializer):
   class Meta:
        model = CustomUser  
        fields = ['username', 'email'] 
    
    

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']


class BookingSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())  
    class Meta:
        model = Booking
        fields = ['id', 'service', 'frequency', 'duration', 'total_cost']
    
    def create(self, validated_data):
        service = validated_data.get('service')  
        frequency = validated_data['frequency']
        duration = validated_data['duration']
        total_cost = self.calculate_total_cost(service, frequency, duration)
        
        booking = Booking.objects.create(
            service=service,
            frequency=frequency,
            duration=duration,
            total_cost=total_cost
        )
        return booking

    def calculate_total_cost(self, service, frequency, duration):
        discount = Decimal('0.10') if duration >= 3 else Decimal('0.00')  
        if frequency == 'weekly':
            total_sessions = duration * 4  
        elif frequency == 'bi-weekly':
            total_sessions = duration * 2  
        elif frequency == 'monthly':
            total_sessions = duration 
        
        total_cost = Decimal(service.price) * Decimal(total_sessions)  
        total_cost *= (Decimal('1.00') - discount)  
        return total_cost



    
    
            
        

