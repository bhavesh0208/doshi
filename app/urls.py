from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('reset-password/', reset_password, name='reset-password'),
    path('stocks/', stocks, name='stocks'),
    path('invoices/', invoices, name='invoices'),
    path('barcodes/', barcodes, name='barcodes'),
    path('exceptions/', exceptions, name='exceptions'),
]
