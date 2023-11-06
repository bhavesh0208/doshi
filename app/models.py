from collections.abc import Iterable
from datetime import timedelta

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from django.contrib.auth import get_user_model
from djongo import models

from app.otp import OtpVerification
from doshi import settings

from .validators import *

# Scan invoice and stockitem choice
SCAN_STATUS_COMPLETED = "COMPLETED"
SCAN_STATUS_PENDING = "PENDING"
SCAN_STATUS_EXTRA = "EXTRA"


INVOICE_ITEM_SCAN_STATUS = STOCK_ITEM_SCAN_STATUS = (
    (SCAN_STATUS_PENDING, "Pending"),
    (SCAN_STATUS_COMPLETED, "Completed"),
    (SCAN_STATUS_EXTRA, "Extra"),
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("This object requires an email")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.role = "ADMIN"
        user.save(using=self._db)

        return user


class BaseModel(models.Model):
    _id = models.ObjectIdField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
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
    REQUIRED_FIELDS = ["name", "contact"]
    USERNAME_FIELD = "email"

    # TO STRING METHOD
    def __str__(self):
        return self.name


class Company(BaseModel):
    # DATABASE FIELDS
    company_name = models.CharField(max_length=70, default="", unique=True)
    company_address = models.CharField(max_length=70, default="", blank=True)
    company_contact = models.CharField(max_length=10, default="", blank=True)
    company_formal_name = models.CharField(max_length=70, default="", blank=True)
    company_email = models.EmailField(max_length=70, default="")

    objects = models.DjongoManager()

    # TO STRING METHOD
    def __str__(self):
        return self.company_name


class StockItem(BaseModel):
    # DATABASE FIELDS
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
    id = models.IntegerField(default=1)

    objects = models.DjongoManager()

    # TO STRING METHOD
    def __str__(self):
        return self.sku_name

    @classmethod
    def get_stock_item(cls, value: str):
        """Return a sku object from sku_name or sku_serial_no"""
        try:
            value = value.strip()
            sku_item = cls._default_manager.get(
                models.Q(sku_name__iexact=value) | models.Q(sku_serial_no__iexact=value)
            )
        except ObjectDoesNotExist:
            sku_item = None
        return sku_item


class InvoiceStockItem(BaseModel):
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    item_qty = models.IntegerField(default=0)
    item_rate = models.CharField(max_length=200, default="")
    item_amount = models.FloatField(default=0)
    item_total_scan = models.IntegerField(
        default=0
    )  # Qty that will be scan at each time
    item_scanned_status = models.CharField(
        max_length=30, choices=STOCK_ITEM_SCAN_STATUS, default=SCAN_STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TO STRING METHOD
    def __str__(self):
        return f"{self.stock_item.sku_name}"

    def update_total_scan(self, total_scan: int = 0, ignore_base_qty: bool = False):
        if ignore_base_qty:
            self.item_total_scan += total_scan
        else:
            self.item_total_scan += self.stock_item.sku_base_qty + total_scan

        if self.item_total_scan < self.item_qty:
            self.item_scanned_status = SCAN_STATUS_PENDING
        elif self.item_total_scan > self.item_qty:
            self.item_scanned_status = SCAN_STATUS_EXTRA
        else:
            self.item_scanned_status = SCAN_STATUS_COMPLETED
        self.save()


# New model for replacing old Invoice model and their related fields
class InvoiceTest(BaseModel):
    # DATABASE FIELDS
    invoice_no = models.CharField(max_length=200, default="")
    invoice_party_name = models.CharField(max_length=200, default="")
    invoice_sales_ledger = models.CharField(max_length=200, default="")
    invoice_date = models.DateField(auto_now_add=True)
    invoice_items = models.ArrayReferenceField(
        InvoiceStockItem, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    total_qty = models.IntegerField(default=0)
    total_amount = models.FloatField(default=0)
    last_interacting_user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, default=None, blank=True
    )  # user who created the invoice
    invoice_company = models.ForeignKey(
        Company, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    is_pi_invoice = models.BooleanField(  # A pro forma invoice (PI) is actually not an invoice.
        default=False  # It is a preliminary bill of sale sent to buyers when an order is placed and in advance of a shipment or delivery of goods.
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TO STARING METHOD
    def __str__(self):
        return self.invoice_no

    @property
    def status(self):
        status = SCAN_STATUS_COMPLETED
        filter_pending_objs = self.invoice_items.filter(
            item_scanned_status=SCAN_STATUS_PENDING
        ).exists()  # filter pending objs
        filter_extra_objs = self.invoice_items.filter(
            item_scanned_status=SCAN_STATUS_EXTRA
        ).exists()
        if filter_pending_objs:
            status = SCAN_STATUS_PENDING
        elif filter_extra_objs:
            status = SCAN_STATUS_EXTRA
        return status

    # @property
    # def _get_total_without_gst(self) :
    #     """Return amount of gst and net total without gst"""
    #     try:
    #         return self.total_amount / 1.18
    #     except ZeroDivisionError:
    #         return 0

    def _get_invoice_sku_item(self, value) -> InvoiceStockItem | None:
        """get sku item from sku_name or sku_serial_no and if it is included in invoice else none"""
        try:
            value = value.strip()
            return self.invoice_items.get(
                models.Q(stock_item__sku_name__iexact=value)
                | models.Q(stock_item__sku_serial_no__iexact=value)
            )
        except ObjectDoesNotExist:
            return None

    def _reset_invoice(self):
        """Reset the total scan of all the invoice sku items and mark their status as `pending`."""
        self.invoice_items.update(
            item_total_scan=0, item_scanned_status=SCAN_STATUS_PENDING
        )
        return self


class Invoice(BaseModel):
    # DATABASE FIELDS
    invoice_no = models.CharField(max_length=200, default="")
    invoice_party_name = models.CharField(max_length=200, default="")
    invoice_sales_ledger = models.CharField(max_length=200, default="")
    invoice_date = models.DateField(auto_now_add=True)
    # invoice_item = models.ForeignKey(
    #     StockItem, on_delete=models.DO_NOTHING, default=None, blank=True
    # )
    invoice_item = models.IntegerField()
    invoice_item_qty = models.IntegerField(default=0)
    invoice_item_rate = models.CharField(max_length=200, default="")
    invoice_item_amount = models.FloatField(default=0.0)
    invoice_item_total_scan = models.IntegerField(default=0.0)
    invoice_total_qty = models.IntegerField(default=0)
    invoice_total_amount = models.FloatField(default=0.0)
    invoice_item_scanned_status = models.CharField(
        max_length=30, choices=INVOICE_ITEM_SCAN_STATUS, default="PENDING"
    )
    invoice_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, default=None, blank=True
    )  # user who created the invoice
    invoice_company = models.ForeignKey(
        Company, on_delete=models.DO_NOTHING, default=None, blank=True
    )

    # TO STARING METHOD
    def __str__(self):
        return self.invoice_no


#  Bypass SKU Quantity Same #########
class ByPassModel(BaseModel):
    # DATABASE FIELDS
    invoice = models.ForeignKey(
        InvoiceTest, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    affected_invoice_stock_item = models.ForeignKey(
        InvoiceStockItem, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    bypass_stock_item = models.ForeignKey(
        StockItem, on_delete=models.DO_NOTHING, default=None, blank=True
    )  # bypass against stock item ie the sku present in invoice which is bypassed by other sku
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        default=None,
        blank=True,
        related_name="bypass_against_sku_name",
    )
    bypass_qty = models.IntegerField(default=1)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, default=None, blank=True
    )

    objects = models.DjongoManager()

    # TO STRING METHOD
    def __str__(self):
        return self.bypass_invoice.invoice_no


class Activity(BaseModel):
    # CHOICES
    ACTIVITY_DISPATCH = "DISPATCH"
    ACTIVITY_EDIT = "EDIT"
    ACTIVITY_TYPE_CHOICES = (
        (ACTIVITY_DISPATCH, "Dispatch Invoice"),
        (ACTIVITY_EDIT, "Edit S.K.U. Name or Base Qty"),
    )

    # DATABASE FIELDS
    activity_type = models.CharField(
        max_length=30, choices=ACTIVITY_TYPE_CHOICES, default="DISPATCH"
    )
    activity_description = models.TextField(max_length=300, blank=True)
    activity_user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, default=None, blank=True
    )
    activity_date = models.DateField(auto_now_add=True)
    activity_time = models.TimeField(auto_now_add=True)

    objects = models.DjongoManager()

    # TO STRING METHOD
    def __str__(self):
        self.activity_description


class OTP(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_secret = models.CharField(max_length=16)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    # valid_till = models.DateTimeField()

    def __str__(self):
        return self.email

    def send_forgot_password_otp_email(self):
        user = self.get_user_by_email(self.email)
        context = {}
        if user:
            totp = OtpVerification(
                token_validity_period=settings.OTP_EMAIL_TOKEN_VALIDITY
            )
            self.token = totp.generate_token()
            self.user = user
            self.otp_secret = totp.key
            self.email = user.email

            if not user.is_active:
                raise Exception(
                    "Access to the portal is restricted and requires contacting the administrator."
                )
            # self.otp = OTP(user=self.user, token=self.token)
            try:
                self.otp, created = self.__class__.objects.get_or_create(
                    email=self.email,
                    defaults={"user": self.user, "otp_secret": self.otp_secret},
                )
                if not created:
                    self.otp.otp_secret = self.otp_secret
                    self.otp.save()
            except Exception as e:
                print(f"Exception Occoured {e}")
                pass

            context.update({"token": self.token})
            if settings.OTP_EMAIL_BODY_TEMPLATE_PATH:
                body_html = get_template(settings.OTP_EMAIL_BODY_TEMPLATE_PATH).render(
                    context
                )
            else:
                body_html = None

            body = None
            send_mail(
                "OTP Verification",
                body,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                html_message=body_html,
            )
            return True
        else:
            raise Exception(f"User with given email {self.email} doesn't exist")

    def verify_otp(self, otp: str):
        totp = OtpVerification(
            key=self.otp_secret, token_validity_period=settings.OTP_EMAIL_TOKEN_VALIDITY
        )
        return totp.verify_otp(otp)

    @staticmethod
    def get_user_by_email(email: str):
        """
        The function checks if a user with a given email exists in the database and returns the user object
        if found, otherwise returns None.

        :param email: The email parameter is a string that represents the email address of a user
        :type email: str
        :return: either an instance of the User model if a user with the specified email exists, or None if
        no user with the specified email exists.
        """
        try:
            UserModel = get_user_model()
            return UserModel.objects.get(email=email)
        except ObjectDoesNotExist:
            return None
