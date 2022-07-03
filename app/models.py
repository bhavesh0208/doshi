from tkinter.tix import STATUS
from django.db.models import *
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from .validators import *
from datetime import date, datetime
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# Create your models here.


class User(Model):

    # CHOICES
    ROLE_ADMIN = "ADMIN"
    ROLE_EMPLOYEE = "EMPLOYEE"
    ROLE_DISPATCHER = "DISPATCHER"
    ROLE_CLIENT = "CLIENT"
    ROLE_CLIENT_HCH = "CLIENT_HCH"
    ROLES_TYPE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_EMPLOYEE, "Employee"),
        (ROLE_DISPATCHER, "Dispatcher"),
        (ROLE_CLIENT, "Client"),
        (ROLE_CLIENT_HCH, "Client_HCH")
    )

    # DATABASE FIELDS
    name = CharField(validators=[validate_name], max_length=70, default="")
    email = EmailField(
        max_length=70, validators=[validate_email], unique=True, default=""
    )
    contact = CharField(
        validators=[validate_contact], unique=True, max_length=10, default=""
    )
    password = CharField(validators=[validate_password], max_length=300, default="")
    role = CharField(max_length=30, choices=ROLES_TYPE_CHOICES, default="EMPLOYEE")
    status = BooleanField(default=False)

    # TO STRING METHOD
    def __str__(self):
        return self.name


class Company(Model):

    # DATABASE FIELDS
    company_name = CharField(max_length=70, default="", unique=True)
    company_address = CharField(max_length=70, default="", blank=True)
    company_contact = CharField(max_length=10, default="", blank=True)
    company_formal_name = CharField(max_length=70, default="ABC", blank=True)
    # comapny_starting_from = DateField()

    # TO STRING METHOD
    def __str__(self):
        return self.company_name


class SKUItems(Model):

    # DATABASE FIELDS
    sku_name = CharField(max_length=100, unique=True, default="")
    sku_qty = IntegerField(default=0)
    sku_rate = FloatField(default=0.0)
    sku_amount = FloatField(default=0.0)
    sku_serial_no = CharField(default="", max_length=200, unique=True, blank=True)
    sku_barcode_image = ImageField(upload_to="barcode/", default="backup/")
    sku_status = BooleanField(default=True)  # True for Active and False for Inactive
    sku_base_qty = IntegerField(default=1)
    # sku_expiry_date = DateField(default=date.today())

    # TO STRING METHOD
    def __str__(self):
        return self.sku_name


class Invoice(Model):

    # CHOICES
    STATUS_COMPLETED = "COMPLETED"
    STATUS_PENDING = "PENDING"
    STATUS_EXTRA = "EXTRA"
    INVOICE_ITEM_STATUS = (
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_EXTRA, "Extra"),
    )

    # DATABASE FIELDS
    invoice_no = CharField(max_length=200, default="")
    invoice_party_name = CharField(max_length=200, default="")
    invoice_sales_ledger = CharField(max_length=200, default="")
    invoice_date = DateField(auto_now_add=True)
    invoice_item = ForeignKey(SKUItems, on_delete=DO_NOTHING, default=None, blank=True)
    invoice_item_qty = IntegerField(default=0)
    invoice_item_rate = CharField(max_length=200, default="")
    invoice_item_amount = FloatField(default=0.0)
    invoice_item_total_scan = IntegerField(default=0.0)
    invoice_total_qty = IntegerField(default=0)
    invoice_total_amount = FloatField(default=0.0)
    invoice_item_scanned_status = CharField(
        max_length=30, choices=INVOICE_ITEM_STATUS, default="PENDING"
    )
    invoice_user = ForeignKey(
        User, on_delete=DO_NOTHING, default=None, blank=True
    )  # user who created the invoice
    invoice_company = ForeignKey(
        Company, on_delete=DO_NOTHING, default=None, blank=True
    )

    # META CLASS
    class Meta:
        unique_together = ("invoice_no", "invoice_item")

    # TO STARING METHOD
    def __str__(self):
        return self.invoice_no


#  Bypass SKU Quantity Same #########
class ByPassModel(Model):

    # DATABASE FIELDS
    bypass_invoice_no = ForeignKey(Invoice, on_delete=CASCADE, default=None, blank=True)
    bypass_sku_name = ForeignKey(SKUItems, on_delete=CASCADE, default=None, blank=True)
    bypass_against_sku_name = ForeignKey(
        SKUItems,
        on_delete=CASCADE,
        default=None,
        blank=True,
        related_name="bypass_against_sku_name",
    )
    bypass_date = DateField(auto_now_add=True)
    bypass_time = TimeField(auto_now_add=True)
    # bypass_by = ForeignKey(invoice_user, on_delete=SET_NULL, default=None, blank=True)

    # TO STRING METHOD
    def __str__(self):
        return self.bypass_invoice_no
