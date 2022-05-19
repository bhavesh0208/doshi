from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import *
from django.core.mail import send_mail
from django.core.files import File
from random import randint
from .validators import * 
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.http import JsonResponse
from .utils import *


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
                        # print(list(e.message_dict.values()), type(e.message_dict))

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


def stocks(request):
    if 'id' in request.session:
        stockList = Stock.objects.filter(is_generated=True)
        return render(request,'doshi/stocks.html', {'stockList': stockList})

    return redirect('login')


def invoices(request):
    if 'id' in request.session:
        return render(request, 'doshi/invoices.html')

    return redirect('login')


def barcodes(request):
    if request.method == 'POST':
        try:
            get_stock = Stock.objects.get(pk=request.POST['stock_id'])
            
            if not StockBarcode.objects.filter(stock=get_stock).count() > 0 and get_stock.is_generated == False:
                sno = generate()
                StockBarcode.objects.create(serial_no=sno, stock=get_stock)
                get_stock.is_generated = True
                get_stock.save()
                messages.success(request, 'Barcode Generated')
                stockList = Stock.objects.filter(is_generated=False)
                return render(request, 'doshi/barcodes.html',  {'stockList': stockList})
            
        except Exeception as e:
            messages.error(request, e)
            return redirect('barcodes')
            

    if 'id' in request.session:
        stockList = Stock.objects.filter(is_generated=False)
        return render(request, 'doshi/barcodes.html', {'stockList': stockList})
    
    return redirect('login')


def download_barcode(request):
    pass    


def exceptions(request):
    if 'id' in request.session:
        return render(request, 'doshi/exceptions.html')

    return redirect('login')
        

def createBarcode(request):

    StockBarcode.objects.create(serial_no=generate())
