from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_contact(value):
    value = str(value)
    if len(value) != 10:
        raise ValidationError(
            _("%(value)s  must contains 10 digits only"), params={"value": value}
        )
    else:
        return value


def validate_name(value):
    # TODO: Add regex validation for names /(^[a-zA-Z][a-zA-Z\s]{0,20}[a-zA-Z]$)/

    if len(value) < 2:
        raise ValidationError(
            _("Name must contains atleast 2 characters"), params={"value": value}
        )
    elif not value.isalpha():
        raise ValidationError(
            _("Name must contains alphabets only"), params={"value": value}
        )
    else:
        return value


def validate_otp(value):
    if not (value.isdigit() and len(value) == 6):
        raise Exception("OTP must be of length 6 and numeric.")
    return value
