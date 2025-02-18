from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from . serializers import UserRegistrationSerializer,UserLoginSerializer,UserLogoutSerializer,ChangePasswordSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.conf import settings

# Create your views here.

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserLoginView(generics.GenericAPIView):
    serializer_class=UserLoginSerializer
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
           return Response(serializer.validated_data, status=status.HTTP_200_OK) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]  
    def post(self, request):
        serializer = UserLogoutSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_200_OK) 
        return Response(serializer.errors, status=status.HTTP_204_NO_CONTENT)

    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated] 
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            user = request.user
            
            if not user.check_password(old_password):
                return Response({"old_password": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return Response({"message": "Password has been successfully updated."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        # uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Send reset password email (you can customize the email body)
        reset_url = f'http://localhost:8000/app/reset-password/{token}/'
        send_mail(
            'Password Reset Request',
            f'Click here to reset your password: {reset_url}',
            'setting.EMAIL_HOST_USER',
            [email],
            fail_silently=False,
        )

        return Response({"message": "Password reset link has been sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)