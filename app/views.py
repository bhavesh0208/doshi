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


# Create your views here.

def index(request):
    if 'id' in request.session:
        user_list = User.objects.all()
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
                        User.objects.create(name=name, email=email, contact=contact, password=password)
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
                if password == user.password:
                    msg = "Logged In user " + user.name
                    request.session['id'] = user.id
                    request.session['name'] = user.name
                    return redirect('index')
                else:
                    messages.error(request, "Invalid Password ")
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
            if get_usr:
                otp = randint(1000, 9999)
                request.session['otp'] = otp
                request.session['email'] = email
                EmailThread(email, otp).start()
            messages.success(request, "OTP sent successfully on this email id...")
            return render(request, 'doshi/verify-otp.html', {'otp': otp, 'email': email})
        except Exception as e:
            messages.error(request, 'User does not exists ')
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
        try:
            password = request.POST['ResetPassword']
            get_user = User.objects.get(email=request.session['email'])
            get_user.password = password
            get_user.save()
            del request.session['r-p']
            return redirect('login')
        except Exception as e:
            messages.error(request, e)
            return redirect('reset-password')

    if 'r-p' in request.session:
        return render(request, 'doshi/reset-password.html')
    else:
        return redirect('login')


def sku_items(request):
    if 'id' in request.session:
        sku_list = SKUItems.objects.exclude(sku_serial_no = None)
        return render(request,'doshi/sku-list.html', {'sku_list': sku_list})

    return redirect('login')


def invoices(request):
    if 'id' in request.session:
        invoices = Invoice.objects.all().values('invoice_no', 'invoice_party_name', 'invoice_date', 'invoice_total_amount').distinct()
        return render(request, 'doshi/invoices.html', {'invoices': invoices})

    return redirect('login')
    

def barcodes(request):
    if request.method == 'POST':
        try:
            sku_id = request.POST['sku_id']
            get_sku = SKUItems.objects.filter(pk=sku_id, sku_serial_no=None)
            
            if get_sku.count() > 0:
                sno, filename = generate_barcode()
                get_sku.update(sku_serial_no = sno, sku_barcode_image = os.path.join('barcode/', filename))
                
            else:
                raise Exception('Unable to generate barcode ')
        except Exception as e:
            print(e)
            messages.error(request, e)
            return redirect('barcodes')
        
    if 'id' in request.session:
        sku_list = SKUItems.objects.filter(sku_serial_no=None)
        return render(request,'doshi/barcodes.html', {'sku_list': sku_list})

    return redirect('login')


def bypassProducts(request):

    if 'id' in request.session:
        get_bypass_list = ByPassSKUModel.objects.all()
        return render(request, 'doshi/bypass-products.html', {'bypass_list':get_bypass_list })
        
    return redirect('login')
        

def invoice_verify(request, invoice_no):  
    invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no), invoice_item_scanned_status=False)
    invoice_barcode_list = [i.invoice_item.sku_serial_no for i in invoice_sku_list]
    request.session['invoice_barcode_list'] = invoice_barcode_list
    
    try:
        if request.method == 'POST':
            barcode_no = request.POST['barcodeInput']

            sku = SKUItems.objects.filter(sku_serial_no=barcode_no)
            if sku.count() > 0:
                invoice_obj = invoice_sku_list.filter(invoice_item=sku[0])
                if invoice_obj.count() > 0:
                    invoice_obj.update(invoice_item_scanned_status=True)
                    invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no), invoice_item_scanned_status=False)
                    return JsonResponse({
                        'data': 'success'
                    })
                else:

                    raise Exception('hello world')
            else:
                raise Exception('Barcode does not exists please check SKU list and generate the barcode')
            
    except Exception as e:
        messages.error(request, e)
        return HttpResponseRedirect(reverse('invoice-verify', args=(invoice_no,)))


    if 'id' in request.session:
        return render(request, 'doshi/invoice-verify.html', {'invoice_sku_list': invoice_sku_list, 'invoice_no': invoice_no})


def verifyInvoice(request):

    if request.method == "POST":

        try:
            # check in all sku list whether barcode exists or not --> returns and sku objecct
            get_sku = SKUItems.objects.get(sku_serial_no=request.POST['barcode'])

            # Get invoice sku queryset
            get_invoice = Invoice.objects.filter(invoice_no=request.POST['invoice']).values('invoice_item__sku_name')

            # convert above queryset to  list
            get_sku_list = [i['invoice_item__sku_name'] for i in get_invoice]

            # print("SKU GET : ", get_sku.sku_name)     BALL BEARING COK UC 206

            # print("GET SKU LIST : ", get_sku_list)       ['BALL BEARING COK UC 206', 'BALL BEARING COK UC 205']
           
            # print("get invoice -> ", get_invoice)   <QuerySet [{'invoice_item__sku_name': 'BALL BEARING COK UC 206'}, {'invoice_item__sku_name': 'BALL BEARING COK UC 205'}]>

            if get_sku.sku_name == request.POST['check-sku']:
                Invoice.objects.filter(invoice_item__sku_name=get_sku.sku_name).update(invoice_item_scanned_status=True)
                print('success')
                
                return JsonResponse({
                    "status": "success",
                    "msg": "SKU mapped"
                })

            elif get_sku.sku_name in get_sku_list:
                print('error')

                return JsonResponse({
                    "status": "error",
                    "msg": "SKU in Invoice"
                    
                })

            else:
                print('warning')
                return JsonResponse({
                    "status": "warning",
                    "msg": "Do you want to continue with this product ?",
                    "sku-name": get_sku.sku_name
                    
                })

        except Exception as ep:

            print("Invoice Verify Error : ", ep)

            return JsonResponse({
                "status": "error",
                "msg": "SKU is not present"
            })

    return redirect('invoices')


def bypassInvoice(request):

    if request.method == "POST":
        print(request.POST)
        
        try:
            invoice_no = request.POST['invoice']
            sku_name = request.POST['sku_name']
            sku_against_name = request.POST['sku_against_name']
            date = request.POST['date']
            time = request.POST['time']
            
            invoice_obj = Invoice.objects.filter(invoice_no=invoice_no)
            print("Invoice obj -> ",invoice_obj)
            sku_name_obj = SKUItems.objects.get(sku_name=sku_name)
            print("SKU_obj -> ", sku_name_obj)
            sku_against_name_obj = SKUItems.objects.get(sku_name=sku_against_name)
            print("SKU_------->  ", sku_against_name_obj)
            # date = datetime.strptime("%m/%d/%Y", date)
            # time = datetime.strptime("%H:%M:%S %p", time)

            ByPassSKUModel.objects.create(bypass_invoice_no=invoice_obj[0], bypass_sku_name=sku_name_obj, bypass_against_sku_name=sku_against_name_obj)

            return JsonResponse({
                "status": "success",
                "msg": "record adddddddddddddddddddddddddd"
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "msg": "record not adddddddddddddddddddddddd",
                "issue": str(e)
            })
    
    return redirect('invoices')
