from django.contrib import admin
from .models import *

# Register your models here.


class UserModelAdmin(admin.ModelAdmin):
    list_display = [
        "_id",
        "name",
        "role",
        "email",
        "contact",
        "is_active",
        "last_login",
    ]


class StockItemModelAdmin(admin.ModelAdmin):
    list_display = [
        "_id",
        "sku_name",
        "sku_qty",
        "sku_rate",
        "sku_serial_no",
        "sku_status",
    ]


class InvoiceModelAdmin(admin.ModelAdmin):
    list_display = [
        "_id",
        "invoice_no",
        "invoice_party_name",
        "invoice_date",
        "invoice_item_scanned_status",
        "invoice_item_qty",
        "invoice_item_rate",
    ]


class ByPassModelAdmin(admin.ModelAdmin):
    list_display = [
        "_id",
        "bypass_invoice_no",
        "bypass_sku_name",
        "bypass_against_sku_name",
        "bypass_date",
        "bypass_time",
    ]


admin.site.register(User, UserModelAdmin)
admin.site.register(StockItem, StockItemModelAdmin)
admin.site.register(Invoice, InvoiceModelAdmin)
admin.site.register(ByPassModel, ByPassModelAdmin)
