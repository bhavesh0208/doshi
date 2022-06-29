from django import template
from app.models import Invoice

register = template.Library()

@register.simple_tag
def status(value):
    all_status = False
    data = Invoice.objects.filter(invoice_no=value, invoice_item_scanned_status__in=[False])
    if not data.exists():
        all_status = True
    return all_status

