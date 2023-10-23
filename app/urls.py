from django.urls import path
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    path("", index, name="index"),
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("verify-otp/", verify_otp, name="verify-otp"),
    path("reset-password/", reset_password, name="reset-password"),
    path("sku-items/<int:page>", sku_items, name="sku-items"),
    path("invoices/", invoices, name="invoices"),
    path("all-invoices/", get_all_invoices, name="all-invoices"),
    path("invoices/invoice-verify/<invoice_no>", invoice_verify, name="invoice-verify"),
    path("invoices/dispatch-invoice/", dispatch_invoice, name="dispatch-invoice"),
    path(
        "all-invoices/invoice-details/<invoice_no>",
        invoice_details,
        name="invoice-details",
    ),
    path("bypass-products/", bypass_products, name="bypass-products"),
    path("verify-invoice/", verify_invoice, name="verify-invoice"),
    path("bypass-invoice/", bypass_invoice, name="bypass-invoice"),
    path("generate-csv-bypass/", generate_csv, name="generate-csv-bypass"),
    path("update-scan-qty/<invoice_no>", update_scan_qty, name="update-scan-qty"),
    path("sku-items/update-sku/", update_sku, name="update-sku"),
    path("activity-logs/", get_activity_logs, name="activity-logs"),
    path(
        "generate-csv-sku-items/",
        generate_excel_sku_items,
        name="generate-csv-sku-items",
    ),
    path("company-list/", get_company_list, name="company-list"),
    path(
        "invoices/invoice-verify/dispatch-sku/",
        dispatch_sku,
        name="dispatch-sku",
    ),
    # path('api/sku-items', listing_sku_api, name="sku-items-api"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
