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


def exceptions(request):
    if 'id' in request.session:
        return render(request, 'doshi/exceptions.html')

    return redirect('login')
        

def invoice_verify(request, invoice_no):  
    invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no), invoice_item_scanned_status=False)
    invoice_barcode_list = [i.invoice_item.sku_serial_no for i in invoice_sku_list]
    request.session['invoice_barcode_list'] = invoice_barcode_list
    
    try:
        if request.method == 'POST':
            barcode_no = request.POST['barcodeInput']
            
            if len(barcode_no) != 13:
                raise Exception('Barcode length must be 13')
                return render(request, 'doshi/invoice-verify.html', {'invoice_no': invoice_no,'invoice_sku_list': invoice_sku_list})
            
            sku = SKUItems.objects.filter(sku_serial_no=barcode_no)
            if sku.count() > 0:
                invoice_obj = invoice_sku_list.filter(invoice_item=sku[0])
                if invoice_obj.count() > 0:
                    invoice_obj.update(invoice_item_scanned_status=True)
                    invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no), invoice_item_scanned_status=False)
                    print('hello')
                    return HttpResponseRedirect(reverse('invoice-verify', args=(invoice_no,)))
                else:

                    raise Exception('hello world')
            else:
                raise Exception('Barcode does not exists please check SKU list and generate the barcode')
            
    except Exception as e:
        messages.error(request, e)
        return HttpResponseRedirect(reverse('invoice-verify', args=(invoice_no,)))


    if 'id' in request.session:
        return render(request, 'doshi/invoice-verify.html', {'invoice_sku_list': invoice_sku_list, 'invoice_no': invoice_no})

