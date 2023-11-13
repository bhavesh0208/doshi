from django.contrib import admin
from app.models import User, StockItem, InvoiceTest, ByPassModel

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


class InvoiceTestModelAdmin(admin.ModelAdmin):
    list_display = [
        "_id",
        "invoice_no",
        "invoice_party_name",
        "invoice_date",
        "total_qty",
        "total_amount",
    ]


class ByPassModelAdmin(admin.ModelAdmin):
    list_display = [
        "_id",
        "invoice",
        "affected_invoice_stock_item",
        "bypass_stock_item",
        "stock_item",
        "bypass_qty",
        "user",
        "created_at",
    ]


admin.site.register(User, UserModelAdmin)
admin.site.register(StockItem, StockItemModelAdmin)
admin.site.register(InvoiceTest, InvoiceTestModelAdmin)
admin.site.register(ByPassModel, ByPassModelAdmin)
