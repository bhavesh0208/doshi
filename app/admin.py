from django.contrib import admin
from .models import *

# Register your models here.


class UserModelAdmin(admin.ModelAdmin):
    list_display =['id', 'name', 'email', 'password', 'contact']



class StockModelAdmin(admin.ModelAdmin):
    list_display =['id', 'stockname', 'stocktotalqty', 'stockbaseqty', 'barcode']



admin.site.register(User, UserModelAdmin)
admin.site.register(Stock, StockModelAdmin)