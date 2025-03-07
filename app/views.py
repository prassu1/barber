from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from . serializers import UserRegistrationSerializer,UserLoginSerializer,UserLogoutSerializer,ChangePasswordSerializer,ForgotPasswordSerializer,ResetPasswordSerializer,UserProfileSerializer
from .serializers import ServiceSerializer, BookingSerializer, PaymentSerializer, AppointmentBookingSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, update_session_auth_hash
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
import logging, requests
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.contrib.auth import login
from app.models import CustomUser
from rest_framework import permissions
from .serializers import BookingSerializer
from .models import Service, Booking, Payment






logger = logging.getLogger(__name__)



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
        serializer = ForgotPasswordSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            reset_token = get_random_string(32)
            reset_url = f"http://127.0.0.1:8000/app/reset-password/{reset_token}"
            send_mail(
            "Password Reset",
            f"Click here to reset your password: {reset_url}",
            "bollaprasanna76gmail.com",
            [email],
            fail_silently=False
            )
            return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    serializer_class=ResetPasswordSerializer
    def post(self, request, *args, **kwargs):
        token = kwargs.get('token')  
        return Response({"message": "Password reset successful"}, status=200)
    def _is_token_expired(self, user):
        token_creation_time = user.reset_token_created_at  
        expiration_time = token_creation_time + timedelta(hours=1)
        if datetime.now() > expiration_time:
            return True
        return False

    
class GoogleLoginView(APIView):
    """Step 1: Redirect user to Google's OAuth 2.0 authorization URL"""
    def get(self, request):
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email",
            "access_type": "offline",
            "prompt": "consent",
        }
        authorization_url = f"{settings.GOOGLE_AUTHORIZATION_URL}?{requests.compat.urlencode(params)}"
        return Response(authorization_url)
    
class GoogleCallbackView(APIView):
    """Step 2: Handle Google's OAuth 2.0 callback and exchange code for tokens"""
    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return Response({"error": "Authorization code not provided"}, status=status.HTTP_400_BAD_REQUEST)
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(settings.GOOGLE_TOKEN_URL, data=data)
        if token_response.status_code != 200:
            logger.error("Failed to fetch access token: %s", token_response.text)
            return Response({"error": "Failed to fetch access token"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(settings.GOOGLE_USER_INFO_URL, headers=headers)
        if user_info_response.status_code != 200:
            logger.error("Failed to fetch user info: %s", user_info_response.text)
            return Response({"error": "Failed to fetch user info"}, status=status.HTTP_400_BAD_REQUEST)
        # google registration
        user_info = user_info_response.json()
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get('id')
        if not email or not google_id:
           return Response({"error": "Missing essential user data from Google"}, status=status.HTTP_400_BAD_REQUEST)
        username = name.replace(" " , " ")
        pswrd = f"{username}1@A"
        if not CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.create_user(
                email = email,
               username = username,
            )
            user.google_id = google_id
            user.is_active = True
            user.is_google_user = True
            user.set_password(pswrd)
            user.save()
            return Response({"message": "user successfully logged in or created"},status=status.HTTP_200_OK)
        return Response({"message": "User already exists"}, status=status.HTTP_200_OK)
       


class GuestLoginView(APIView):
    def get(self, request, *args, **kwargs):
        username = "guest_user"
        user= CustomUser.objects.filter(username=username).first()
        if not user:
            user = CustomUser.objects.create_user(username=username, email='guest@example.com')
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        request.session['username']=username
        return JsonResponse({
            'message': 'Guest user logged in successfully',
        })
    

class UserProfileEditView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request ):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save() 
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data  
            })
        return Response({
            'message': 'Error updating profile',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ServiceListView(APIView):    
    def post(self, request):
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppointmentBookingView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AppointmentBookingSerializer(data=request.data)
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        appointment_id = request.data.get("appointment_id")
        if not appointment_id:
            return Response({'message': 'Appointment ID is required for cancellation.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AppointmentBookingSerializer()
        response = serializer.cancel_appointment(appointment_id)
        if 'appointment_id' in response:
            return Response(response, status=status.HTTP_200_OK) 
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    





            

