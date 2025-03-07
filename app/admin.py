from django.contrib import admin
from . models import CustomUser,Service,Booking,Payment,AppointmentBooking
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Service)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(AppointmentBooking)
