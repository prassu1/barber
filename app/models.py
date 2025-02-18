from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
# Create your models here.


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

    # Optional additional fields for user

    USERNAME_FIELD = 'username'  
    REQUIRED_FIELDS = ['email']  

    objects = CustomUserManager()

    def __str__(self):
        return self.username
    


    












        
