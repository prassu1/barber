from django.contrib import admin
from . models import CustomUser,Service,Booking
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Service)
admin.site.register(Booking)