from django import template
from app.models import Invoice, Company

register = template.Library()


@register.simple_tag
def status(value):
    all_status = False
    print(value)
    data = Invoice.objects.filter(
        invoice_no=value, invoice_item_scanned_status__in=[False]
    )
    if not data.exists():
        all_status = True
    return all_status


@register.filter
def get_company_name(value):
    if value is None:
        return "-"
    else:
        company = Company.objects.filter(id=int(value))
        if company.exists():
            return company[0].company_name
        else:
            return "-"
