from django.contrib import admin
from .models import *

# Register your models here.


class UserModelAdmin(admin.ModelAdmin):
    list_display =['id', 'name', 'email', 'password', 'contact']



class StockModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'stock_name', 'stock_qty', 'stock_rate']


class StockBarcodeModelAdmin(admin.ModelAdmin):
    list_display = ['serial_no', 'stock']


admin.site.register(User, UserModelAdmin)
admin.site.register(Stock, StockModelAdmin)
admin.site.register(StockBarcode, StockBarcodeModelAdmin)
