import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_year(value):
    if len(str(value)) != 4:
        raise ValidationError(_('Invalid year error message'))


def validate_contract_number(value):
    if not re.match(r'^[A-Za-zА-Яа-я0-9/\-()]+$', value):
        raise ValidationError(_('Invalid contract number message'))

def validate_edition_number(value):
    if value < 0 or value > 9999:
        raise ValidationError(_('Invalid edition number error message'))

def validate_number_of_copies(value):
    if value < 0 or value > 100:
        raise ValidationError(_('Invalid number of copies error message'))

def validate_bank_code(value):
    if len(str(value)) > 9:
        raise ValidationError(_('Invalid bank code'))

def validate_taxpayer_number(value):
   if len(str(value)) < 0 or len(str(value)) > 15:
       raise ValidationError(_('Invalid taxpayer number'))

def validate_vat_rate(value):
    if value > 100:
        raise ValidationError(_('Invalid vat rate'))

def validate_bank_name(value):
    if not re.match(r'^[\w\s\.,\-\u0400-\u04FF]+$', value):
        raise ValidationError(
            _('The name of the bank can contain only Latin and Cyrillic letters, numbers and punctuation marks.')
        )

def validate_bank_code(value):
    if not re.match(r'^[A-Za-z0-9]+$', value):
        raise ValidationError(
            _('The bank code must contain only numbers and Latin letters.')
        )
