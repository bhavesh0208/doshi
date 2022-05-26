from threading import Thread
from django.core.mail import send_mail
from barcode import EAN13, generate
from random import randint
from .models import *
from io import BytesIO
from barcode.writer import ImageWriter
from django.conf import settings
import os
from django.core.mail import EmailMessage


class EmailThread(Thread):
    def __init__(self, subject, body, email, attachments = None):
        self.subject = subject
        self.body = body
        self.email = email
        self.attachments =attachments
        Thread.__init__(self)

    def run(self):
        from_email = "djangodeveloper09@gmail.com"
        to = self.email
        e = EmailMessage(self.subject, self.body, from_email, [to])
        e.attach_file(self.attachments)
        e.send()


def generate_barcode():
    sno = EAN13(str(randint(100000000000, 999999999999)), writer=ImageWriter())
    
    if SKUItems.objects.filter(sku_serial_no=sno).count() > 0:
        generate_barcode()
    else:
        filename = "Barcode_{}.png".format(sno)
        filepath = "./media/barcode/{}".format(filename)
        
        with open(filepath, "wb") as f:
            EAN13(sno.ean, writer=ImageWriter()).write(f)
        
        return (sno.ean, filename)

