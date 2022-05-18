from django.db import models
from django.core.validators import validate_email
from django.contrib.auth import password_validation
from django.contrib.auth.password_validation import validate_password
from .validators import * 


# Create your models here.

class User(models.Model):
    name = models.CharField(validators=[validate_name], max_length=70)
    email = models.EmailField(max_length=70, validators=[validate_email], unique=True)
    contact = models.CharField(validators=[validate_contact], unique=True, max_length=10)
    password = models.CharField(validators=[validate_password], max_length=200)

    def __str__(self):
        return self.name


class Stock(models.Model):
    stockname = models.CharField(max_length=100)
    stocktotalqty = models.IntegerField()
    stockbaseqty = models.IntegerField()
    barcode = models.BigIntegerField(default=0)

    def __str__(self):
        return self.stockname


# In Process model
#class Barcode(models.Model):
#    barcode = models.BigIntegerField(unique=True, null=True, blank=True)
