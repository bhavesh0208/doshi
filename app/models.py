from .validators import *
from djongo import models
from django.core.validators import validate_email
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("This object requires an email")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
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
        (ROLE_CLIENT_HCH, "Client_HCH"),
    )

    # DATABASE FIELDS
    _id = models.ObjectIdField()
    name = models.CharField(validators=[validate_name], max_length=70, default="")
    email = models.EmailField(
        max_length=70, validators=[validate_email], unique=True, default=""
    )
    contact = models.CharField(
        validators=[validate_contact], unique=True, max_length=10, default=""
    )
    role = models.CharField(
        max_length=30, choices=ROLES_TYPE_CHOICES, default=ROLE_EMPLOYEE
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = "email"

    # TO STRING METHOD
    def __str__(self):
        return self.name


class Company(models.Model):
    # DATABASE FIELDS
    _id = models.ObjectIdField()
    company_name = models.CharField(max_length=70, default="", unique=True)
    company_address = models.CharField(max_length=70, default="", blank=True)
    company_contact = models.CharField(max_length=10, default="", blank=True)
    company_formal_name = models.CharField(max_length=70, default="", blank=True)
    company_email = models.EmailField(
        max_length=70, validators=[validate_email], default=""
    )

    # TO STRING METHOD
    def __str__(self):
        return self.company_name


class SKUItems(models.Model):
    # DATABASE FIELDS
    _id = models.ObjectIdField()
    sku_name = models.CharField(max_length=100, unique=True, default="")
    sku_qty = models.IntegerField(default=0)
    sku_rate = models.FloatField(default=0.0)
    sku_amount = models.FloatField(default=0.0)
    sku_serial_no = models.CharField(
        default="", max_length=200, unique=True, blank=True
    )
    sku_status = models.BooleanField(
        default=True
    )  # True for Active and False for Inactive
    sku_base_qty = models.IntegerField(default=1)

    # TO STRING METHOD
    def __str__(self):
        return self.sku_name


class Invoice(models.Model):
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
    _id = models.ObjectIdField()
    invoice_no = models.CharField(max_length=200, default="")
    invoice_party_name = models.CharField(max_length=200, default="")
    invoice_sales_ledger = models.CharField(max_length=200, default="")
    invoice_date = models.DateField(auto_now_add=True)
    invoice_item = models.ForeignKey(
        SKUItems, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    invoice_item_qty = models.IntegerField(default=0)
    invoice_item_rate = models.CharField(max_length=200, default="")
    invoice_item_amount = models.FloatField(default=0.0)
    invoice_item_total_scan = models.IntegerField(default=0.0)
    invoice_total_qty = models.IntegerField(default=0)
    invoice_total_amount = models.FloatField(default=0.0)
    invoice_item_scanned_status = models.CharField(
        max_length=30, choices=INVOICE_ITEM_STATUS, default="PENDING"
    )
    invoice_user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, default=None, blank=True
    )  # user who created the invoice
    invoice_company = models.ForeignKey(
        Company, on_delete=models.DO_NOTHING, default=None, blank=True
    )

    # META CLASS
    class Meta:
        unique_together = ("invoice_no", "invoice_item")

    # TO STARING METHOD
    def __str__(self):
        return self.invoice_no


#  Bypass SKU Quantity Same #########
class ByPassModel(models.Model):
    # DATABASE FIELDS
    _id = models.ObjectIdField()
    bypass_invoice_no = models.ForeignKey(
        Invoice, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    bypass_sku_name = models.ForeignKey(
        SKUItems, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    bypass_against_sku_name = models.ForeignKey(
        SKUItems,
        on_delete=models.CASCADE,
        default=None,
        blank=True,
        related_name="bypass_against_sku_name",
    )
    bypass_date = models.DateField(default=timezone.now)
    bypass_time = models.TimeField(auto_now_add=True)
    # bypass_by = models.ForeignKey(invoice_user, on_delete=SET_NULL, default=None, blank=True)

    # TO STRING METHOD
    # def __str__(self):
    #     return self.bypass_invoice_no.invoice_no


class Activity(models.Model):
    # CHOICES
    ACTIVITY_DISPATCH = "DISPATCH"
    ACTIVITY_EDIT = "EDIT"
    ACTIVITY_TYPE_CHOICES = (
        (ACTIVITY_DISPATCH, "Dispatch Invoice"),
        (ACTIVITY_EDIT, "Edit S.K.U. Name or Base Qty"),
    )

    # DATABASE FIELDS
    _id = models.ObjectIdField()
    activity_type = models.CharField(
        max_length=30, choices=ACTIVITY_TYPE_CHOICES, default="DISPATCH"
    )
    activity_description = models.TextField(max_length=300, blank=True)
    activity_user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    activity_date = models.DateField(auto_now_add=True)
    activity_time = models.TimeField(auto_now_add=True)

    # TO STRING METHOD
    def __str__(self):
        self.activity_description
