from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


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
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name
    
class Booking(models.Model):
    service = models.ForeignKey(Service, related_name="bookings", on_delete=models.CASCADE)
    frequency = models.CharField(max_length=255)
    duration = models.IntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    start_datetime = models.DateTimeField(default=timezone.now)
    
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

 


    












        
