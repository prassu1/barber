from django.urls import path
from .views import UserRegistrationView,UserLoginView,UserLogoutView,ChangePasswordView,ForgotPasswordView,ResetPasswordView
from .views import GoogleLoginView, GoogleCallbackView,GuestLoginView, UserProfileEditView,BookingCreateView,ServiceListView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/',UserLoginView.as_view(),name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:token>/',ResetPasswordView.as_view(), name='reset-password'),
    path("auth/google/login/", GoogleLoginView.as_view(), name="google-login"),
    path("auth/google/callback/", GoogleCallbackView.as_view(), name="google-callback"),
    path('guest-login/', GuestLoginView.as_view(), name='guest-login'),
    path('profile_edit/', UserProfileEditView.as_view(), name='profile_edit'),
    path('bookings/', BookingCreateView.as_view(), name='booking-create'), 
    path('services/',ServiceListView.as_view(),name='services')
]
