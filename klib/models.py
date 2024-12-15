import datetime
import json
import logging
import requests

from datetime import date
from django.utils import timezone
from decimal import Decimal

from django.db.models import Sum
from djmoney.models.fields import CurrencyField, MoneyField
from djmoney.settings import CURRENCY_CHOICES
from django.utils.translation import gettext_lazy as _

from klib.document_generator import generate_act_document_journal, generate_act_document_not_periodicals, \
    generate_act_document_files, generate_act_document_depository
from klib.validators import validate_year, validate_edition_number, validate_number_of_copies, validate_vat_rate, \
    validate_contract_number, validate_bank_name, validate_bank_code
from kuser.constants import LIBRARY_TYPE
from kuser.models import Worker, AbstractUser, Reader
from main.models import DateTimeModel
from django.db import models, transaction

logger = logging.getLogger(__name__)

CURRENCY_TYPE_BYN = 'BYN'
CURRENCY_TYPE_BYN_NAME = 'Рубль РБ'
CURRENCY_TYPE_RUB = 'RUB'
CURRENCY_TYPE_RUB_NAME = 'Рубль РФ'
CURRENCY_TYPE = (
    (CURRENCY_TYPE_BYN, CURRENCY_TYPE_BYN_NAME),
    (CURRENCY_TYPE_RUB, CURRENCY_TYPE_RUB_NAME),
)


class Company(DateTimeModel):
    LEGAL_FORM_1 = 'ООО'
    LEGAL_FORM_2 = 'ОАО'
    LEGAL_FORM_3 = 'ИП'
    LEGAL_FORM_4 = 'УП'
    LEGAL_FORM_5 = 'ЗАО'
    LEGAL_FORM_6 = 'ОДО'
    LEGAL_FORM_7 = 'АО'
    LEGAL_FORM_8 = 'ГО'
    LEGAL_FORM_9 = 'ГП'
    LEGAL_FORM_10 = 'ГУ'
    LEGAL_FORM_11 = 'У'
    LEGAL_FORM_12 = 'УО'
    LEGAL_FORM_13 = 'ЧУП'
    LEGAL_FORM_14 = 'ЧП'
    LEGAL_FORM_15 = 'РУП'
    LEGAL_FORM_16 = 'Отсутствует'

    LEGAL_FORM_CHOICES = (
        (LEGAL_FORM_1, LEGAL_FORM_1),
        (LEGAL_FORM_2, LEGAL_FORM_2),
        (LEGAL_FORM_3, LEGAL_FORM_3),
        (LEGAL_FORM_4, LEGAL_FORM_4),
        (LEGAL_FORM_5, LEGAL_FORM_5),
        (LEGAL_FORM_6, LEGAL_FORM_6),
        (LEGAL_FORM_7, LEGAL_FORM_7),
        (LEGAL_FORM_8, LEGAL_FORM_8),
        (LEGAL_FORM_9, LEGAL_FORM_9),
        (LEGAL_FORM_10, LEGAL_FORM_10),
        (LEGAL_FORM_11, LEGAL_FORM_11),
        (LEGAL_FORM_12, LEGAL_FORM_12),
        (LEGAL_FORM_13, LEGAL_FORM_13),
        (LEGAL_FORM_14, LEGAL_FORM_14),
        (LEGAL_FORM_15, LEGAL_FORM_15),
        (LEGAL_FORM_16, LEGAL_FORM_16)
    )

    COUNTRY_1 = 'РБ'
    COUNTRY_2 = 'РФ'

    COUNTRY_CHOICES = (
        (COUNTRY_1, COUNTRY_1),
        (COUNTRY_2, COUNTRY_2)
    )

    legal_form = models.CharField(max_length=50, choices=LEGAL_FORM_CHOICES, default=COUNTRY_1,
                                  verbose_name=_('Legal form'))
    short_name = models.CharField(max_length=100, verbose_name=_('Short name'))
    official_name = models.CharField(max_length=150, verbose_name=_('Official name'))
    postal_code = models.CharField(max_length=6, verbose_name=_('Postal code'))
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default=COUNTRY_1,
                               verbose_name=_('Country'))
    address = models.CharField(max_length=100, verbose_name=_('Address'))
    taxpayer_number = models.CharField(max_length=15, unique=True, verbose_name=_('Taxpayer number'))
    phone_1 = models.CharField(max_length=15, verbose_name=_('Phone'))
    phone_2 = models.CharField(max_length=15, verbose_name=_('Phone 2'), blank=True, null=True)
    email = models.CharField(max_length=30, verbose_name=_('Email'), blank=True, null=True)
    bank_name = models.CharField(max_length=40, verbose_name=_('Bank name'), validators=[validate_bank_name])
    bank_code = models.CharField(max_length=9, verbose_name=_('Bank code'), validators=[validate_bank_code])

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')

    def __str__(self):
        return f'{self.legal_form} {self.short_name}'

    def save(self, *args, **kwargs):
        if self.legal_form and self.short_name:
            self.official_name = f'{self.legal_form} {self.short_name}'
        super(Company, self).save(*args, **kwargs)


class Edition(DateTimeModel):
    TYPE_PERIODICAL = 'PERIODICAL'
    TYPE_PERIODICAL_NAME = _('Periodical')
    TYPE_NON_PERIODICAL = 'NON_PERIODICAL'
    TYPE_NON_PERIODICAL_NAME = _('Non-periodical')

    TYPES = (
        (TYPE_PERIODICAL, TYPE_PERIODICAL_NAME),
        (TYPE_NON_PERIODICAL, TYPE_NON_PERIODICAL_NAME),
    )

    SUBTYPE_MAGAZINE = 'MAGAZINES'
    SUBTYPE_MAGAZINE_NAME = _('Magazines type name')
    SUBTYPE_NEWSPAPER = 'NEWSPAPERS'
    SUBTYPE_NEWSPAPER_NAME = _('Newspapers type name')

    PERIODICAL_SUBTYPES = (
        (SUBTYPE_MAGAZINE, SUBTYPE_MAGAZINE_NAME),
        (SUBTYPE_NEWSPAPER, SUBTYPE_NEWSPAPER_NAME),
    )

    SUBTYPE_BOOK = 'BOOK'
    SUBTYPE_BOOK_NAME = _('Book type name')
    SUBTYPE_BROCHURE = 'BROCHURE'
    SUBTYPE_BROCHURE_NAME = _('Brochure type name')
    SUBTYPE_STD = 'STD'
    SUBTYPE_STD_NAME = _('STD type name')
    SUBTYPE_INFORMATION_FLYER = 'INFORMATION_FLYER'
    SUBTYPE_INFORMATION_FLYER_NAME = _('Information Flyer type name')
    SUBTYPE_STD_CHANGES = 'STD_CHANGES'
    SUBTYPE_STD_CHANGES_NAME = _('STD changes type name')
    SUBTYPE_E_RESOURCE = 'E_RESOURCE'
    SUBTYPE_E_RESOURCE_NAME = _('E-resource type name')

    NON_PERIODICAL_SUBTYPES = (
        (SUBTYPE_BOOK, SUBTYPE_BOOK_NAME),
        (SUBTYPE_BROCHURE, SUBTYPE_BROCHURE_NAME),
        (SUBTYPE_STD, SUBTYPE_STD_NAME),
        (SUBTYPE_INFORMATION_FLYER, SUBTYPE_INFORMATION_FLYER_NAME),
        (SUBTYPE_STD_CHANGES, SUBTYPE_STD_CHANGES_NAME),
        (SUBTYPE_E_RESOURCE, SUBTYPE_E_RESOURCE_NAME)
    )

    SUBTYPES = PERIODICAL_SUBTYPES + NON_PERIODICAL_SUBTYPES

    edition_type = models.CharField(max_length=256, choices=TYPES, default=TYPE_PERIODICAL,
                                    verbose_name=_('Edition type'))
    edition_subtype = models.CharField(max_length=256, choices=SUBTYPES, default=SUBTYPE_MAGAZINE,
                                       verbose_name=_('Edition subtype'))
    title = models.CharField(null=False, blank=False, max_length=150,
                             verbose_name=_('Edition title'))
    note = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Note'))

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.edition_subtype in dict(self.PERIODICAL_SUBTYPES).keys():
            self.edition_type = self.TYPE_PERIODICAL
        else:
            self.edition_type = self.TYPE_NON_PERIODICAL

        super().save(*args, **kwargs)


# это
class BaseEdition(Edition):
    year = models.CharField(null=True, blank=True, max_length=4, verbose_name=_('Year'), validators=[validate_year])

    international_number = models.CharField(null=True, blank=True, max_length=25, verbose_name=_('ISBN'))
    index = models.CharField(null=True, blank=True, max_length=30, verbose_name=_('Index'))
    document_number = models.CharField(null=True, blank=True, max_length=30, verbose_name=_('Doc number'))
    responsibility_info = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Responsibility info'))
    parallel_title = models.CharField(null=True, blank=True, max_length=150, verbose_name=_('Parallel title'))
    designation = models.CharField(null=True, blank=True, max_length=40, verbose_name=_('Designation'))
    title_info = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Title info'))
    part_number = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Part number'))
    part_name = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Part name'))
    author = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Author'))
    place_of_publication = models.CharField(null=True, blank=True, max_length=100,
                                            verbose_name=_('Place of publication'))
    publisher = models.CharField(null=True, blank=True, max_length=40, verbose_name=_('Publisher'))

    series_title = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Series title'))
    edition_info = models.CharField(null=True, blank=True, max_length=40, verbose_name=_('Edition info'))
    volume = models.CharField(null=True, blank=True, max_length=15, verbose_name=_('Volume'))
    information_carrier = models.CharField(null=True, blank=True, max_length=15, verbose_name=_('Information carrier'))

    class Meta:
        verbose_name = _('Base edition')
        verbose_name_plural = _('Base editions')

    def __str__(self):
        return f'{self.title}'

    def check_copies_balance(self):
        fund_elements = BaseFundElement.objects.filter(edition=self)
        total_copies_received = fund_elements.count()
        missing_copies = self.number_of_copies - total_copies_received

        return {
            'edition': self,
            'total_copies_received': total_copies_received,
            'missing_copies': max(0, missing_copies),
        }


class PeriodicalEdition(Edition):
    year = models.CharField(max_length=4, verbose_name=_('Year'), validators=[validate_year])

    class Meta:
        verbose_name = _('Periodical edition')
        verbose_name_plural = _('Periodical editions')

    def save(self, *args, **kwargs):
        if self.id is None:
            super().save(*args, **kwargs)
            self.send_post_request('add')
        else:
            super().save(*args, **kwargs)
            self.send_post_request('index')

    def send_post_request(self, endpoint):
        url = f'http://belrw-search:8080/public/search/edition/{endpoint}/per{self.id}'
        data = {
            'id': self.id,
            'type': self.edition_type,
            'subtype': self.edition_subtype,
            'database': 'database 1',
            'title': self.title,
            'year': self.year,
            'note': self.note
        }
        try:
            response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending POST request: {e}")

    def delete(self, *args, **kwargs):
        url = f'http://belrw-search:8080/public/search/edition/delete/per{self.id}'
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending POST request: {e}")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title


class NonPeriodicalEdition(Edition):
    international_number = models.CharField(null=True, blank=True, max_length=25, verbose_name=_('ISBN'))
    index = models.CharField(null=True, blank=True, max_length=30, verbose_name=_('Index'))
    document_number = models.CharField(null=True, blank=True, max_length=30, verbose_name=_('Doc number'))
    responsibility_info = models.CharField(null=True, blank=True, max_length=100,
                                           verbose_name=_('Responsibility info'))
    parallel_title = models.CharField(null=True, blank=True, max_length=150,
                                      verbose_name=_('Parallel title'))
    designation = models.CharField(null=True, blank=True, max_length=40, verbose_name=_('Designation'))
    title_info = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Title info'))
    part_number = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Part number'))
    part_name = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Part name'))
    author = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Author'))
    place_of_publication = models.CharField(null=True, blank=True, max_length=100,
                                            verbose_name=_('Place of publication'))
    publisher = models.CharField(null=True, blank=True, max_length=40, verbose_name=_('Publisher'))
    date_of_publication = models.DateField(null=False, verbose_name=_('Date of publication'))
    series_title = models.CharField(null=True, blank=True, max_length=100, verbose_name=_('Series title'))
    edition_info = models.CharField(null=True, blank=True, max_length=40, verbose_name=_('Edition info'))
    volume = models.CharField(null=True, blank=True, max_length=15, verbose_name=_('Volume'))
    information_carrier = models.CharField(null=True, blank=True, max_length=15,
                                           verbose_name=_('Information carrier'))

    class Meta:
        verbose_name = _('Non-periodical edition')
        verbose_name_plural = _('Non-periodical editions')

    def save(self, *args, **kwargs):
        if self.id is None:
            super().save(*args, **kwargs)
            self.send_post_request('add')
        else:
            super().save(*args, **kwargs)
            self.send_post_request('index')

    def send_post_request(self, endpoint):
        url = f'http://belrw-search:8080/public/search/edition/{endpoint}/nop{self.id}'

        data = {
            'id': self.id,
            'type': self.edition_type,
            'subtype': self.edition_subtype,
            'database': 'database 1',
            'title': self.title,
            'note': self.note,
            'international_number': self.international_number,
            'index': self.index,
            'document_number': self.document_number,
            'responsibility_info': self.responsibility_info,
            'parallel_title': self.parallel_title,
            'designation': self.designation,
            'title_info': self.title_info,
            'part_number': self.part_number,
            'part_name': self.part_name,
            'author': self.author,
            'place_of_publication': self.place_of_publication,
            'publisher': self.publisher,
            'date_of_publication': self.date_of_publication.isoformat() if self.date_of_publication else None,
            'series_title': self.series_title,
            'edition_info': self.edition_info,
            'volume': self.volume,
            'information_carrier': self.information_carrier
        }

        try:
            response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending POST request: {e}")

    def delete(self, *args, **kwargs):
        url = f'http://belrw-search:8080/public/search/edition/delete/nop{self.id}'
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending POST request: {e}")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title


class AbstractOrder(DateTimeModel):
    BALANCE_TYPE_1 = 'Стоит на балансе'
    BALANCE_TYPE_2 = 'Не стоит на балансе'
    BALANCE_TYPE = (
        (BALANCE_TYPE_1.lower(), BALANCE_TYPE_1),
        (BALANCE_TYPE_2.lower(), BALANCE_TYPE_2)
    )

    ORDER_STATUS_DRAFT = 'DRAFT'
    ORDER_STATUS_DRAFT_NAME = 'Черновой'
    ORDER_STATUS_ACTIVE = 'ACTIVE'
    ORDER_STATUS_ACTIVE_NAME = 'Действующий'
    ORDER_STATUS_PARTIALLY_CLOSED = 'PARTIALLY_CLOSED'
    ORDER_STATUS_PARTIALLY_CLOSED_NAME = 'Частично закрыт'
    ORDER_STATUS_CLOSED = 'CLOSED'
    ORDER_STATUS_CLOSED_NAME = 'Закрыт'

    ORDER_STATUS = (
        (ORDER_STATUS_DRAFT, ORDER_STATUS_DRAFT_NAME),
        (ORDER_STATUS_ACTIVE, ORDER_STATUS_ACTIVE_NAME),
        (ORDER_STATUS_PARTIALLY_CLOSED, ORDER_STATUS_PARTIALLY_CLOSED_NAME),
        (ORDER_STATUS_CLOSED, ORDER_STATUS_CLOSED_NAME),
    )

    contract_number = models.CharField(null=True, blank=True, max_length=25, verbose_name=_('Contract number'),
                                       validators=[validate_contract_number])
    contract_date = models.DateField(null=True, blank=True, verbose_name=_('Contract date'))
    company = models.ForeignKey(null=True, blank=True, to=Company, on_delete=models.SET_NULL, verbose_name=_('Company'))
    balance_type = models.CharField(null=True, blank=True, max_length=20, choices=BALANCE_TYPE, default=BALANCE_TYPE_1,
                                    verbose_name=_('Balance'))
    status = models.CharField(max_length=100, choices=ORDER_STATUS, default=ORDER_STATUS_ACTIVE,
                              verbose_name=_('Order status'))
    completion_date = models.DateField(null=True, blank=True, verbose_name=_('Completion date'))

    class Meta:
        abstract = True


class BaseOrder(AbstractOrder):
    PAYMENT_TYPE_CASH = 'CASH'
    PAYMENT_TYPE_CASH_NAME = 'Наличные'
    PAYMENT_TYPE_ACCOUNT = 'ACCOUNT'
    PAYMENT_TYPE_ACCOUNT_NAME = 'Безналично'
    PAYMENT_TYPE_INADVANCE = 'INADVANCE'
    PAYMENT_TYPE_INADVANCE_NAME = 'Предварительный'
    PAYMENT_TYPE_GIFT = 'GIFT'
    PAYMENT_TYPE_GIFT_NAME = 'Дар'
    PAYMENT_TYPE_PRICELESS = 'PRICELESS'
    PAYMENT_TYPE_PRICELESS_NAME = 'Бесплатно'
    PAYMENT_TYPE = (
        (PAYMENT_TYPE_CASH, PAYMENT_TYPE_CASH_NAME),
        (PAYMENT_TYPE_ACCOUNT, PAYMENT_TYPE_ACCOUNT_NAME),
        (PAYMENT_TYPE_INADVANCE, PAYMENT_TYPE_INADVANCE_NAME),
        (PAYMENT_TYPE_GIFT, PAYMENT_TYPE_GIFT_NAME),
        (PAYMENT_TYPE_PRICELESS, PAYMENT_TYPE_PRICELESS_NAME),
    )

    edition_type = models.CharField(max_length=16, choices=Edition.TYPES, verbose_name=_('Edition type'))
    edition_subtype = models.CharField(max_length=16, verbose_name=_('Edition type'),
                                       choices=BaseEdition.PERIODICAL_SUBTYPES)
    edition = models.ForeignKey(null=True, blank=True, to=BaseEdition, related_name='edition_order',
                                on_delete=models.SET_NULL, verbose_name=_('Base edition'))
    quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Quantity'))
    payment_type = models.CharField(max_length=16, choices=PAYMENT_TYPE, default=PAYMENT_TYPE_CASH,
                                    verbose_name=_('Payment type'))
    currency = models.CharField(max_length=16, choices=CURRENCY_TYPE, default=CURRENCY_TYPE_BYN,
                                verbose_name=_('Currency'))

    duration_of_receipt = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Duration of receipt"))
    first_number = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('First issue number'),
                                               validators=[validate_edition_number])
    last_number = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Last issue number'),
                                              validators=[validate_edition_number])
    number_of_copies = models.PositiveIntegerField(null=True, blank=True,
                                                   verbose_name=_('Number of copies of one issue'),
                                                   validators=[validate_number_of_copies])
    total_issue_numbers = models.PositiveIntegerField(null=True, blank=True,
                                                      verbose_name=_('Total number of issue numbers'))
    duration_of_storage = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Duration of storage"))
    price_per_instance = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2,
                                             verbose_name=_('Price per instance'))
    vat_rate = models.PositiveIntegerField(null=True, blank=True, default=20, verbose_name=_('Vat rate'),
                                           validators=[validate_vat_rate])
    total_price = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2,
                                      verbose_name=_('Total price'))
    price_per_instance_no_vat = models.DecimalField(
        null=True, blank=True, max_digits=10, decimal_places=2, verbose_name=_('Price per instance without VAT'))
    vat_per_instance = models.DecimalField(
        null=True, blank=True, max_digits=10, decimal_places=2, verbose_name=_('VAT per instance'))
    total_price_no_vat = models.DecimalField(
        null=True, blank=True, max_digits=10, decimal_places=2, verbose_name=_('Total price without VAT'))
    total_price_with_vat = models.DecimalField(
        null=True, blank=True, max_digits=10, decimal_places=2, verbose_name=_('Total price with VAT'))
    total_vat = models.DecimalField(
        null=True, blank=True, max_digits=10, decimal_places=2, verbose_name=_('Total VAT'))
    addition_agreement = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Addition agreement'))
    agreement_date = models.DateField(null=True, blank=True, verbose_name=_('Agreement date'))
    subscription = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Filing'))
    library = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Library'), choices=LIBRARY_TYPE)
    year = models.CharField(max_length=4, verbose_name=_('Year'), validators=[validate_year])
    filing = models.IntegerField(null=True, blank=True,
                                 choices=[(year, year) for year in range(2005, datetime.date.today().year + 1)],
                                 verbose_name=_('Filing'))

    def get_total_price_no_vat(self):
        return (
            BaseOrderEdition.objects.filter(order=self).aggregate(
                total_price_no_vat=Sum('price_without_vat')
            )['total_price_no_vat'] or 0
            if self.edition_type == Edition.TYPE_NON_PERIODICAL
            else self.price_per_instance_no_vat * (self.total_issue_numbers or 0)
        )

    def get_total_price_with_vat(self):
        return BaseOrderEdition.objects.filter(order=self).aggregate(total_price_with_vat=Sum(
            'price_with_vat'))['total_price_with_vat'] or 0

    def get_total_vat(self):
        return (
            BaseOrderEdition.objects.filter(order=self).aggregate(
                total_price_no_vat=Sum('price_without_vat')
            )['total_price_no_vat'] or 0
            if self.edition_type == Edition.TYPE_NON_PERIODICAL
            else (self.vat_per_instance * self.total_issue_numbers if self.total_issue_numbers else 0)
        )

    def get_quantity_getted(self):
        return BaseArrival.objects.filter(order_edition__order=self).aggregate(total_qty=Sum('qty'))['total_qty'] or 0

    class Meta:
        app_label = 'klib'
        verbose_name = _('Заказ непериодики')
        verbose_name_plural = _('Заказы непериодики')

    def __str__(self):
        return f'{self.contract_number}'

    def __init__(self, *args, **kwargs):
        self.edition_type = Edition.TYPE_NON_PERIODICAL
        super().__init__(*args, **kwargs)


class BaseOrderFirstClass(BaseOrder):
    class Meta:
        proxy = True
        app_label = 'klib'
        verbose_name = _('Заказ непериодики')
        verbose_name_plural = _('Заказы непериодики')


class BasePeriodicalOrder(BaseOrder):
    class Meta:
        proxy = True
        verbose_name = _('Заказ периодики')
        verbose_name_plural = _('Заказы периодики')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edition_type = Edition.TYPE_PERIODICAL

    def save(self, *args, **kwargs):
        # if self.number_of_copies and self.price_per_instance_no_vat and self.vat_per_instance:
        #     self.total_price_no_vat = self.price_per_instance_no_vat * self.number_of_copies
        #     self.total_vat = self.vat_per_instance * self.number_of_copies
        #     self.total_price_with_vat = self.total_price_no_vat + self.total_vat

        super(BaseOrder, self).save(*args, **kwargs)

        amount = BaseArrival.objects.filter(order_edition__order=self).aggregate(total_qty=Sum('qty'))[
                     'total_qty'] or 0
        if self.total_issue_numbers <= amount:
            self.status = BaseOrder.ORDER_STATUS_CLOSED
            self.completion_date = timezone.now()

        super(BaseOrder, self).save(*args, **kwargs)


class BasePeriodicalOrderFirstClass(BasePeriodicalOrder):
    class Meta:
        proxy = True
        verbose_name = _('Заказ периодики')
        verbose_name_plural = _('Заказы периодики')


class BaseOrderEdition(DateTimeModel):
    BALANCE_TYPE_1 = 'Стоит на балансе'
    BALANCE_TYPE_2 = 'Не стоит на балансе'
    BALANCE_TYPE = (
        (BALANCE_TYPE_1.lower(), BALANCE_TYPE_1),
        (BALANCE_TYPE_2.lower(), BALANCE_TYPE_2)
    )

    order = models.ForeignKey(to=BaseOrder, related_name='order_ordereditions', on_delete=models.CASCADE,
                              verbose_name=_('Base order'))
    edition = models.ForeignKey(to=BaseEdition, related_name='edition_ordereditions', on_delete=models.CASCADE,
                                verbose_name=_('Base edition'))
    quantity = models.PositiveIntegerField(verbose_name=_('Quantity'))
    price_with_vat = models.DecimalField(null=True, max_digits=12, decimal_places=2, verbose_name=_('Price with vat'))
    price_without_vat = models.DecimalField(null=True, max_digits=12, decimal_places=2,
                                            verbose_name=_('Price without vat'))
    vat_rate = models.DecimalField(null=True, max_digits=12, decimal_places=2, verbose_name=_('Vat rate'))
    vat = models.DecimalField(null=True, max_digits=12, decimal_places=2, verbose_name=_('Vat'))
    balance_type = models.CharField(null=True, blank=True, max_length=20, choices=BALANCE_TYPE, default=BALANCE_TYPE_1,
                                    verbose_name=_('Balance'))

    class Meta:
        app_label = 'klib'

    def quantity_display(self):
        total_arrivals_qty = BaseArrival.objects.filter(order_edition=self).aggregate(total_qty=Sum('qty'))[
                                 'total_qty'] or 0
        return total_arrivals_qty

    def __str__(self):
        return f'Order {self.order.id} {self.edition.title}'


class PeriodicalOrder(AbstractOrder):
    duration_of_receipt = models.PositiveIntegerField(verbose_name="Duration of receipt")
    first_number = models.PositiveIntegerField(verbose_name=_('First issue number'),
                                               validators=[validate_edition_number])
    last_number = models.PositiveIntegerField(verbose_name=_('Last issue number'),
                                              validators=[validate_edition_number])
    number_of_copies = models.PositiveIntegerField(verbose_name=_('Number of copies of one issue'),
                                                   validators=[validate_number_of_copies])
    total_issue_numbers = models.PositiveIntegerField(verbose_name=_('Total number of issue numbers'))
    duration_of_storage = models.PositiveIntegerField(verbose_name="Duration of storage")
    price_per_instance = MoneyField(max_digits=10, decimal_places=2, default_currency='BYN',
                                    verbose_name=_('Price per instance'))
    vat_rate = models.PositiveIntegerField(default=20, verbose_name=_('Vat rate'), validators=[validate_vat_rate])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Total price'))
    addition_agreement = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Addition agreement'))
    agreement_date = models.DateField(null=True, blank=True, verbose_name=_('Agreement date'))

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.contract_number}'

    def save(self, *args, **kwargs):
        if self.last_number and self.first_number:
            self.total_issue_numbers = (self.last_number - self.first_number + 1) * self.number_of_copies
        if self.price_per_instance and self.vat_rate:
            self.total_price = self.price_per_instance.amount * self.total_issue_numbers
        super(PeriodicalOrder, self).save(*args, **kwargs)


class JournalOrder(PeriodicalOrder):
    edition = models.ForeignKey(null=True, to=PeriodicalEdition, related_name='journal_orders',
                                on_delete=models.SET_NULL,
                                verbose_name=_('Title of the publication'))

    class Meta:
        verbose_name = _('Journal order')
        verbose_name_plural = _('Journal orders')


class NewspaperOrder(PeriodicalOrder):
    edition = models.ForeignKey(null=True, to=PeriodicalEdition, related_name='newspaper_orders',
                                on_delete=models.SET_NULL,
                                verbose_name=_('Title of the publication'))
    bound_year = models.IntegerField(verbose_name=_('Bound year'), validators=[validate_year])

    class Meta:
        verbose_name = _('Newspaper order')
        verbose_name_plural = _('Newspaper orders')


class NonPeriodicalOrder(AbstractOrder):
    currency = CurrencyField(choices=CURRENCY_CHOICES, default='BYN', verbose_name=_('Currency'))
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Total order price'))
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Total order vat'))

    def __str__(self):
        return f'{self.contract_number}'

    class Meta:
        verbose_name = _('Non Periodical Order')
        verbose_name_plural = _('Non Periodical Orders')

    @transaction.atomic
    def save(self, *args, **kwargs):
        total_price = sum(
            element.price for element in self.non_periodical_orders.all()
        )
        self.total_price = total_price
        total_vat = sum(
            (Decimal(element.vat_rate) / Decimal(100)) * element.price for element in
            self.non_periodical_orders.all()
        )
        self.total_vat = total_vat
        super().save(*args, **kwargs)


class NonPeriodicalOrderElement(DateTimeModel):
    edition = models.ForeignKey(null=True, to=NonPeriodicalEdition, related_name='non_periodical_edition',
                                on_delete=models.SET_NULL, verbose_name=_('Title of the publication'))
    number_of_copies = models.PositiveIntegerField(verbose_name=_('Number of copies'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Total price'))
    order = models.ForeignKey(null=True, to=NonPeriodicalOrder, related_name='non_periodical_orders',
                              on_delete=models.SET_NULL, verbose_name=_('Order'))
    vat_rate = models.PositiveIntegerField(default=20, verbose_name=_('Vat rate'))

    class Meta:
        verbose_name = _('Edition')
        verbose_name_plural = _('Editions')

    def __str__(self):
        return self.edition.title

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        if order:
            order.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.order:
            self.order.save()


class BaseArrival(DateTimeModel):
    BALANCE_TYPE_1 = 'Стоит на балансе'
    BALANCE_TYPE_2 = 'Не стоит на балансе'
    BALANCE_TYPE = (
        (BALANCE_TYPE_1.lower(), BALANCE_TYPE_1),
        (BALANCE_TYPE_2.lower(), BALANCE_TYPE_2)
    )

    order_edition = models.ForeignKey(null=True, blank=True, to=BaseOrderEdition, related_name='non_periodical_edition',
                                      on_delete=models.SET_NULL, verbose_name=_('Order edition'))
    edition = models.ForeignKey(null=True, blank=True, to=BaseEdition, related_name='edition_arrival',
                                on_delete=models.SET_NULL, verbose_name=_('Edition'))
    qty = models.PositiveIntegerField(null=True, blank=False, default=1, verbose_name=_('Quantity'))
    amount = models.DecimalField(null=True, blank=False, max_digits=12, decimal_places=2, verbose_name=_('Amount'))
    amount_with_vat = models.DecimalField(null=True, blank=False, max_digits=12, decimal_places=2,
                                          verbose_name=_('Amount with vat'))
    amount_vat = models.DecimalField(null=True, blank=False, max_digits=12, decimal_places=2,
                                     verbose_name=_('Vat amount'))
    invoice_number = models.CharField(null=True, blank=False, max_length=64, verbose_name=_('Invoice number'))
    invoice_date = models.DateField(null=True, blank=False, verbose_name=_('Invoice date'))

    double_number = models.BooleanField(null=False, blank=False, default=False, verbose_name=_('Double number'))
    edition_number = models.PositiveIntegerField(null=True, blank=False, verbose_name=_('Edition Number'))
    second_edition_number = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Second Edition Number'))
    library = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Library'))
    filing = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Filing'))
    balance_type = models.CharField(null=True, blank=True, max_length=20, choices=BALANCE_TYPE, default=BALANCE_TYPE_1,
                                    verbose_name=_('Balance'))
    company = models.ForeignKey(null=True, blank=True, to=Company, on_delete=models.SET_NULL, verbose_name=_('Company'))

    class Meta:
        verbose_name = _('Arrival')
        verbose_name_plural = _('Arrivals')

    def __str__(self):
        return f'{self.invoice_number}'

    def save(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        if not self.library and request:
            worker = Worker.objects.filter(user=request.user).first()
            if worker:
                self.library = worker.library
            else:
                reader = Reader.objects.filter(user=request.user).first()
                if reader:
                    self.library = reader.library

        super().save(*args, **kwargs)

        if self.order_edition:
            order = self.order_edition.order
            total_arrivals_qty = BaseArrival.objects.filter(order_edition__order=order).aggregate(total_qty=Sum('qty'))[
                                     'total_qty'] or 0
            if order.quantity is not None and total_arrivals_qty >= order.quantity:
                order.status = BaseOrder.ORDER_STATUS_CLOSED
                order.completion_date = timezone.now()
                order.save()


class ActiveFundElementManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(publication_status=BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF)


# Фонд все остальные
class BaseFundElement(DateTimeModel):
    BALANCE_TYPE_1 = 'Стоит на балансе'
    BALANCE_TYPE_2 = 'Не стоит на балансе'
    BALANCE_TYPE = (
        (BALANCE_TYPE_1.lower(), BALANCE_TYPE_1),
        (BALANCE_TYPE_2.lower(), BALANCE_TYPE_2)
    )

    SUBTYPE_MAGAZINE = 'MAGAZINES'
    SUBTYPE_MAGAZINE_NAME = _('Magazines type name')
    SUBTYPE_NEWSPAPER = 'NEWSPAPERS'
    SUBTYPE_NEWSPAPER_NAME = _('Newspapers type name')

    PERIODICAL_SUBTYPES = (
        (SUBTYPE_MAGAZINE, SUBTYPE_MAGAZINE_NAME),
        (SUBTYPE_NEWSPAPER, SUBTYPE_NEWSPAPER_NAME),
    )

    SUBTYPE_BOOK = 'BOOK'
    SUBTYPE_BOOK_NAME = _('Book type name')
    SUBTYPE_BROCHURE = 'BROCHURE'
    SUBTYPE_BROCHURE_NAME = _('Brochure type name')
    SUBTYPE_STD = 'STD'
    SUBTYPE_STD_NAME = _('STD type name')
    SUBTYPE_INFORMATION_FLYER = 'INFORMATION_FLYER'
    SUBTYPE_INFORMATION_FLYER_NAME = _('Information Flyer type name')
    SUBTYPE_STD_CHANGES = 'STD_CHANGES'
    SUBTYPE_STD_CHANGES_NAME = _('STD changes type name')
    SUBTYPE_E_RESOURCE = 'E_RESOURCE'
    SUBTYPE_E_RESOURCE_NAME = _('E-resource type name')

    NON_PERIODICAL_SUBTYPES = (
        (SUBTYPE_BOOK, SUBTYPE_BOOK_NAME),
        (SUBTYPE_BROCHURE, SUBTYPE_BROCHURE_NAME),
        (SUBTYPE_STD, SUBTYPE_STD_NAME),
        (SUBTYPE_INFORMATION_FLYER, SUBTYPE_INFORMATION_FLYER_NAME),
        (SUBTYPE_STD_CHANGES, SUBTYPE_STD_CHANGES_NAME),
        (SUBTYPE_E_RESOURCE, SUBTYPE_E_RESOURCE_NAME)
    )

    TYPES = PERIODICAL_SUBTYPES + NON_PERIODICAL_SUBTYPES

    PUBLICATION_STATUS_WRITTEN_OFF = 'WRITTEN_OFF'
    PUBLICATION_STATUS_WRITTEN_OFF_NAME = 'Исключен'
    PUBLICATION_STATUS_NOT_WRITTEN_OFF = 'NOT_WRITTEN_OFF'
    PUBLICATION_STATUS_NOT_WRITTEN_OFF_NAME = 'В фонде'
    PUBLICATION_STATUS_DEPOSITORY = 'IN_THE_DEPOSITORY_FUND'
    PUBLICATION_STATUS_DEPOSITORY_NAME = 'В депозитарном фонде'
    PUBLICATION_STATUS_REPLACEABLE = 'REPLACEABLE'
    PUBLICATION_STATUS_REPLACEABLE_NAME = 'Замененное издание (неподтвержденное)'
    PUBLICATION_STATUS_REPLACING = 'REPLACING'
    PUBLICATION_STATUS_REPLACING_NAME = 'Заменившее издание (неподтвержденное)'

    STATUS = (
        (PUBLICATION_STATUS_WRITTEN_OFF, PUBLICATION_STATUS_WRITTEN_OFF_NAME),
        (PUBLICATION_STATUS_NOT_WRITTEN_OFF, PUBLICATION_STATUS_NOT_WRITTEN_OFF_NAME),
        (PUBLICATION_STATUS_DEPOSITORY, PUBLICATION_STATUS_DEPOSITORY_NAME),
        (PUBLICATION_STATUS_REPLACEABLE, PUBLICATION_STATUS_REPLACEABLE_NAME),
        (PUBLICATION_STATUS_REPLACING, PUBLICATION_STATUS_REPLACING_NAME),
    )
    objects = models.Manager()
    active = ActiveFundElementManager()
    library = models.CharField(max_length=75, choices=LIBRARY_TYPE, verbose_name=_('Library'), null=True)
    arrival = models.ForeignKey(null=True, to=BaseArrival, related_name='arrival_found',
                                on_delete=models.SET_NULL, verbose_name=_('Arrival'))
    edition = models.ForeignKey(null=True, blank=False, to=BaseEdition, on_delete=models.CASCADE,
                                verbose_name=_('Edition'))
    inventory_number = models.CharField(null=True, max_length=64, verbose_name=_('Inventory number'))
    price = models.DecimalField(null=True, max_digits=12, decimal_places=2, verbose_name=_('Price'))
    price_with_vat = models.DecimalField(null=True, max_digits=12, decimal_places=2, verbose_name=_('Price with vat'))
    vat_amount = models.DecimalField(null=True, max_digits=12, decimal_places=2, verbose_name=_('Vat amount'))
    registration_date = models.DateField(null=True, verbose_name=_('Invoice date'))
    invoice_number = models.CharField(null=True, max_length=64, verbose_name=_('Invoice number'))
    invoice_date = models.DateField(null=True, verbose_name=_('Invoice date'))
    publication_status = models.CharField(max_length=100, choices=STATUS, default=PUBLICATION_STATUS_NOT_WRITTEN_OFF,
                                          verbose_name=_('Order status'))
    is_booked = models.BooleanField(null=False, blank=False, default=False, verbose_name=_('Is Booked'))
    subscription = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Filing'))
    balance_type = models.CharField(null=True, blank=True, max_length=20, choices=BALANCE_TYPE, default=BALANCE_TYPE_1,
                                    verbose_name=_('Balance'))

    # def save(self, *args, **kwargs):
    #     user = kwargs.pop('user', None)
    #     if self.arrival:
    #         self.library = self.arrival.library
    #     else:
    #         reader = Reader.objects.filter(user=user).first()
    #         if user:
    #             self.library = reader.library
    #         else:
    #             self.library = ''
    #     logger.debug(f'{self.library}')
    #     super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Fund element')
        verbose_name_plural = _('Fund')

    def __str__(self):
        return self.inventory_number if self.inventory_number else f'Element {self.id}'

    def get_edition(self):
        return self.arrival.order_edition.edition


# фонд для первого класса
class BaseFundElementFirstClass(BaseFundElement):
    class Meta:
        proxy = True
        verbose_name = _('Fund element')
        verbose_name_plural = _('Fund')


# Фонд газеты
class BaseFundElementNewspapers(BaseFundElement):
    class Meta:
        proxy = True
        verbose_name = _('Фонд газеты')
        verbose_name_plural = _('Фонд газет')


class BaseFundElementNewspapersFirstClass(BaseFundElement):
    class Meta:
        proxy = True
        verbose_name = _('Фонд газеты')
        verbose_name_plural = _('Фонд газет')


# Фонд журналы
class BaseFundElementMagazines(BaseFundElement):
    class Meta:
        proxy = True
        verbose_name = _('Фонд журналы')
        verbose_name_plural = _('Фонд журналов')


# Фонд журналы для первого класса
class BaseFundElementMagazinesFirstClass(BaseFundElement):
    class Meta:
        proxy = True
        verbose_name = _('Фонд журналы')
        verbose_name_plural = _('Фонд журналов')


class WriteOffAct(DateTimeModel):
    act_number = models.CharField(max_length=20, blank=True, verbose_name=_('Act number'))
    act_date = models.DateField(default=date.today, verbose_name=_('Act date'))
    basis_for_write_off = models.CharField(max_length=255, verbose_name=_('The basis of the write-off'))
    total_excluded = models.PositiveIntegerField(default=0, editable=False,
                                                 verbose_name=_('Total excluded from the fund'))
    socio_economic_count = models.PositiveIntegerField(default=0, verbose_name=_('Socio-economic'))
    technical_count = models.PositiveIntegerField(default=0, verbose_name=_('Technic'))
    other_count = models.PositiveIntegerField(default=0, verbose_name=_('Others'))
    railway_theme_count = models.PositiveIntegerField(default=0, verbose_name=_('On railway topics'))
    chairman = models.IntegerField(null=True, verbose_name=_('Chairman of the Commission'))
    vice_chairman = models.IntegerField(null=True, verbose_name=_('Deputy Chairman of the Commission'))
    member_1 = models.IntegerField(null=True, verbose_name=_('Member of the Commission 1'))
    member_2 = models.IntegerField(null=True, verbose_name=_('Member of the Commission 2'))
    member_3 = models.IntegerField(null=True, verbose_name=_('Member of the Commission 3'))
    submitted_by = models.IntegerField(verbose_name=_('I handed over the written-off documents(a)'))
    registered_by = models.IntegerField(verbose_name=_('The act was carried out in the book of total accounting'))

    class Meta:
        app_label = 'klib'
        abstract = True


class WriteOffActJournal(WriteOffAct):
    selected_elements_info = models.TextField(blank=True, null=True, verbose_name=_('Selected elements info'))
    inventory_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Inventory number'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_worker_name(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.full_name()
        except Worker.DoesNotExist:
            return "Не найден"

    def get_worker_position(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.position
        except Worker.DoesNotExist:
            return "Не найдена"

    def generate_act_document_journal(self):
        return generate_act_document_journal(self)

    class Meta:
        app_label = 'klib'
        verbose_name = _('The act of debiting')
        verbose_name_plural = _('Acts of write-off')


class WriteOffActNotPeriodicals(WriteOffAct):
    selected_elements_info = models.TextField(blank=True, null=True, verbose_name=_('Selected elements info'))
    inventory_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Inventory number'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_worker_name(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.full_name()
        except Worker.DoesNotExist:
            return "Не найден"

    def get_worker_position(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.position
        except Worker.DoesNotExist:
            return "Не найдена"

    def generate_act_document_not_periodicals(self):
        return generate_act_document_not_periodicals(self)

    class Meta:
        app_label = 'klib'
        verbose_name = _('Write off act not periodicals')
        verbose_name_plural = _('Write off act not periodicals')


class WriteOffActFiles(WriteOffAct):
    selected_elements_info = models.TextField(blank=True, null=True, verbose_name=_('Selected elements info'))
    inventory_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Inventory number'))
    subscription = models.CharField(null=True, blank=True, max_length=255, verbose_name=_('Filing'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_worker_name(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.full_name()
        except Worker.DoesNotExist:
            return "Не найден"

    def get_worker_position(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.position
        except Worker.DoesNotExist:
            return "Не найдена"

    def generate_act_document_files(self):
        return generate_act_document_files(self)

    class Meta:
        app_label = 'klib'
        verbose_name = _('Write off act files')
        verbose_name_plural = _('Write off act files')


class DigitalResource(DateTimeModel):
    SUBTYPE_BOOK = 'BOOK'
    SUBTYPE_BOOK_NAME = _('Book type name')
    SUBTYPE_ARTICLE = 'ARTICLE'
    SUBTYPE_ARTICLE_NAME = _('Article')
    SUBTYPE_STD = 'STD'
    SUBTYPE_STD_NAME = _('STD type name')
    SUBTYPE_INFORMATION_FLYER = 'INFORMATION_FLYER'
    SUBTYPE_INFORMATION_FLYER_NAME = _('Information Flyer type name')
    SUBTYPE_STD_CHANGES = 'STD_CHANGES'
    SUBTYPE_STD_CHANGES_NAME = _('STD changes type name')

    NON_PERIODICAL_SUBTYPES = (
        (SUBTYPE_BOOK, SUBTYPE_BOOK_NAME),
        (SUBTYPE_ARTICLE, SUBTYPE_ARTICLE_NAME),
        (SUBTYPE_STD, SUBTYPE_STD_NAME),
        (SUBTYPE_INFORMATION_FLYER, SUBTYPE_INFORMATION_FLYER_NAME),
        (SUBTYPE_STD_CHANGES, SUBTYPE_STD_CHANGES_NAME)
    )

    fund = models.OneToOneField(blank=True, null=True, unique=True, to=BaseFundElement, on_delete=models.SET_NULL,
                                related_name='fund_digital_resource', verbose_name=_('BaseFundElement'))
    resource = models.FileField(blank=False, null=False, max_length=256, upload_to="resources/",
                                verbose_name=_('Resource'))

    copyright = models.BooleanField(blank=False, null=False, default=False, verbose_name=_('Copyright'))
    type = models.CharField(choices=NON_PERIODICAL_SUBTYPES, default=SUBTYPE_BOOK, max_length=64,
                            verbose_name=_('Edition type'))
    title = models.CharField(null=True, blank=True, max_length=256, verbose_name=_('Title'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'klib'
        verbose_name = _('Digital resource')
        verbose_name_plural = _('Digital resources')


class OpenInventory(DateTimeModel):
    name = models.ForeignKey(to=BaseEdition, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('Name'))

    class Meta:
        app_label = 'klib'
        verbose_name = _('Open inventory')
        verbose_name_plural = _('Open inventorys')


class DepositoryFundElement(WriteOffAct):
    selected_elements_info = models.TextField(blank=True, null=True, verbose_name=_('Selected elements info'))
    inventory_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Inventory number'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_worker_name(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.full_name()
        except Worker.DoesNotExist:
            return "Не найден"

    def get_worker_position(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.position
        except Worker.DoesNotExist:
            return "Не найдена"

    def generate_act_document_depository(self):
        return generate_act_document_depository(self)

    def __str__(self):
        return f'{self.act_number} {self.inventory_number}'

    class Meta:
        app_label = 'klib'
        verbose_name = _('Depository fund element')
        verbose_name_plural = _('Depository fund element')


class ReplaceEdition(DateTimeModel):
    replaceable_edition = models.ForeignKey(
        BaseFundElement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replaceable_editions',
        verbose_name=_('Replaceable edition')
    )
    replacing_edition = models.ForeignKey(
        BaseEdition,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replacing_editions',
        verbose_name=_('Replacing edition')
    )
    replacing_fund_element = models.ForeignKey(
        BaseFundElement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replacing_fund_elements',
        verbose_name=_('Replacing fund element')
    )
    act = models.ForeignKey(
        'ReplacementAct',
        on_delete=models.CASCADE,
        related_name='elements',
        verbose_name=_('Replacement Act')
    )

    class Meta:
        verbose_name = _('Replace edition')
        verbose_name_plural = _('Replace editions')

    def replaceable_title(self):
        return self.replaceable_edition.edition.title if self.replaceable_edition else None

    def replacing_title(self):
        return self.replacing_edition.title if self.replacing_edition else None

    def __str__(self):
        return f'{self.replaceable_title()} -> {self.replacing_title()}'


class ReplacementAct(DateTimeModel):
    act_number = models.CharField(max_length=20, blank=True, verbose_name=_('Act number'))
    act_date = models.DateField(default=date.today, verbose_name=_('Act date'))
    total_excluded = models.PositiveIntegerField(default=0, editable=False,
                                                 verbose_name=_('Total excluded from the fund'))
    socio_economic_count = models.PositiveIntegerField(default=0, verbose_name=_('Socio-economic'))
    technical_count = models.PositiveIntegerField(default=0, verbose_name=_('Technic'))
    other_count = models.PositiveIntegerField(default=0, verbose_name=_('Others'))
    railway_theme_count = models.PositiveIntegerField(default=0, verbose_name=_('On railway topics'))
    chairman = models.IntegerField(null=True, verbose_name=_('Chairman of the Commission'))
    vice_chairman = models.IntegerField(null=True, verbose_name=_('Deputy Chairman of the Commission'))
    member_1 = models.IntegerField(null=True, verbose_name=_('Member of the Commission 1'))
    member_2 = models.IntegerField(null=True, verbose_name=_('Member of the Commission 2'))
    member_3 = models.IntegerField(null=True, verbose_name=_('Member of the Commission 3'))
    submitted_by = models.IntegerField(verbose_name=_('I handed over the written-off documents(a)'))
    registered_by = models.IntegerField(verbose_name=_('The act was carried out in the book of total accounting'))

    class Meta:
        verbose_name = _('Replacement Act')
        verbose_name_plural = _('Replacement Acts')

    def __str__(self):
        return f'Replacement Act {self.act_number}'

    def get_worker_name(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.full_name()
        except Worker.DoesNotExist:
            return "Не найден"

    def get_worker_position(self, worker_id):
        try:
            worker = Worker.objects.using('belrw-user-db').get(id=worker_id)
            return worker.position
        except Worker.DoesNotExist:
            return "Не найдена"

    def get_replace_editions(self):
        """
        Получить все замены изданий в акте
        Returns:
            QuerySet[ReplaceEdition]: QuerySet с заменами изданий
        """
        return ReplaceEdition.objects.filter(act=self)

    def add_replace_edition(self, replaceable_edition, replacing_edition):
        """
        Добавить замену издания в акт
        Args:
            replaceable_edition: BaseFundElement - заменяемое издание
            replacing_edition: BaseEdition - издание на замену
        """
        if isinstance(replaceable_edition, BaseFundElement) and isinstance(replacing_edition, BaseEdition):
            return ReplaceEdition.objects.create(
                act=self,
                replaceable_edition=replaceable_edition,
                replacing_edition=replacing_edition
            )

    def remove_replace_edition(self, replace_edition):
        """Удалить замену издания из акта"""
        if isinstance(replace_edition, ReplaceEdition):
            replace_edition.delete()

    def clear_replace_editions(self):
        """Удалить все замены изданий из акта"""
        self.elements.all().delete()

    def get_replace_editions_info(self):
        """Получить информацию о всех заменах изданий в акте"""
        editions = self.get_replace_editions()
        return [{
            'replaceable': {
                'inventory_number': edition.replaceable_edition.inventory_number if edition.replaceable_edition else None,
                'title': edition.replaceable_edition.edition.title if edition.replaceable_edition and edition.replaceable_edition.edition else None,
                'price': edition.replaceable_edition.price if edition.replaceable_edition else None
            },
            'replacing': {
                'title': edition.replacing_edition.title if edition.replacing_edition else None,
                'year': edition.replacing_edition.year if edition.replacing_edition else None
            }
        } for edition in editions]

    def get_replace_editions_count(self):
        """
        Получить количество замен в акте
        Returns:
            int: Количество замен изданий
        """
        return self.elements.count()


class ReplacementActReplace(ReplacementAct):
    class Meta:
        proxy = True
        verbose_name = _('Replacement Act Replace')
        verbose_name_plural = _('Replacement Acts Replace')
