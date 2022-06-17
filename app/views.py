from urllib import response
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from .models import *
from django.core.mail import send_mail
from django.core.files import File
from random import randint
from .validators import * 
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.conf import settings
from .utils import *
from django.urls import reverse
from datetime import datetime
import csv
from django.contrib.auth.hashers import make_password, check_password


# Create your views here.

def index(request):
    if 'id' in request.session:
        user_list = User.objects.all()
        if  SKUItems.objects.filter(sku_serial_no = None).exists():
            GenerateBRCode().start()
        return render(request, 'doshi/index.html', {'user' : user_list})
    else:
        return redirect('login')
        

def register(request):
    if request.method == "POST":
        
        
        # User.objects.filter(Q(email=email)|Q(contact=contact)).count() == 0

        try:
            name = request.POST['registerName']
            email = request.POST['registerEmail']
            contact = request.POST['registerContact']
            password = request.POST['registerPassword']

            if User.objects.filter(email=email).count() == 0:
                if User.objects.filter(contact=contact).count() == 0:
                    try:
                        User(name=name, email=email, contact=contact, password=password).full_clean()
                        encryptedpassword=make_password(password)
                        User.objects.create(name=name, email=email, contact=contact, password=encryptedpassword)
                        return redirect('login')
                    except ValidationError as e:
                        

                        messages.error(request, e.message_dict.values())
                        return redirect('register')
                else:
                    raise Exception("User with this contact number already exists ")
            else:
                raise Exception('User with this email id already exists')
        except Exception as e:
            messages.error(request, e)
            return redirect('register')

    return render(request, 'doshi/register.html')


def login(request):
    if request.method == 'POST':
        
        try:
            email = request.POST['loginEmail']
            password = request.POST['loginPassword']
            user = User.objects.get(email=email)
            
            if user:
                encryptedpassword=make_password(password)
               
                checkpassword=check_password(password, user.password)
                if check_password:
                    if user.status:
                        msg = "Logged In user " + user.name
                        request.session['id'] = user.id
                        request.session['name'] = user.name
                        return redirect('index')
                    else:
                        messages.error(request, "You are not allowed to access the portal")
                        return redirect('login')
                else:
                    messages.error(request, "Invalid Password")
                    return redirect('login')
        except User.DoesNotExist as e:
            msg = "Invalid User"
            messages.error(request, msg)
        except Exception as e:
            messages.error(request, e)

    return render(request, 'doshi/login.html')
        

def logout(request):
    if 'id' in request.session:
        request.session.flush()

    return redirect('login')


def forgot_password(request):
    if request.method == 'POST':
        
        try:
            email = request.POST['sendOTPEmail']
            get_usr = User.objects.get(email=email)
            if get_usr.status:
                otp = randint(1000, 9999)
                request.session['otp'] = otp
                request.session['email'] = email
                body = f"Please use the verification code below on the Doshi website: \n Your otp is {otp} \n If you didn't request this, you can ignore this email or let us know."
                EmailThread('OTP Verification', body, email).start()
                messages.success(request, "OTP sent successfully on this email id")
                return render(request, 'doshi/verify-otp.html', {'otp': otp, 'email': email})
            else:
                raise Exception("You are not allowed to access the portal")
        except User.DoesNotExist:
            messages.error(request, 'User does not exists') 
            return redirect('forgot-password')
        except Exception as e:
            messages.error(request, e) 
            return redirect('forgot-password')

    return render(request, 'doshi/forgot-password.html')


def verify_otp(request):
    if request.method == 'POST':
        try:
            verify_otp = request.POST['verifyOTP']
            if 'otp' in request.session:
                if int(verify_otp) == int(request.session['otp']):
                    messages.success(request, 'OTP verification successful')
                    del request.session['otp']
                    request.session['r-p'] = "12345"
                    return redirect('reset-password')
                else:
                    raise Exception("Invalid OTP ")
        except Exception as e:
            messages.error(request, e)
            return redirect('verify-otp')

    if 'otp' in request.session:
        return render(request, 'doshi/verify-otp.html')
    else:
        return redirect('login')
    

def reset_password(request):
    if request.method == 'POST':
            password = request.POST['newPassword']
            print(password)
            get_user = User.objects.get(email=request.session['email'])

            get_user.password = make_password(password)
            get_user.save()
            del request.session['r-p']
            return redirect('login')
        # try:
        #     password = request.POST['ResetPassword']
        #     print(password)
        #     get_user = User.objects.get(email=request.session['email'])
        #     get_user.password = password
        #     get_user.save()
        #     del request.session['r-p']
        #     return redirect('login')
        # except Exception as e:
        #     messages.error(request, e)
        #     return redirect('reset-password')

    if 'r-p' in request.session:
        return render(request, 'doshi/reset-password.html')
    else:
        return redirect('login')


def sku_items(request):
    try:
        if 'id' in request.session:
            sku_list = SKUItems.objects.exclude(sku_serial_no = None).filter(sku_status=1, sku_qty__gte=10) # remove
            
            # generate barcode if not exists
            generate_barcode_list = SKUItems.objects.filter(sku_serial_no = None)
            if  generate_barcode_list.exists():
                for sku in generate_barcode_list:
                    sno, filename = generate_barcode()
                    sku.sku_serial_no = sno
                    sku.sku_barcode_image = os.path.join('barcode/', filename)
                    sku.save() 

                # GenerateBRCode().start()
            zipBarcodes()
            return render(request,'doshi/sku-list.html', {'sku_list': sku_list})
        return redirect('login')
    except Exception as e:
        print(e)
        return redirect('index')


def all_invoices(request):
    if 'id' in request.session:
        invoices = Invoice.objects.all().values('invoice_no', 'invoice_party_name', 'invoice_date', 'invoice_total_amount').distinct()
        return render(request, 'doshi/all-invoices.html', {'invoices': invoices})

    return redirect('login')
        

def invoices(request):
    if 'id' in request.session:
        invoices = Invoice.objects.filter(invoice_item_scanned_status=False).values('invoice_no', 'invoice_party_name', 'invoice_date', 'invoice_total_amount').distinct()
        return render(request, 'doshi/invoices.html', {'invoices': invoices})

    return redirect('login')


def invoice_details(request, invoice_no):
    if 'id' in request.session:
        invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no))
        invoice_details = invoice_sku_list[0]
        return render(request, 'doshi/invoice-details.html', {'invoice_sku_list': invoice_sku_list, 'invoice_details': invoice_details})


# def barcodes(request):
#     if request.method == 'POST':
#         try:
#             sku_id = request.POST['sku_id']
#             get_sku = SKUItems.objects.filter(pk=sku_id, sku_serial_no=None)
            
#             if get_sku.count() > 0:
#                 sno, filename = generate_barcode()
#                 get_sku.update(sku_serial_no = sno, sku_barcode_image = os.path.join('barcode/', filename))
                
#             else:
#                 raise Exception('Unable to generate barcode ')
#         except Exception as e:
#             messages.error(request, e)
#             return redirect('barcodes')
        
#     if 'id' in request.session:
#         sku_list = SKUItems.objects.filter(sku_serial_no=None)
#         return render(request,'doshi/barcodes.html', {'sku_list': sku_list})

#     return redirect('login')


def bypassProducts(request):

    if 'id' in request.session:
        get_bypass_list = ByPassModel.objects.all()
        return render(request, 'doshi/bypass-products.html', {'bypass_list':get_bypass_list })
        
    return redirect('login')
        

def invoice_verify(request, invoice_no):  
    invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no)).order_by('invoice_item_scanned_status')
    invoice_pending_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no), invoice_item_scanned_status=False)
    print(invoice_pending_sku_list)
    invoice_barcode_list = [i.invoice_item.sku_serial_no for i in invoice_sku_list]
    request.session['invoice_barcode_list'] = invoice_barcode_list
    
    if 'id' in request.session and invoice_sku_list.count() > 0:
        return render(request, 'doshi/invoice-verify.html', {'invoice_sku_list': invoice_sku_list, 'invoice_no': invoice_no, 'invoice_pending_sku_list': invoice_pending_sku_list})
    return redirect('invoices')


def verifyInvoice(request):

    if request.method == "POST":

        try:
            invoice_no = request.POST['invoice']
            # check in all sku list whether barcode exists or not --> returns and sku objecct
            get_sku = SKUItems.objects.get(sku_serial_no=request.POST['barcode'])
            
            # Get invoice sku queryset
            get_invoice = Invoice.objects.filter(invoice_no=invoice_no, invoice_item_scanned_status=False).values('invoice_item__sku_name', 'invoice_item__sku_expiry_date', 'invoice_item_total_scan', 'invoice_item_qty', 'invoice_item_scanned_status')

            # convert above queryset to  list 
            get_sku_list = [i['invoice_item__sku_name'] for i in get_invoice ]
            
            # print("SKU GET : ", get_sku.sku_name)     BALL BEARING COK UC 206

            # print("GET SKU LIST : ", get_sku_list)       ['BALL BEARING COK UC 206', 'BALL BEARING COK UC 205']
           
            # print("get invoice -> ", get_invoice)   <QuerySet [{'invoice_item__sku_name': 'BALL BEARING COK UC 206'}, {'invoice_item__sku_name': 'BALL BEARING COK UC 205'}]>
            
            if (get_sku.sku_name in get_sku_list):
                get_invoice_item = get_invoice.filter(invoice_item=get_sku)
                
                if get_invoice_item[0]['invoice_item__sku_expiry_date'] < date.today():
                    raise Exception('SKU Expired')
                else:
                    if not get_invoice_item[0]['invoice_item_scanned_status']:
                        get_invoice_item.update(invoice_item_total_scan=F('invoice_item_total_scan') + 1)
                        if get_invoice_item[0]['invoice_item_total_scan'] == get_invoice_item[0]['invoice_item_qty']:
                            print(get_invoice_item)
                            Invoice.objects.filter(invoice_item__sku_name=get_sku.sku_name).update(invoice_item_scanned_status=True)
                    else:
                        raise Exception('SKU scanning completed')
                
                
                # sku_qty_invoice =  Invoice.objects.filter(invoice_no=invoice_no, invoice_item=get_sku)[0].invoice_item_qty

                get_sku.sku_qty -= 1
                get_sku.save()

                return JsonResponse({
                    "status": "success",
                    "msg": "S.K.U. mapped"
                })

            else:
                if get_sku_list:
                    return JsonResponse({
                        "status": "warning",
                        "msg": "Do you want to continue with this product ?",
                        "sku-name": get_sku.sku_name
                    })
                else:
                    raise Exception("S.K.U. scanning already completed")

        except SKUItems.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "msg": "Barcode does not exist"
            })

        except Exception as ep:

            print("Invoice Verify Error : ", ep)

            return JsonResponse({
                "status": "error",
                "msg": str(ep)
            })

    return redirect('invoices')


def bypassInvoice(request):

    if request.method == "POST":
        try:
            invoice_no = request.POST['invoice']
            sku_name = request.POST['sku_name']
            sku_against_name = request.POST['sku_against_name']
            
            sku_against_name_obj = SKUItems.objects.get(sku_name=sku_against_name)

            sku_name_obj = SKUItems.objects.get(sku_name=sku_name)

            invoice_obj = Invoice.objects.filter(invoice_no=invoice_no, invoice_item=sku_against_name_obj)

            if not invoice_obj[0].invoice_item_scanned_status:
                invoice_obj.update(invoice_item_total_scan = F('invoice_item_total_scan') + 1)
                if invoice_obj[0].invoice_item_total_scan == invoice_obj[0].invoice_item_qty:
                    Invoice.objects.filter(invoice_no=invoice_no, invoice_item=sku_against_name_obj).update(invoice_item_scanned_status=True, invoice_user=request.session['id'])
                    
                    # ByPassModel.objects.create(bypass_invoice_no=invoice_obj[0], bypass_sku_name=sku_name_obj, bypass_against_sku_name=sku_against_name_obj)
            else:
                raise Exception('SKU scanning already completed')
            
            
            # sku_against_name_obj.save()
            print(sku_name_obj.sku_qty)
            sku_name_obj.sku_qty -= 1
            sku_name_obj.save()
            ByPassModel.objects.create(bypass_invoice_no=invoice_obj[0], bypass_sku_name=sku_name_obj, bypass_against_sku_name=sku_against_name_obj)
            
            return JsonResponse({
                "status": "success",
                "msg": "record added"
            })

        except Exception as e:
            print(e)
            return JsonResponse({
                "status": "error",
                "msg": "record not added",
                "issue": str(e)
            })
    
    return redirect('invoices')


def generate_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="BypassData.csv"'

    writer = csv.writer(response)
    writer.writerow(['Invoice_no', 'Bypass SKU Name', 'Bypass Against SKU Name', 'Bypass SKU Quantity', 'Bypass Datetime'])
    
    users = ByPassModel.objects.all().values_list('bypass_invoice_no__invoice_no', 'bypass_sku_name__sku_name',  'bypass_against_sku_name__sku_name', 'bypass_against_sku_name__sku_qty', 'bypass_datetime')
    print(users)
    for user in users:
        writer.writerow(user)
    
    return response
