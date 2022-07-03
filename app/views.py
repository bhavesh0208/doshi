from logging import raiseExceptions
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
from datetime import datetime, date
import csv
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator
from django.http import HttpResponse


# Create your views here.


def index(request):
    if "id" in request.session:
        role = request.session["role"]
        if role in ["CLIENT_HCH", "CLIENT", "DISPATCHER"]:
            return redirect("sku-items")
        else:
            total_bypass_sku = ByPassModel.objects.filter(
                bypass_date=date.today()
            ).count()
            total_sales = sum(
                [
                    float(i["invoice_item_amount"])
                    for i in Invoice.objects.filter(
                        invoice_item_scanned_status="PENDING"
                    ).values("invoice_item_amount")
                ]
            )
            total_sku_rate = round(
                sum(
                    [
                        float(i["sku_rate"])
                        for i in SKUItems.objects.all().values("sku_rate")
                    ]
                ),
                2,
            )
            total_pending_invoices = Invoice.objects.filter(
                invoice_item_scanned_status="PENDING"
            ).values("invoice_no")
            inv = len(set([i["invoice_no"] for i in total_pending_invoices]))

            return render(
                request,
                "doshi/index.html",
                {
                    "total_bypass_sku": total_bypass_sku,
                    "total_sales": total_sales,
                    "total_sku_rate": total_sku_rate,
                    "total_pending_invoices": inv,
                },
            )
    else:
        return redirect("login")


def register(request):
    if request.method == "POST":

        try:
            name = request.POST["registerName"]
            email = request.POST["registerEmail"]
            contact = request.POST["registerContact"]
            password = request.POST["registerPassword"]

            if User.objects.filter(email=email).count() == 0:
                if User.objects.filter(contact=contact).count() == 0:
                    try:
                        User(
                            name=name, email=email, contact=contact, password=password
                        ).full_clean()
                        encryptedpassword = make_password(password)
                        User.objects.create(
                            name=name,
                            email=email,
                            contact=contact,
                            password=encryptedpassword,
                        )
                        return redirect("login")
                    except ValidationError as e:

                        messages.error(request, e.message_dict.values())
                        return redirect("register")
                else:
                    raise Exception("User with this contact number already exists ")
            else:
                raise Exception("User with this email id already exists")
        except Exception as e:
            messages.error(request, e)
            return redirect("register")

    return render(request, "doshi/register.html")


def login(request):
    if request.method == "POST":

        try:
            email = request.POST["loginEmail"]
            password = request.POST["loginPassword"]
            user = User.objects.get(email=email)

            if user:
                encryptedpassword = make_password(password)
                checkpassword = check_password(password, user.password)
                if check_password:
                    if user.status:
                        msg = "Logged In user " + user.name
                        request.session["id"] = user.id
                        request.session["name"] = user.name
                        request.session["role"] = user.role
                        if user.role in ["CLIENT_HCH", "CLIENT", "DISPATCHER"]:
                            return redirect("sku-items")
                        else:
                            return redirect("index")
                    else:
                        messages.error(
                            request, "You are not allowed to access the portal"
                        )
                        return redirect("login")
                else:
                    messages.error(request, "Invalid Password")
                    return redirect("login")
        except User.DoesNotExist as e:
            msg = "Invalid User"
            messages.error(request, msg)
        except Exception as e:
            messages.error(request, e)

    return render(request, "doshi/login.html")


def logout(request):
    if "id" in request.session:
        request.session.flush()

    return redirect("login")


def forgot_password(request):
    if request.method == "POST":

        try:
            email = request.POST["sendOTPEmail"]
            get_usr = User.objects.get(email=email)
            if get_usr.status:
                otp = randint(1000, 9999)
                request.session["otp"] = otp
                request.session["email"] = email
                body = f"Please use the verification code below on the Doshi website: \n Your otp is {otp} \n If you didn't request this, you can ignore this email or let us know."
                EmailThread("OTP Verification", body, email).start()
                messages.success(request, "OTP sent successfully on this email id")
                return render(
                    request, "doshi/verify-otp.html", {"otp": otp, "email": email}
                )
            else:
                raise Exception("You are not allowed to access the portal")
        except User.DoesNotExist:
            messages.error(request, "User does not exists")
            return redirect("forgot-password")
        except Exception as e:
            messages.error(request, e)
            return redirect("forgot-password")

    return render(request, "doshi/forgot-password.html")


def verify_otp(request):
    if request.method == "POST":
        try:
            verify_otp = request.POST["verifyOTP"]
            if "otp" in request.session:
                if int(verify_otp) == int(request.session["otp"]):
                    messages.success(request, "OTP verification successful")
                    del request.session["otp"]
                    request.session["r-p"] = "12345"
                    return redirect("reset-password")
                else:
                    raise Exception("Invalid OTP ")
        except Exception as e:
            messages.error(request, e)
            return redirect("verify-otp")

    if "otp" in request.session:
        return render(request, "doshi/verify-otp.html")
    else:
        return redirect("login")


def reset_password(request):
    if request.method == "POST":
        password = request.POST["newPassword"]
        get_user = User.objects.get(email=request.session["email"])

        get_user.password = make_password(password)
        get_user.save()
        del request.session["r-p"]
        return redirect("login")

    if "r-p" in request.session:
        return render(request, "doshi/reset-password.html")
    else:
        return redirect("login")


def sku_items(request):
    try:
        if "id" in request.session:
            role = request.session["role"]
            if role == "CLIENT_HCH":
                sku_list = SKUItems.objects.filter(sku_name__contains="HCH")
            else:
                sku_list = SKUItems.objects.all()  # remove

            return render(request, "doshi/sku-list.html", {"sku_list": sku_list})
        else:
            return redirect("login")
    except Exception as e:
        return redirect("index")


def invoice_status(invoice_no):
    status = "PENDING"
    all_obj = Invoice.objects.filter(
        invoice_no=invoice_no, invoice_item_scanned_status="PENDING"
    )
    extra_obj = Invoice.objects.filter(
        invoice_no=invoice_no, invoice_item_scanned_status="EXTRA"
    )
    if all_obj.exists():
        status = "PENDING"
    elif extra_obj.exists():
        status = "EXTRA"
    else:
        status = "COMPLETED"

    return status


def get_all_invoices(request):
    if "id" in request.session:
        role = request.session["role"]
        if role in ["CLIENT_HCH", "CLIENT"]:
            return redirect("sku-items")
        else:

            invoices = (
                Invoice.objects.all()
                .values(
                    "invoice_no",
                    "invoice_party_name",
                    "invoice_date",
                    "invoice_total_amount",
                )
                .distinct()
            )

            get_all_status = [invoice_status(i["invoice_no"]) for i in invoices]
            bypass_data = zip(invoices, get_all_status)
            return render(
                request,
                "doshi/all-invoices.html",
                {"invoices": bypass_data, "get_all_status": get_all_status},
            )

    return redirect("login")


def invoices(request):
    if "id" in request.session:
        role = request.session["role"]
        if role in ["CLIENT_HCH", "CLIENT"]:
            return redirect("sku-items")
        else:
            invoices = (
                Invoice.objects.filter(
                    invoice_item_scanned_status__in=["PENDING", "EXTRA"]
                )
                .values(
                    "invoice_no",
                    "invoice_party_name",
                    "invoice_date",
                    "invoice_total_amount",
                )
                .distinct()
            )

            return render(request, "doshi/invoices.html", {"invoices": invoices})

    return redirect("login")


def invoice_details(request, invoice_no):
    if "id" in request.session:
        role = request.session["role"]
        if role in ["CLIENT_HCH", "CLIENT"]:
            return redirect("sku-items")
        else:

            invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no))
            invoice_details = invoice_sku_list[0]

            invoice_barcode_list = [i.invoice_item_id for i in invoice_sku_list]

            serial_numbers = SKUItems.objects.filter(
                id__in=invoice_barcode_list
            ).values("sku_name", "sku_serial_no")

            invoice_sku = zip(invoice_sku_list, serial_numbers)

        return render(
            request,
            "doshi/invoice-details.html",
            {"invoice_sku_list": invoice_sku, "invoice_details": invoice_details},
        )


def bypass_products(request):

    if "id" in request.session:
        role = request.session["role"]
        if role in ["CLIENT_HCH", "CLIENT"]:
            return redirect("sku-items")
        else:
            get_bypass_list = ByPassModel.objects.all()
            return render(
                request, "doshi/bypass-products.html", {"bypass_list": get_bypass_list}
            )

    return redirect("login")


def invoice_verify(request, invoice_no):

    invoice_sku_list = Invoice.objects.filter(invoice_no=str(invoice_no))

    invoice_pending_sku_list = Invoice.objects.filter(
        invoice_no=invoice_no, invoice_item_scanned_status="PENDING"
    )

    pending_invoice_barcode_list = [i.invoice_item_id for i in invoice_pending_sku_list]
    pending_sku_names = SKUItems.objects.filter(
        id__in=pending_invoice_barcode_list
    ).values("sku_name", "sku_serial_no")

    invoice_barcode_list = [i.invoice_item_id for i in invoice_sku_list]

    serial_numbers = SKUItems.objects.filter(id__in=invoice_barcode_list).values(
        "sku_name", "sku_serial_no"
    )

    request.session["invoice_barcode_list"] = invoice_barcode_list

    invoice_sku = zip(invoice_sku_list, serial_numbers)

    if "id" in request.session and invoice_sku_list.count() > 0:
        role = request.session["role"]
        if role in ["CLIENT_HCH", "CLIENT"]:
            return redirect("sku-items")
        else:
            return render(
                request,
                "doshi/invoice-verify.html",
                {
                    "invoice_sku_list": invoice_sku,
                    "invoice_no": invoice_no,
                    "invoice_pending_sku_list": invoice_pending_sku_list,
                    "pending_sku_names": pending_sku_names,
                },
            )
    return redirect("invoices")


def verify_invoice(request):

    if request.method == "POST":

        try:
            invoice_no = request.POST["invoice"]

            check_invoice = Invoice.objects.filter(
                invoice_no=invoice_no,
                invoice_item_scanned_status__in=["PENDING", "EXTRA"],
            )
            if not check_invoice.exists():
                raise Exception("All S.K.U's scanning completed")

            get_sku = SKUItems.objects.get(sku_serial_no=request.POST["barcode"])

            get_invoice = Invoice.objects.filter(invoice_no=invoice_no)
            get_sku_id_list = [i.invoice_item_id for i in get_invoice]

            if get_sku.id in get_sku_id_list:

                get_invoice_item = Invoice.objects.filter(
                    invoice_no=invoice_no, invoice_item_id=get_sku.id
                )

                if get_invoice_item[0].invoice_item_scanned_status == "PENDING":
                    # get_invoice_item.update(invoice_item_total_scan = F("invoice_item_total_scan") + 1)
                    sample = (
                        get_invoice_item[0].invoice_item_total_scan
                        + get_sku.sku_base_qty
                    )
                    get_invoice_item.update(invoice_item_total_scan=sample)

                    if int(get_invoice_item[0].invoice_item_total_scan) == int(
                        get_invoice_item[0].invoice_item_qty
                    ):
                        get_invoice_item.update(
                            invoice_item_scanned_status="COMPLETED",
                            invoice_user=request.session["id"],
                        )

                    elif int(get_invoice_item[0].invoice_item_total_scan) > int(
                        get_invoice_item[0].invoice_item_qty
                    ):
                        get_invoice_item.update(
                            invoice_item_scanned_status="EXTRA",
                            invoice_user=request.session["id"],
                        )

                else:
                    raise Exception("S.K.U. scanning completed")

                return JsonResponse({"status": "success", "msg": "S.K.U. mapped"})

            else:
                if get_sku_id_list:
                    return JsonResponse(
                        {
                            "status": "warning",
                            "msg": "Do you want to continue with this product ?",
                            "sku-name": get_sku.sku_name,
                        }
                    )
                else:
                    raise Exception("S.K.U. scanning already completed")

        except SKUItems.DoesNotExist:
            return JsonResponse({"status": "error", "msg": "Barcode does not exist"})

        except Exception as ep:
            return JsonResponse({"status": "error", "msg": str(ep)})

    return redirect("invoices")


def bypass_invoice(request):

    if request.method == "POST":
        try:
            invoice_no = request.POST["invoice"]
            sku_name = request.POST["sku_name"]
            sku_against_name = request.POST["sku_against_name"]

            sku_against_name_obj = SKUItems.objects.get(sku_name=sku_against_name)

            sku_name_obj = SKUItems.objects.get(sku_name=sku_name)
            # sku_against_name_obj_id = Invoice.objects.filter(invoice_ite=sku_against_name)

            invoice_obj = Invoice.objects.filter(
                invoice_no=invoice_no, invoice_item_id=sku_against_name_obj
            )

            if invoice_obj[0].invoice_item_scanned_status == "PENDING":
                sample = (
                    invoice_obj[0].invoice_item_total_scan + sku_name_obj.sku_base_qty
                )
                invoice_obj.update(invoice_item_total_scan=sample)

                if int(invoice_obj[0].invoice_item_total_scan) == int(
                    invoice_obj[0].invoice_item_qty
                ):
                    invoice_obj.update(
                        invoice_item_scanned_status="COMPLETED",
                        invoice_user=request.session["id"],
                    )
                elif int(invoice_obj[0].invoice_item_total_scan) > int(
                    invoice_obj[0].invoice_item_qty
                ):
                    invoice_obj.update(
                        invoice_item_scanned_status="EXTRA",
                        invoice_user=request.session["id"],
                    )

                    # ByPassModel.objects.create(bypass_invoice_no=invoice_obj[0], bypass_sku_name=sku_name_obj, bypass_against_sku_name=sku_against_name_obj)
            else:
                raise Exception("S.K.U. scanning already completed")

            # sku_against_name_obj.save()

            ByPassModel.objects.create(
                bypass_invoice_no=invoice_obj[0],
                bypass_sku_name=sku_name_obj,
                bypass_against_sku_name=sku_against_name_obj,
                bypass_date=date.today(),
            )

            return JsonResponse({"status": "success", "msg": "record added"})

        except Exception as e:
            return JsonResponse(
                {"status": "error", "msg": "record not added", "issue": str(e)}
            )

    return redirect("invoices")


def generate_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename='Bypassbypass_data.csv'"

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
        bypass_sku_name = SKUItems.objects.get(id=each["bypass_sku_name_id"]).sku_name
        bypass_against_sku_name = SKUItems.objects.get(
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


def update_scan_qty(request):
    if "id" in request.session:
        try:
            if request.method == "POST":
                invoice_no = request.POST["invoice-no"]
                invoice_item_total_scan = request.POST["invoice-item-total-scan"]
                invoice_item_name = request.POST["invoice-item-name"]

                sku_id = SKUItems.objects.filter(sku_name=invoice_item_name)
                data = Invoice.objects.filter(
                    invoice_no=invoice_no, invoice_item_id=sku_id
                )
                print(data, sku_id, invoice_item_name, invoice_item_total_scan)
        except Exception as e:
            pass


def dispatch_invoice(request):
    if "id" in request.session:
        try:
            if request.is_ajax:
                invoice_no = request.GET.get("invoice_no", None)
                invoice_sku_list = Invoice.objects.filter(invoice_no=invoice_no)
                for item in invoice_sku_list:
                    item.invoice_item_scanned_status = "COMPLETED"
                    item.save()
                return JsonResponse(
                    {
                        "status": "success",
                        "msg": f"Invoice No.{invoice_no} dispatched successfully.",
                    }
                )
        except Exception as e:
            JsonResponse({"status": "error", "msg": e})


def update_sku(request):
    if "id" in request.session:
        try:
            if request.method == "POST":
                sku_id = request.POST["update-sku-id"]
                sku_name = request.POST["update-sku-name"]
                sku_base_qty = request.POST["update-sku-qty"]

                sku_item = SKUItems.objects.get(id=sku_id)
                sku_item.sku_name = sku_name
                sku_item.sku_base_qty = sku_base_qty
                sku_item.save()
                return redirect("sku-items")
        except Exception as e:
            return HttpResponse(e)
    return JsonResponse({"HEllo": "World"})
