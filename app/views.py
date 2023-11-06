import csv
from datetime import date

import xlwt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required, permission_required

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from app.models import *
from app.utils import *
from app.validators import *

# Create your views here.
INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"
REDIRECT_PATH_URI_SESSION_TOKEN = "_redirect_url_token"
token_generator = default_token_generator


def index(request):
    total_bypass_sku = ByPassModel.objects.filter(bypass_date=date.today()).count()
    total_sales = sum(
        [
            float(i["invoice_item_amount"])
            for i in Invoice.objects.filter(
                invoice_item_scanned_status="PENDING"
            ).values("invoice_item_amount")
        ]
    )
    total_sku_rate = round(
        sum([float(i["sku_rate"]) for i in StockItem.objects.all().values("sku_rate")]),
        2,
    )
    total_pending_invoices = Invoice.objects.filter(
        invoice_item_scanned_status="PENDING"
    ).values("invoice_no")
    inv = len(set([i["invoice_no"] for i in total_pending_invoices]))

    return render(
        request,
        "index.html",
        {
            "total_bypass_sku": total_bypass_sku,
            "total_sales": total_sales,
            "total_sku_rate": total_sku_rate,
            "total_pending_invoices": inv,
        },
    )


# def index(request):
#     if request.user.is_authenticated:
#         # role = request.session["role"]
#         role = "EMPLOYEE"
#         if role in ["CLIENT_HCH", "CLIENT"]:
#             return redirect("sku-items", page=1)
#         elif role in ["DISPATCHER"]:
#             return redirect("invoices")
#         else:
#             total_bypass_sku = ByPassModel.objects.filter(
#                 bypass_date=date.today()
#             ).count()
#             total_sales = sum(
#                 [
#                     float(i["invoice_item_amount"])
#                     for i in Invoice.objects.filter(
#                         invoice_item_scanned_status="PENDING"
#                     ).values("invoice_item_amount")
#                 ]
#             )
#             total_sku_rate = round(
#                 sum(
#                     [
#                         float(i["sku_rate"])
#                         for i in StockItem.objects.all().values("sku_rate")
#                     ]
#                 ),
#                 2,
#             )
#             total_pending_invoices = Invoice.objects.filter(
#                 invoice_item_scanned_status="PENDING"
#             ).values("invoice_no")
#             inv = len(set([i["invoice_no"] for i in total_pending_invoices]))

#             return render(
#                 request,
#                 "index.html",
#                 {
#                     "total_bypass_sku": total_bypass_sku,
#                     "total_sales": total_sales,
#                     "total_sku_rate": total_sku_rate,
#                     "total_pending_invoices": inv,
#                 },
#             )
#     else:
#         return redirect("login")


def register(request):
    if request.method == "POST":
        try:
            name = request.POST.get("registerName")
            email = request.POST.get("registerEmail")
            contact = request.POST.get("registerContact")
            password = request.POST.get("registerPassword")
            data = {
                "name": name,
                "email": email,
                "contact": contact,
                "password": password,
            }
            user = User(**data)
            user.full_clean()
            User.objects.create_user(**data)
            return redirect("login")

        except ValidationError as ve:
            for err in ve.message_dict.values():
                messages.error(request, str(err[0]))
            return redirect("register")
        except Exception as e:
            messages.error(request, str(e))
            return redirect("register")

    return render(request, "register.html")


def login_user(request):
    if request.method == "POST":
        try:
            email = request.POST["loginEmail"]
            password = request.POST["loginPassword"]
            user = authenticate(username=email, password=password)

            if user is None:
                messages.error(request, "Invalid email or password.")
                return redirect("login")
            elif not user.is_active:
                messages.error(request, "You are not allowed to access the portal")
                return redirect("login")
            else:
                login(request, user)
                if REDIRECT_PATH_URI_SESSION_TOKEN in request.session:
                    redirect_to = request.session.get(REDIRECT_PATH_URI_SESSION_TOKEN)
                    del request.session[REDIRECT_PATH_URI_SESSION_TOKEN]
                    return redirect(redirect_to)
                return redirect("index")

        except Exception as e:
            messages.error(request, e)
            return render(request, "login.html")

    else:
        # check if redirect path exists
        # i.e like http://127.0.0.1:8000/login/?next=/sku-items/1 -> /sku-items/1 here `next` is REDIRECT_FIELD_NAME
        redirect_to = request.GET.get(settings.REDIRECT_FIELD_NAME)
        if redirect_to:
            request.session.setdefault(REDIRECT_PATH_URI_SESSION_TOKEN, redirect_to)
        return render(request, "login.html")


def logout_user(request):
    if request.user:
        logout(request)
    return redirect("login")


def forgot_password(request):
    if request.method == "POST":
        try:
            email = request.POST["sendOTPEmail"]
            user = OTP.get_user_by_email(email)
            if user:
                otp_obj, created = OTP.objects.get_or_create(
                    email=user.email, user=user, defaults={"is_verified": False}
                )
                if not created:
                    otp_obj.is_verified = False
                    otp_obj.save()
                sent_status = otp_obj.send_forgot_password_otp_email()
                response = redirect("verify-otp")
                response.set_cookie("user-email", email)
                messages.success(request, "OTP sent successfully on this email id")
                return response
        except Exception as e:
            print(f"{e}")
            messages.error(request, e)
            return redirect("forgot-password")

    return render(request, "forgot-password.html")


def verify_otp(request):
    if request.method == "POST":
        try:
            code_1 = request.POST.get("code_1")
            code_2 = request.POST.get("code_2")
            code_3 = request.POST.get("code_3")
            code_4 = request.POST.get("code_4")
            code_5 = request.POST.get("code_5")
            code_6 = request.POST.get("code_6")
            otp = code_1 + code_2 + code_3 + code_4 + code_5 + code_6
            validate_otp(otp)
            email = request.COOKIES.get("user-email")
            instance = OTP.objects.get(email=email)
            verify = instance.verify_otp(otp)
            if verify:
                instance.is_verified = True
                instance.save()
                uidb64 = urlsafe_base64_encode(force_bytes(instance.user.pk))
                token = token_generator.make_token(instance.user)
                response = redirect("reset-password", uidb64=uidb64, token=token)

                response.delete_cookie("user-email")
                return response
            else:
                raise Exception("Invalid OTP")

        except Exception as e:
            messages.error(request, e)
            return redirect("verify-otp")

    if request.method == "GET":
        if "user-email" in request.COOKIES:
            return render(request, "verify-otp.html")
        else:
            return redirect("login")


def reset_password(request, **kwargs):
    UserModel = get_user_model()
    reset_url_token = "set-password"

    def get_user_from_uidb64(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            from bson import ObjectId

            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(_id=ObjectId(uid))
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserModel.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user

    if request.method == "GET":
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        user = get_user_from_uidb64(kwargs["uidb64"])

        if user is not None:
            token = kwargs["token"]
            if token == reset_url_token:
                session_token = request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if token_generator.check_token(user, session_token):
                    # If the token is valid, display the password reset form
                    return render(request, "reset-password.html")
            else:
                if token_generator.check_token(user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = request.path.replace(token, reset_url_token)
                    return redirect(redirect_url)
        else:
            messages.error(request, "Password reset unsuccessful.")
            return redirect("login")

    if request.method == "POST":
        password = request.POST["newPassword"]
        uidb64 = request.resolver_match.kwargs.get("uidb64")
        user = get_user_from_uidb64(uidb64)
        session_token = request.session.get(INTERNAL_RESET_SESSION_TOKEN)
        if token_generator.check_token(user, session_token):
            user.set_password(password)
            user.save()
            del request.session[INTERNAL_RESET_SESSION_TOKEN]
        messages.success(request, "password reset successful.")
        return redirect("login")


@login_required(login_url="login")
@permission_required("app.view_skuitems", raise_exception=True)
def get_stock_items(request, page):
    try:
        sku_list = StockItem.objects.all()
        # if request.user.is_authenticated:
        #     role = request.session["role"]

        #     if role == "CLIENT_HCH":
        #         sku_list = StockItem.objects.filter(sku_name__contains="HCH")
        #     elif role in ["ADMIN", "CLIENT", "EMPLOYEE"]:
        #         sku_list = StockItem.objects.all()
        #     else:
        #         return redirect("invoices")

        query = request.GET.get("query", "")
        if query:
            sku_list = sku_list.filter(
                Q(sku_name__icontains=query) | Q(sku_serial_no__icontains=query)
            ).order_by("sku_name")
        paginator = Paginator(sku_list, 25)
        page_number = page
        sku_obj = paginator.get_page(page_number)
        sku_obj.adjusted_elided_pages = paginator.get_elided_page_range(
            page_number, on_each_side=1
        )
        return render(request, "sku-list.html", {"sku_obj": sku_obj})
    except Exception as e:
        print(f"{e}")
        return redirect("index")


# @login_required(login_url="login")
# @permission_required("app.view_invoicetest", raise_exception=True)
def invoices(request):
    invoices = InvoiceTest.objects.all()[:1]
    return render(
        request,
        "invoices.html",
        {"invoices": invoices},
    )


# @login_required(login_url="login")
# @permission_required("app.view_invoicetest", raise_exception=True)
def invoice_details(request, invoice_no):
    # if request.user.is_authenticated:
    #     role = request.session["role"]
    #     if role in ["CLIENT_HCH", "CLIENT"]:
    #         return redirect("sku-items", page=1)
    #     else:
    invoice = InvoiceTest.objects.get(invoice_no=str(invoice_no))
    invoice_sku_list = invoice.invoice_items.all()
    # invoice_barcode_list = [i for i in invoice.invoice_items.all()]
    # print(invoice_barcode_list)
    # serial_numbers = StockItem.objects.filter(id__in=invoice_barcode_list).values(
    #     "sku_name", "sku_serial_no"
    # )

    # invoice_sku = zip(invoice, serial_numbers)

    return render(
        request,
        "invoice-details.html",
        {"invoice": invoice, "invoice_sku_list": invoice_sku_list},
    )


def bypass_products(request):
    # if request.user.is_authenticated:
    #     role = request.session["role"]
    #     if role in ["CLIENT_HCH", "CLIENT"]:
    #         return redirect("sku-items", page=1)
    #     else:
    get_bypass_list = ByPassModel.objects.all()
    return render(request, "bypass-products.html", {"bypass_list": get_bypass_list})


def invoice_verify(request, invoice_no):
    try:
        invoice = InvoiceTest.objects.get(invoice_no=str(invoice_no))
        invoice_sku_list = invoice.invoice_items.all()
        invoice_sku_list_pending = invoice.invoice_items.filter(
            item_scanned_status="PENDING"
        )

        # if "id" in request.session and invoice_sku_list.count() > 0:
        #     role = request.session["role"]
        #     if role in ["CLIENT_HCH", "CLIENT"]:
        #         return redirect("sku-items", page=1)
        #     else:
        return render(
            request,
            "invoice-verify.html",
            {
                "invoice_sku_list": invoice_sku_list,
                "invoice": invoice,
                "invoice_sku_list_pending": invoice_sku_list_pending,
            },
        )
    except InvoiceTest.DoesNotExist:
        messages.error(request, f"Invalid invoice no {invoice_no}")
        return redirect("invoices")


# api end point for scanning invoice sku item
@require_POST
def verify_sku_scan(request, invoice_no):
    """"""

    try:
        serial_no = request.POST["barcode"]
        invoice = InvoiceTest.objects.get(invoice_no=invoice_no)
        context = dict()
        print(invoice.status)
        if invoice.status == SCAN_STATUS_PENDING:
            # check if above stock exists in invoice
            invoice_stock_item = invoice._get_invoice_sku_item(serial_no)

            # check for valid stock item
            valid_sku_item = StockItem.get_stock_item(serial_no)

            if invoice_stock_item:
                invoice_stock_item.update_total_scan()
                context.update(
                    {
                        "status": "success",
                        "codename": "valid_sku_scan",
                        "msg": "S.K.U. mapped",
                    }
                )
            elif valid_sku_item:
                context.update(
                    {
                        "status": "warning",
                        "codename": "bypass_sku_item",
                        "msg": "Do you want to continue with this product ?",
                        "data": {"sku-name": valid_sku_item.sku_name},
                    }
                )
            else:
                context.update(
                    {
                        "status": "error",
                        "codename": "invalid_serial_no",
                        "msg": "Please try a different barcode as the one entered is not associated with any SKU item.",
                    }
                )
        else:
            context.update(
                {
                    "status": "warning",
                    "codename": "invoice_scanning_completed",
                    "msg": f"Invoice scanning already completed.",
                }
            )
            if invoice.status == SCAN_STATUS_EXTRA:
                context.update(
                    {
                        "msg": f"Invoice scanning already completed and sku with extra status found in invoice items."
                    }
                )

        return JsonResponse(context)

    except Invoice.DoesNotExist:
        context.update(
            {
                "status": "error",
                "codename": "invoice_not_found",
                "msg": f"Invalid invoice no {invoice_no}",
            }
        )
        return JsonResponse(context)

    except Exception as ep:
        context.update(
            {"status": "error", "codename": "undefined_exception", "msg": str(ep)}
        )
        return JsonResponse(context)


@require_POST
def bypass_invoice_sku_item(request, invoice_no):
    try:
        sku_name = request.POST["sku_name"]
        sku_against_name = request.POST["sku_against_name"]
        context = dict()

        # Fetch data
        invoice = InvoiceTest.objects.get(invoice_no=invoice_no)
        bypass_sku_item = invoice._get_invoice_sku_item(sku_against_name)
        sku_item = StockItem.get_stock_item(sku_name)

        if bypass_sku_item and sku_item:
            if bypass_sku_item.item_scanned_status != SCAN_STATUS_COMPLETED:
                bypass_sku_item.update_total_scan(
                    total_scan=sku_item.sku_base_qty, ignore_base_qty=True
                )
                bypass_data = {
                    "invoice": invoice,
                    "affected_invoice_stock_item": bypass_sku_item,
                    "bypass_stock_item": bypass_sku_item.stock_item,
                    "stock_item": sku_item,
                    # "user": request.user,
                    "bypass_qty": sku_item.sku_base_qty,
                }
                obj = ByPassModel.objects.create(**bypass_data)
                context.update(
                    {
                        "status": "success",
                        "codename": "bypass_success",
                        "msg": f"Stock item '{sku_item.sku_name}' has bypased against stock item '{bypass_sku_item.stock_item.sku_name}'.",
                    }
                )
            else:
                context.update(
                    {
                        "status": "warning",
                        "codename": "sku_scan_complete",
                        "msg": f"Not allowed to bypass the sku '{sku_against_name}' as status might be completed or extra.",
                    }
                )

            return JsonResponse(context)
        else:
            context.update(
                {
                    "status": "error",
                    "codename": "invalid_bypass_request",
                    "msg": f"Invalid bypass sku name '{sku_name}' or bypass against sku name '{sku_against_name}'",
                }
            )
            return JsonResponse(context)

    except Exception as e:
        print(str(e))
        return JsonResponse(
            {"status": "error", "msg": "record not added", "issue": str(e)}
        )


def generate_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename='BypassData.csv'"

    writer = csv.writer(response)
    writer.writerow(
        [
            "Invoice_no",
            "Bypass S.K.U. Name",
            "Bypass Against S.K.U. Name",
            "Bypass Date",
            "Bypass Time",
        ]
    )

    bypass_data = ByPassModel.objects.all().values()
    for each in bypass_data:
        invoice_no = Invoice.objects.get(id=each["bypass_invoice_no_id"]).invoice_no
        bypass_sku_name = StockItem.objects.get(id=each["bypass_sku_name_id"]).sku_name
        bypass_against_sku_name = StockItem.objects.get(
            id=each["bypass_against_sku_name_id"]
        )
        bypass_date = each["bypass_date"].strftime("%Y-%m-%d")
        bypass_time = each["bypass_time"].strftime("%H:%M:%S %p")

        bypass_data = (
            invoice_no,
            bypass_sku_name,
            bypass_against_sku_name,
            bypass_date,
            bypass_time,
        )
        writer.writerow(bypass_data)

    return response


# Rework on  this logic -> need to improve
def update_scan_qty(request, invoice_no):
    if request.user.is_authenticated:
        try:
            if request.method == "POST":
                get_invoice_no = invoice_no
                invoice_item_total_scan = request.POST["invoice-item-total-scan"]
                invoice_item_barcode = request.POST["invoice-barcode"]

                print(invoice_item_total_scan, get_invoice_no)
                sku_obj = StockItem.objects.get(sku_serial_no=invoice_item_barcode)

                if invoice_item_total_scan == "":
                    invoice_item_total_scan = sku_obj.sku_base_qty
                invoice = Invoice.objects.filter(
                    invoice_no=get_invoice_no, invoice_item_id=sku_obj.id
                )
                print(sku_obj, invoice_item_barcode, invoice_item_total_scan)
                invoice.update(invoice_item_total_scan=invoice_item_total_scan)

                if int(invoice[0].invoice_item_total_scan) == int(
                    invoice[0].invoice_item_qty
                ):
                    invoice.update(invoice_item_scanned_status="COMPLETED")
                elif int(invoice[0].invoice_item_total_scan) > int(
                    invoice[0].invoice_item_qty
                ):
                    invoice.update(invoice_item_scanned_status="EXTRA")
                else:
                    invoice.update(invoice_item_scanned_status="PENDING")

                return redirect("invoice-details", invoice_no=get_invoice_no)
        except StockItem.DoesNotExist:
            print("S.K.U. does not exists")
            messages.error(request, "Invalid Barcode")
            return redirect("invoice-details", invoice_no=get_invoice_no)
        except Exception as e:
            print("Error - ", e)
            messages.error(request, e)
            return redirect("invoice-details", invoice_no=get_invoice_no)


def dispatch_sku(request):
    if request.user.is_authenticated:
        try:
            role = request.session["role"]
            if role in ["CLIENT_HCH", "CLIENT"]:
                return redirect("sku-items", page=1)
            elif role in ["EMPLOYEE", "ADMIN"]:
                return redirect("invoices")
            else:
                if request.is_ajax:
                    invoice_no = request.GET.get("invoice_no", None)
                    sku_name = request.GET.get("sku_name", None)
                    sku_barcode_no = request.GET.get("sku_barcode_no", None)

                    invoice_sku_list = Invoice.objects.filter(
                        invoice_no=invoice_no,
                    )

                    sku_item = StockItem.objects.filter(
                        sku_name=sku_name, sku_serial_no=sku_barcode_no
                    )
                    if sku_item.exists():
                        invoice_item_obj = Invoice.objects.get(
                            invoice_no=invoice_no, invoice_item=sku_item[0]
                        )

                        invoice_item_obj.invoice_item_scanned_status = "COMPLETED"
                        user = User.objects.get(id=request.session["id"])
                        print(isinstance(user, User), invoice_item_obj.invoice_item)
                        invoice_item_obj.invoice_user = User.objects.get(
                            id=request.session["id"]
                        )
                        invoice_item_obj.invoice_item_total_scan = (
                            invoice_item_obj.invoice_item_qty
                        )
                        invoice_item_obj.save()
                    else:
                        raise Exception("S.k.U. not exists.")
                    # for item in invoice_sku_list:
                    #     item.invoice_item_scanned_status = "COMPLETED"
                    #     item.save()

                    # user_id = request.session["id"]
                    # user = User.objects.get(id=user_id)

                    # description = f"Invoice No: {invoice_no} dispatched by {user}."
                    # Activity.objects.create(
                    #     activity_type="DISPATCH",
                    #     activity_user=user,
                    #     activity_description=description,
                    # )
                    return JsonResponse(
                        {
                            "status": "success",
                            "msg": f"S.K.U. {sku_name} dispatched successfully.",
                        }
                    )
        except Exception as e:
            JsonResponse({"status": "error", "msg": e})


def dispatch_invoice(request, invoice_no):
    # if request.user.is_authenticated:
    try:
        # role = request.session["role"]
        # if role in ["CLIENT_HCH", "CLIENT"]:
        #     return redirect("sku-items", page=1)
        # elif role in ["DISPATCHER"]:
        #     return redirect("invoices")
        # else:
        invoice = InvoiceTest.objects.get(invoice_no=invoice_no)
        invoice_sku_list = invoice.invoice_items.all()
        if invoice_sku_list.exists():
            invoice_sku_list.update(item_scanned_status=SCAN_STATUS_COMPLETED)

        # user_id = request.session["id"]
        # user = User.objects.get(id=user_id)

        # description = f"Invoice No: {invoice_no} dispatched by {user}."
        # Activity.objects.create(
        #     activity_type="DISPATCH",
        #     activity_user=user,
        #     activity_description=description,
        # )

        return redirect("invoices")
        # return JsonResponse(
        #     {
        #         "status": "success",
        #         "msg": f"Invoice No.{invoice_no} dispatched successfully.",
        #     }
        # )

    except Exception as e:
        return redirect("invoices")


def update_sku(request):
    if request.user.is_authenticated:
        try:
            if request.method == "POST":
                sku_serial_no = request.POST["update-sku-srno"]
                sku_name = request.POST["update-sku-name"]
                sku_base_qty = request.POST["update-sku-qty"]

                sku_item = StockItem.objects.get(sku_serial_no=sku_serial_no)
                sku_name_before = sku_item.sku_name
                sku_base_qty_before = sku_item.sku_base_qty
                sku_item.sku_name = sku_name
                sku_item.sku_base_qty = sku_base_qty
                sku_item.save()

                user_id = request.session["id"]
                user = User.objects.get(id=user_id)
                description = f"Updated S.K.U.Name from {sku_name_before} to {sku_name} and Base Quantity from {sku_base_qty_before} to {sku_base_qty}."
                activity_type = "EDIT"
                Activity.objects.create(
                    activity_type=activity_type,
                    activity_description=description,
                    activity_user=user,
                )
                return redirect("sku-items", page=1)
        except Exception as e:
            return HttpResponse("Error -> ", e)
    return JsonResponse({"success": "record updated"})


def get_activity_logs(request):
    if request.user.is_authenticated:
        role = request.session["role"]
        if role in ["CLIENT_HCH", "CLIENT"]:
            return redirect("sku-items", page=1)
        elif role in ["DISPATCHER"]:
            return redirect("invoices")
        elif role in ["EMPLOYEE"]:
            return redirect("index")
        else:
            activity_data = Activity.objects.all()

            return render(
                request, "activity-logs.html", {"activity_data": activity_data}
            )
    return redirect("login")


def generate_excel_sku_items(request):
    if request.user.is_authenticated:
        role = request.session["role"]

        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = 'attachment; filename="StockUnits.xls"'

        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("StockItem")

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = [
            "S.K.U. Name",
            "Barcode Number",
        ]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        # rows = StockItem.objects.all().values_list('username', 'first_name', 'last_name', 'email')
        if role == "CLIENT_HCH":
            rows = StockItem.objects.filter(sku_name__contains="HCH").values_list(
                "sku_name", "sku_serial_no"
            )
        else:
            rows = StockItem.objects.all().values_list("sku_name", "sku_serial_no")

        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        return response


@login_required(login_url="login")
@permission_required("app.view_company", raise_exception=True)
def get_company_list(request):
    companies = Company.objects.all()
    return render(request, "companies.html", {"company_data": companies})


# def get_company_list(request):
# if request.user.is_authenticated:
#     role = request.session["role"]
#     if role in ["CLIENT_HCH", "CLIENT"]:
#         return redirect("sku-items", page=1)
#     elif role in ["DISPATCHER"]:
#         return redirect("invoices")
#     else:
#         companies = Company.objects.all()
#         return render(request, "companies.html", {"company_data": companies})
# else:
#     return redirect("login")


# def listing_sku_api(request):
#     if request.user.is_authenticated:
#         page_number = request.GET.get("page", 1)
#         startswith = request.GET.get("startswith", "")
#         sku_list = StockItem.objects.filter(sku_name__startswith=startswith).order_by('sku_name')
#         paginator = Paginator(sku_list, 25)
#         page_obj = paginator.get_page(page_number)

#         data = [{
#                     "sku-name": i.sku_name,
#                     "sku-qty": i.sku_qty
#                 }
#                 for i in page_obj.object_list
#                 ]

#         payload = {
#             "page":{
#                 "current": page_obj.number,
#                 "has_next":page_obj.has_next(),
#                 "has_previous":page_obj.has_previous()
#             },
#             "data": data
#         }
#         return JsonResponse(payload)
#     else:
#         return redirect("login")
