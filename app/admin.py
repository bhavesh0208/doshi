from django.contrib import admin
from .models import *

# Register your models here.


class UserModelAdmin(admin.ModelAdmin):
    list_display =['id', 'name', 'email', 'password', 'contact']



class SKUItemsModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'sku_name', 'sku_qty', 'sku_rate', 'sku_serial_no', 'sku_barcode_image']


class InvoiceModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice_no', 'invoice_party_name', 'invoice_date', 'invoice_item', 'invoice_item_qty', 'invoice_item_rate']


admin.site.register(User, UserModelAdmin)
admin.site.register(SKUItems, SKUItemsModelAdmin)
admin.site.register(Invoice, InvoiceModelAdmin)