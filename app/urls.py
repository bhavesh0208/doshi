from django.urls import path
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('reset-password/', reset_password, name='reset-password'),
    path('sku-items/', sku_items, name='sku-items'),
    path('invoices/', invoices, name='invoices'),
    path('all-invoices/', all_invoices, name='all-invoices'),
    path('invoices/invoice-verify/<invoice_no>', invoice_verify, name='invoice-verify'),
    path('invoices/dispatch-invoice', dispatchInvoice, name="dispatch-invoice"),
    path('all-invoices/invoice-details/<str:invoice_no>', invoice_details, name='invoice-details'),
    path('bypass-products/', bypassProducts, name='bypass-products'),
    path('verify-invoice', verifyInvoice, name="verify-invoice"),
    path('bypass-invoice', bypassInvoice, name="bypass-invoice"),
    path('generate-csv/', generate_csv, name='generate-csv'),
    path('update-scan-qty/', update_scan_qty, name="update-scan-qty"),
    path('sku-items/update-sku', update_sku, name='update-sku')
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
