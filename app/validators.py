from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_contact(value):
    value = str(value)
    if len(value) != 10:
        raise ValidationError(_('%(value)s  must contains 10 digits only'), params={'value': value})
    else:
        return value

def validate_name(value):
    if len(value) < 2:
        raise ValidationError(_('Name must contains atleast 2 characters'), params={'value': value})
    elif not value.isalpha():
        raise ValidationError(_('Name must contains alphabets only'), params={'value': value})
    else:
        return value


