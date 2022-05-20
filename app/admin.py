from django.contrib import admin
from .models import *

# Register your models here.


class UserModelAdmin(admin.ModelAdmin):
    list_display =['id', 'name', 'email', 'password', 'contact']



class SKUItemsModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'sku_name', 'sku_qty', 'sku_rate', 'sku_serial_no']



admin.site.register(User, UserModelAdmin)
admin.site.register(SKUItems, SKUItemsModelAdmin)
