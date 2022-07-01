from threading import Thread
from barcode import EAN13, generate
from random import randint
from .models import *
from io import BytesIO
from barcode.writer import ImageWriter
from django.conf import settings
import os
from django.conf import settings
from django.core.mail import EmailMessage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from zipfile import ZipFile
import pathlib

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
        
        if isinstance(to, str):
            e = EmailMessage(self.subject, self.body, from_email, [to])
        else:
            e = EmailMessage(self.subject, self.body, from_email, to)
        
        if self.attachments is not None:
            e.attach_file(self.attachments)
        e.send()


class GenerateBRCode(Thread):
    def __init__(self):
        Thread.__init__(self)
    
    def run(self):
        sku_list = SKUItems.objects.all()
        
        for sku in sku_list:

            try:

                if sku.sku_barcode_image:
                    pass
            except Exception as ep:

                print(ep)

                filename = f"{sku.sku_serial_no}.jpg"
                filepath = f"/media/barcode/{filename}"
                print(os)

                with open(filepath, "wb") as f:
                    EAN13(sku.sku_serial_no, writer=ImageWriter()).write(f)


                sku.sku_barcode_image = filepath

                sku.save()


def generate_BRC():
    sku_list = SKUItems.objects.all()

    for sku in sku_list:
        filename =  generate_barcode(sku.sku_serial_no)
        # filepath = os.path.join()
        s3 = boto3.client('s3',  aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        s3.upload_file(Filename=f"./media/barcode/{filename}",Bucket=settings.AWS_STORAGE_BUCKET_NAME,Key=f"{filename}")
        



import boto3

def generate_barcode(sno=None):
    if sno is None:
        sno = EAN13(str(randint(100000000000, 999999999999)), writer=ImageWriter())
    
    filename = "{}.jpg".format(sno)
    filepath = "./media/barcode/{}".format(filename)
    
    with open(filepath, "wb") as f:
        EAN13(sno, writer=ImageWriter()).write(f)
    

    
    return filename

## Logic Incomplete @ 
def zipBarcodes():
    sku_file_paths = SKUItems.objects.all().values_list('sku_barcode_image', flat=True)
    with ZipFile('./media/AllBarcodes.zip','w') as archive:
        for image_path in sku_file_paths:
            if image_path == "backup/":
                continue
            elif image_path is not None :
                archive.write(os.path.join(settings.MEDIA_ROOT, image_path), arcname=os.path.basename(image_path))
        # print(archive.namelist())

def sendEmailReport():
    """ send email to every user in database """

    user_email = User.objects.values('email')
    user_email_list = [i.get('email') for i in user_email]

    today_date = datetime.today().strftime('%Y-%m-%d')
    bypass_sku_data = ByPassModel.objects.all().filter(bypass_datetime__contains = today_date)
    
    try:

        if bypass_sku_data.exists():
            with open('Bypass_file.csv', mode='w') as employee_file:
                import csv
                writer = csv.writer(employee_file)
                writer.writerow(['Invoice No', 'Bypass SKU Quantity', 'Bypass SKU Name', 'Bypass Against SKU Name', 'Bypass Datetime'])

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
        schedular.add_job(sendEmailReport, 'cron', hour=19, minute=30)
        schedular.start()
    except Exception as e:
        print('schedular shutdown successfully')
        schedular.shutdown()