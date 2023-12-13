from django.urls import path
from app.views import *

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    # User Related Views
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("verify-otp/", verify_otp, name="verify-otp"),
    path("reset-password/<uidb64>/<token>/", reset_password, name="reset-password"),
    # Webportal content urls
    # Stock Item urls
    path("sku-items/", get_stock_items, name="sku-items"),
    path("sku-items/edit/<uid>/", update_sku, name="update-sku"),
    # Invoice urls
    path("invoice/", invoices, name="invoices"),
    path(
        "invoice/details/<invoice_no>/",
        invoice_details,
        name="invoice-details",
    ),
    path(
        "invoice/details/<invoice_no>/edit/scan-qty/",
        update_invoiceitem_scan_qty,
        name="update-scan-qty",
    ),
    path("invoice/verify/<invoice_no>/", invoice_verify, name="invoice-verify"),
    path(
        "invoice/verify/<invoice_no>/scan/",
        verify_sku_scan,
        name="verify-sku-scan",
    ),
    path(
        "invoice/verify/<invoice_no>/bypass/",
        bypass_invoice_sku_item,
        name="bypass-invoice-item",
    ),
    path(
        "invoices/verify/<invoice_no>/dispatch/sku-item/<uid>/",
        dispatch_sku,
        name="dispatch-sku",
    ),
    path("invoice/dispatch/<invoice_no>/", dispatch_invoice, name="dispatch-invoice"),
    path("bypass-products/", bypass_products, name="bypass-products"),
    # Activity log urls
    path("activity/logs/", get_activity_logs, name="activity-logs"),
    # CSV generate urls
    path("generate-csv-bypass/", generate_csv, name="generate-csv-bypass"),
    path(
        "generate-csv-sku-items/",
        generate_excel_sku_items,
        name="generate-csv-sku-items",
    ),
    # Company urls
    path("company/list/", get_company_list, name="company-list"),
]
