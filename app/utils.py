from threading import Thread
from barcode import EAN13, generate
from random import randint
from .models import *
from io import BytesIO
from barcode.writer import ImageWriter
from django.conf import settings
import os
from django.core.mail import EmailMessage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


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
        e = EmailMessage(self.subject, self.body, from_email, to)
        
        if self.attachments is not None:
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


def sendEmailReport():
    """ send email to every user in database """

    user_email = User.objects.values('email')
    user_email_list = [i['email'] for i in user_email]

    today_date = datetime.today().strftime('%Y-%m-%d')
    bypass_sku_data = ByPassModel.objects.all().filter(bypass_datetime__date = today_date)
    
    try:

        if bypass_sku_data.exists():
            with open('Bypass_file.csv', mode='w') as employee_file:
                import csv
                writer = csv.writer(employee_file)
                writer.writerow(['Invoice_no', 'Bypass SKU Quantity', 'Bypass SKU Name', 'Bypass Against SKU Name', 'Bypass Datetime'])

                users = ByPassModel.objects.all().values_list('bypass_invoice_no__invoice_no', 'bypass_sku_name__sku_qty', 'bypass_sku_name__sku_name', 'bypass_against_sku_name__sku_name', 'bypass_datetime')

                for user in users:
                    writer.writerow(user)

            EmailThread('Bypass SKU List CSV data', 'CSV file for Bypass SKU Items', user_email_list, attachments='Bypass_file.csv').start()
        else:
            EmailThread('Bypass SKU List CSV data', 'There is no bypass SKU List generated today', user_email_list).start()
    except Exception as e:
        print(e)
        print("Error in sendEmailReport")

    

def startSchedular():
    """Create a BackgroundScheduler, and set the daemon parameter to True. This allows us to kill the thread when we exit the DJANGO application."""
    try:
        schedular = BackgroundScheduler(deamon=True)
        schedular.add_job(sendEmailReport, 'cron', hour=15, minute=11)
        schedular.start()
    except Exception as e:
        print('schedular shutdown successfully')
        schedular.shutdown()