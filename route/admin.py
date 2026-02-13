from django.contrib import admin

# Register your models here.
from .models import FuelStation,RouteRequest,FuelStop

admin.site.register(FuelStation)
admin.site.register(RouteRequest)
admin.site.register(FuelStop)
