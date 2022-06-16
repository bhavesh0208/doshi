from django.db.models import *
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from .validators import *
from datetime import date, datetime
from django.utils import timezone

# Create your models here.


class User(Model):
    name = CharField(validators=[validate_name], max_length=70, default="")
    email = EmailField(max_length=70, validators=[validate_email], unique=True, default="")
    contact = CharField(validators=[validate_contact], unique=True, max_length=10, default="")
    password = CharField(validators=[validate_password], max_length=200, default="")

    def __str__(self):
        return self.name

class Company(Model):
    company_name =  CharField(max_length=70, default="", unique=True)
    company_address = CharField(max_length=70, default="")
    company_contact = CharField(max_length=10, default="")
    company_formal_name = CharField(max_length=70, default="")
    # comapny_starting_from = DateField()


class SKUItems(Model):
    sku_name = CharField(max_length=100, unique=True, default="")
    sku_qty = IntegerField(default=0)
    sku_rate = FloatField(default=0.0)
    sku_serial_no = CharField(default="", max_length=200, unique=True, blank=True, null=True)
    sku_barcode_image = ImageField(upload_to='barcode/', default='backup/')
    sku_status = BooleanField(default=True) # True for Active and False for Inactive
    # sku_expiry_date = DateField(default=date.today())

    def __str__(self):
        return self.sku_name


class Invoice(Model):
    invoice_no = CharField(max_length=200, default="")
    invoice_party_name = CharField(max_length=200, default="")
    invoice_sales_ledger = CharField(max_length=200, default="")
    invoice_date = DateField(auto_now_add=True)
    invoice_item = ForeignKey(SKUItems, on_delete=SET_NULL, default=None, blank=True, null=True)
    invoice_item_qty = IntegerField(default=0)
    invoice_item_rate = FloatField(default=0.0)
    invoice_item_amount = FloatField(default=0.0)
    invoice_item_total_scan = IntegerField(default=0.0)
    invoice_total_qty = IntegerField(default=0)
    invoice_total_amount = FloatField(default=0.0)
    invoice_item_scanned_status = BooleanField(default=False)

    class Meta:
        unique_together = ('invoice_no', 'invoice_item')
    

    def __str__(self):
        return self.invoice_no


class ByPassModel(Model):
    bypass_invoice_no = ForeignKey(Invoice, on_delete=CASCADE, default=None, blank=True)
    bypass_sku_name = ForeignKey(SKUItems, on_delete=CASCADE, default=None, blank=True)
    bypass_against_sku_name = ForeignKey(SKUItems, on_delete=CASCADE, default=None, blank=True, related_name='bypass_against_sku_name')
    bypass_datetime = DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.bypass_sku_name.sku_serial_no

