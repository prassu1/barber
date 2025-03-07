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
from .models import Booking,Service,Payment
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from .models import AppointmentBooking
from django.core.mail import send_mail
 




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
        fields = ['id', 'service', 'frequency', 'duration', 'total_cost', 'start_datetime', 'total_paid']
    
    def create(self, validated_data):
        service = validated_data.get('service')  
        frequency = validated_data['frequency']
        duration = validated_data['duration']
        start_datetime = validated_data.get('start_datetime', timezone.now())
        total_cost = self.calculate_total_cost(service, frequency, duration)
        
        booking = Booking.objects.create(
            service=service,
            frequency=frequency,
            duration=duration,
            total_cost=total_cost,
            start_datetime=start_datetime,
            total_paid=Decimal('0.00')
        )
        return booking

    def calculate_total_cost(self, service, frequency, duration):
        total_sessions = 5 
        discount = Decimal('0.10') if duration == 3 and total_sessions == 5 else Decimal('0.00')
        if frequency == 'weekly':
            total_sessions = duration * 4 
            unit_price = service.price_per_week  
        elif frequency == 'bi-weekly':
            total_sessions = duration * 2
            unit_price = service.price_per_biweekly 
        elif frequency == 'monthly':
            total_sessions = duration 
            unit_price = service.price_per_month
        else:
            total_sessions = 0 
            unit_price = Decimal('0.00')
        
        total_cost = unit_price * total_sessions 
        total_cost *= (Decimal('1.00') - discount)  
        return total_cost
    

class PaymentSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    paid_amount = serializers.SerializerMethodField()
    due_amount = serializers.SerializerMethodField()
    remaining_paid_amount = serializers.SerializerMethodField()  
    total_paid = serializers.SerializerMethodField() 

    class Meta:
        model = Payment
        fields = ['id', 'booking', 'amount', 'payment_method', 'payment_status', 'payment_type', 'partial_amount', 'installment_plan', 'installment_number', 'paid_amount', 'due_amount', 'remaining_paid_amount' , 'paid_datetime', 'due_months', 'total_paid']
    
    def get_paid_amount(self, obj):
        total_paid = Payment.objects.filter(booking=obj.booking).aggregate(
            total_paid=Sum('amount')
        )['total_paid'] or Decimal('0.00')
        return total_paid 
        
    def get_due_amount(self, obj): 
        total_paid = self.get_paid_amount(obj)
        due_amount = obj.booking.total_cost - total_paid
        return max(Decimal('0.00'), due_amount)
        
    def get_remaining_paid_amount(self, obj):
        total_paid = self.get_paid_amount(obj)
        remaining_paid_amount = obj.booking.total_cost - total_paid
        return max(Decimal('0.00'), remaining_paid_amount)

    def get_total_paid(self, obj): 
        total_paid = Payment.objects.filter(booking=obj.booking).aggregate(
            total_paid=Sum('amount')
        )['total_paid'] or Decimal('0.00')
        return total_paid
    
    
    def create(self, validated_data):
        booking = validated_data['booking']
        amount = validated_data['amount']
        payment_method = validated_data['payment_method']
        payment_type = validated_data.get('payment_type', 'full').lower() 
        partial_amount = validated_data.get('deposit_amount', 0)
        installment_plan = validated_data.get('installment_plan', False)  
        due_months = validated_data.get('due_months', None)  
        total_paid = validated_data.get('total_paid', Decimal('0.00'))
        installment_number = None 
        
        if payment_type == 'full' :
            if booking.total_paid >= booking.total_cost:
                ({"amount": ["This booking has already been fully paid. No further full payments are allowed."]})
            if amount != booking.total_cost:
                raise serializers.ValidationError({"amount": ["Amount must match the total cost of the booking for full payment."]})
        
        elif payment_type == 'partial':
            if amount <= 0:
                raise serializers.ValidationError({"amount": ["Partial payment amount must be greater than 0."]})
            if booking.total_paid >= booking.total_cost:
                raise serializers.ValidationError({"amount": ["This booking has already been fully paid. No further partial payments are allowed."]})
            if booking.total_paid + amount > booking.total_cost:
                raise serializers.ValidationError({"amount": ["Partial payment exceeds the total cost of the booking."]})
        
        elif payment_type == 'installment' :
            if not installment_plan :
                raise serializers.ValidationError({"installment_plan": ["Installment plan must be enabled and the installment number specified."]})
            if due_months is None or due_months <= 0:
                raise serializers.ValidationError({"due_months": ["Due months must be specified and greater than 0."]})
            
            installment_amount = booking.total_cost / due_months
            if amount != installment_amount:
                raise serializers.ValidationError({"amount": [f"Installment amount must be {installment_amount} per month."]})
            
            previous_installments = Payment.objects.filter(
                booking=booking,
                payment_type='installment'
            ).count() 
            installment_number = previous_installments + 1
            
            if installment_number > due_months:
                raise serializers.ValidationError({"installment_number": [f"Installment number cannot exceed {due_months}. This booking only allows {due_months} installments."]})

            
        if payment_type == 'full' and amount == booking.total_cost:
            payment_status = 'Completed'
        else:
            payment_status = 'pending'

            payment_date = timezone.now()

        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            payment_method=payment_method,
            payment_status=payment_status,
            payment_type=payment_type,
            partial_amount=partial_amount,
            installment_plan=installment_plan,
            installment_number=installment_number, 
            due_months=due_months,
        )

        if payment_status == 'Completed' and payment_type == 'full':
            booking.total_cost = amount
            booking.save()

        if payment_type == 'installment': 
            installment_amount = booking.total_cost / due_months
            booking.total_paid += installment_amount
            booking.save()

        if payment_type == 'partial': 
            booking.total_paid += amount
            booking.save()

        payment.total_paid = self.get_total_paid(payment)  
        payment.paid_amount = self.get_paid_amount(payment)  
        payment.due_amount = self.get_due_amount(payment)  
        payment.remaining_paid_amount = self.get_remaining_paid_amount(payment)  
        payment.save()  
        return payment
    

class AppointmentBookingSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)  

    class Meta:
        model = AppointmentBooking
        fields = ['booking_id', 'appointment_date', 'payments','customer_email']  

    def create(self, validated_data):
        appointment = AppointmentBooking.objects.create(**validated_data)
        existing_payments = Payment.objects.filter(booking_id=appointment.booking_id)
        for payment in existing_payments:
            payment.appointment = appointment
            payment.save()  

        full_payment = any(payment.payment_status == 'Completed' and payment.due_amount == 0 for payment in existing_payments)
        
        if full_payment:
            appointment.status = 'confirmed'
            appointment.save()
            response = {
                'message': 'Appointment booked successfully with full payment.',
                'appointment_id': appointment.id,
                'status': appointment.status
            }
            self.send_confirmation_email(appointment)
            print('hi')
        else:
            appointment.status = 'pending'
            appointment.save()
            response = {
                'message': 'Appointment booked with pending payment.',
                'appointment_id': appointment.id,
                'status': appointment.status
            }

        return response

    def cancel_appointment(self, appointment_id):
        try:
            appointment = AppointmentBooking.objects.get(id=appointment_id)
            appointment.status = 'canceled'
            appointment.save()

            self.send_cancellation_email(appointment)

            return {
                'message': 'Appointment canceled successfully.',
                'appointment_id': appointment.id,
                'status': appointment.status
            }
        except AppointmentBooking.DoesNotExist:
            return {
                'message': 'Appointment not found.',
                'appointment_id': appointment_id
            }

    def send_confirmation_email(self, appointment):
        user_email = appointment.customer_email  
        subject = 'Your Appointment has been Confirmed'
        message = f"Dear {'user'},\n\n" \
                  f"Your appointment has been successfully booked and confirmed for {appointment.appointment_date}. " \
                  f"Thank you for making the full payment.\n\n" \
                  f"Best regards,\nYour Company Name"
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,  
            [user_email],              
            fail_silently=False
        )

    def send_cancellation_email(self, appointment):
        user_email = appointment.customer_email  
        subject = 'Your Appointment has been Canceled'
        message = f"Dear {'user'},\n\n" \
                  f"Your appointment scheduled for {appointment.appointment_date} has been canceled. " \
                  f"We are sorry for the inconvenience.\n\n" \
                  f"Best regards,\nYour Company Name"
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,  
            [user_email],              
            fail_silently=False
        ) 




    
    
    



    
        
        

    
    
            
        

