from django.utils.translation import gettext_lazy as _
from django.db import models

from main.models import DateTimeModel

CHOICE_ONE = 'Абонемент'
CHOICE_TWO = 'Читальный зал'
CHOICES = (
    (CHOICE_ONE.lower(), CHOICE_ONE),
    (CHOICE_TWO.lower(), CHOICE_TWO),
)


class Order(DateTimeModel):
    service_type = models.CharField(choices=CHOICES, max_length=64, verbose_name=_('Service type'))
    edition_name = models.CharField(max_length=256, verbose_name=_('Edition name'))
    count = models.IntegerField(verbose_name=_('Count'))

    class Meta:
        app_label = 'kfinder'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def __str__(self):
        return f'{self.service_type} - {self.edition_name}'