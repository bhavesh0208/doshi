from django.db.models import *
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from .validators import *
from datetime import date



# Create your models here.


class User(Model):
    name = CharField(validators=[validate_name], max_length=70, default="")
    email = EmailField(max_length=70, validators=[validate_email], unique=True, default="")
    contact = CharField(validators=[validate_contact], unique=True, max_length=10, default="")
    password = CharField(validators=[validate_password], max_length=200, default="")

    def __str__(self):
        return self.name


class SKUItems(Model):
    sku_name = CharField(max_length=100, unique=True, default="")
    sku_qty = IntegerField(default=0)
    sku_rate = FloatField(default=0.0)
    sku_serial_no = CharField(default="", max_length=200, unique=True, blank=True, null=True)
    sku_barcode_image = ImageField(upload_to='barcode/', default='backup/')

    def __str__(self):
        return self.sku_name


class Invoice(Model):
    invoice_no = CharField(max_length=200, default="")
    invoice_party_name = CharField(max_length=200, default="")
    invoice_sales_ledger = CharField(max_length=200, default="")
    invoice_date = DateField(default=date.today())
    invoice_item = ForeignKey(SKUItems, on_delete=CASCADE, default=None, blank=True)
    invoice_item_qty = IntegerField(default=0.0)
    invoice_item_rate = FloatField(default=0.0)
    invoice_item_amount = FloatField(default=0.0)
    invoice_total_qty = IntegerField(default=0)
    invoice_total_amount = FloatField(default=0.0)
    invoice_item_scanned_status = BooleanField(default=False)
    

    def __str__(self):
        return self.invoice_no



