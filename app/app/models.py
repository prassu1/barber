from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from decimal import Decimal
import datetime


#custom user manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)
    
#custom user model
class CustomUser(AbstractBaseUser,PermissionsMixin):
    username = models.CharField(max_length=20,unique=True)
    email = models.EmailField(max_length=50)
    password = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser=models.BooleanField(default=False)
   
    
    USERNAME_FIELD = 'username'  
    REQUIRED_FIELDS = ['email']  

    objects = CustomUserManager()

    def __str__(self):
        return self.username



class Service(models.Model):
    name = models.CharField(max_length=225)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True) 
    # menu_item = models.ForeignKey(on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name
    
    
class Booking(models.Model):
    service = models.ForeignKey(Service, related_name="bookings", on_delete=models.CASCADE)
    frequency = models.CharField(max_length=255)
    duration = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    start_datetime = models.DateTimeField(default=timezone.now)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    

    
    frequency_choices = [
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ]
    frequency = models.CharField(max_length=10, choices=frequency_choices)
    
    duration_choices = [
        (3, '3 Months'),
        (6, '6 Months'),
    ]
    duration = models.IntegerField(choices=duration_choices)
    
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
def __str__(self):
    return f"{self.service.name} - {self.frequency} for {self.duration} months , Booking time: {self.start_datetime} "
    


class Payment(models.Model):
    booking = models.ForeignKey('Booking', related_name='payments', on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=255)
    payment_status = models.CharField(max_length=50, default='Pending')
    payment_type = models.CharField(max_length=50, default='full')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    partial_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    installment_plan = models.BooleanField(default=False)
    installment_number = models.PositiveIntegerField(null=True, blank=True)
    frequency = models.CharField(max_length=20, null=True, blank=True)
    paid_datetime = models.DateTimeField(default=datetime.datetime.now) 
    due_months = models.IntegerField(null=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2 , null=True)
    appointment = models.ForeignKey('AppointmentBooking', on_delete=models.CASCADE, related_name='payments', null=True, blank=True)  # Corrected the ForeignKey

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('full', 'Full Payment'),
        ('partial', 'Partial'),
        ('installment', 'Installment'),
    ]

    def __str__(self):
        return f"Payment {self.id} for Appointment {self.appointment.id}" if self.appointment else f"Payment {self.id}"

        
 
class AppointmentBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
        
    ]
    
    booking_id = models.CharField(max_length=255)
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    customer_email = models.EmailField(null=True)
    
    def __str__(self):
        return f"AppointmentBooking {self.booking_id} on {self.appointment_date}"
    












        
