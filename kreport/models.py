import datetime

from klib.models import Edition
from kreport.constans import TEMPLATE_TYPE_CHOICES, MONTH_CHOICES, YEAR_CHOICES, YEAR_CHOICES_N, MONTH_CHOICES_N, \
    LIBRARY_TYPE, BOOK_TYPE_CHOICES, REPORT_TYPE_CHOICES, DEBT_REPORT_TYPE_CHOICES, CIRC_REPORT_TYPE_CHOICES, \
    REPORT_CHOICES
from kreport.document_generator import MONTHS
from kuser.constants import EDUCATION_TYPE
from main.models import DateTimeModel
from django.db import models
from django.utils.translation import gettext_lazy as _


class CreateInventoryBook(DateTimeModel):
    template_type = models.CharField(choices=Edition.SUBTYPES, max_length=50, verbose_name=_('Template type'),
                                     default=Edition.SUBTYPE_BOOK)
    library = models.CharField(max_length=75, choices=LIBRARY_TYPE, verbose_name=_('Library'), null=True)
    first_inventory_number = models.IntegerField(verbose_name=_('First inventory number'), blank=True, null=True)
    last_inventory_number = models.IntegerField(verbose_name=_('Last inventory number'), blank=True, null=True)
    all_edition = models.BooleanField(verbose_name=_('All edition'))
    display_excluded_editions = models.BooleanField(verbose_name=_('Display excluded editions'))
    display_current_editions = models.BooleanField(verbose_name=_('Display current editions'))
    date_of_create = models.DateField(verbose_name=_('Date of create'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Create inventory book')
        verbose_name_plural = _('Create inventory books')


class CreateWorkplaceReport(DateTimeModel):
    organization = models.CharField(max_length=100, verbose_name=_('Organization'), null=True, blank=True)
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Position'))
    year = models.IntegerField(verbose_name="Год",
                               choices=[(year, year) for year in range(2005, datetime.date.today().year + 1)],
                               blank=True, null=True)
    add_excluded = models.BooleanField(verbose_name=_('Add excluded'), default=False)

    library = models.CharField(max_length=75, choices=LIBRARY_TYPE, verbose_name=_('Library'), null=True)

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Create workplace report')
        verbose_name_plural = _('Create workplace report')


class WorkplaceReportFirstClass(CreateWorkplaceReport):
    class Meta:
        proxy = True
        app_label = 'kreport'
        verbose_name = _('Create workplace report')
        verbose_name_plural = _('Create workplace report')


# Книга недополученных изданий
class BookIncompleteEdition(DateTimeModel):
    year = models.IntegerField(verbose_name="Год", choices=YEAR_CHOICES_N)
    moth = models.IntegerField(verbose_name="Месяц", choices=MONTH_CHOICES_N)

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Book incomplete edition')
        verbose_name_plural = _('Books incomplete editions')


class CreateEducationReport(DateTimeModel):
    education = models.CharField(max_length=30, choices=EDUCATION_TYPE, verbose_name=_('Education'), null=True,
                                 blank=True)
    year = models.IntegerField(verbose_name="Год",
                               choices=[(year, year) for year in range(2005, datetime.date.today().year + 1)],
                               blank=True, null=True)
    add_excluded = models.BooleanField(verbose_name=_('Add excluded'), default=False)

    library = models.CharField(max_length=75, choices=LIBRARY_TYPE, verbose_name=_('Library'), null=True)

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Create education report')
        verbose_name_plural = _('Create education report')


class CreateEducationReportFirstClass(CreateEducationReport):
    class Meta:
        proxy = True
        app_label = 'kreport'
        verbose_name = _('Create education report')
        verbose_name_plural = _('Create education report')


class TotalBook(DateTimeModel):
    book_type = models.CharField(choices=BOOK_TYPE_CHOICES, max_length=100, verbose_name=_('Book type'))
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))
    month = models.CharField(choices=MONTH_CHOICES, max_length=100, verbose_name=_('Month'))
    year = models.CharField(choices=YEAR_CHOICES, max_length=100, verbose_name=_('Year'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Total book')
        verbose_name_plural = _('Total books')


class UserAccounting(DateTimeModel):
    report_type = models.CharField(choices=REPORT_TYPE_CHOICES, max_length=64, verbose_name=_('Report type'))
    year = models.IntegerField(verbose_name="Год",
                               choices=[(year, year) for year in range(2005, datetime.date.today().year + 1)],
                               blank=True, null=True)
    month = models.IntegerField(choices=MONTHS, verbose_name=_('Month'), null=True, blank=True)
    day = models.IntegerField(verbose_name="День", blank=True, null=True)

    library = models.CharField(max_length=75, choices=LIBRARY_TYPE, verbose_name=_('Library'), null=True)

    class Meta:
        app_label = 'kreport'
        verbose_name = _('User accounting')
        verbose_name_plural = _('User accounting')


class UserAccountingFirstClass(UserAccounting):
    class Meta:
        proxy = True
        app_label = 'kreport'
        verbose_name = _('User accounting')
        verbose_name_plural = _('User accounting')


# Книга недополученных изданий (Непериодика)
class BookIncompleteEditionNonPeriodicals(DateTimeModel):
    month = models.CharField(choices=MONTH_CHOICES, max_length=100, verbose_name=_('Month'))
    year = models.CharField(choices=YEAR_CHOICES, max_length=100, verbose_name=_('Year'))
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Book incomplete edition non periodicals')
        verbose_name_plural = _('Books incomplete edition non periodicals')


# Бухгалтерской ведомость
class AccountiongStatement(DateTimeModel):
    month = models.CharField(choices=MONTH_CHOICES, max_length=100, verbose_name=_('Month'))
    year = models.CharField(choices=YEAR_CHOICES, max_length=100, verbose_name=_('Year'))
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Accountiong statement')
        verbose_name_plural = _('Аccounting statements')


# Акт приёмки периодики
class CertificateAcceptancePeriodicals(DateTimeModel):
    month = models.CharField(choices=MONTH_CHOICES, max_length=100, verbose_name=_('Month'))
    year = models.CharField(choices=YEAR_CHOICES, max_length=100, verbose_name=_('Year'))
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Certificate acceptance periodicals')
        verbose_name_plural = _('Certificate acceptance periodicals')


# Отчёт приёмки периодики
class PeriodicalsAcceptanceReport(DateTimeModel):
    month = models.CharField(choices=MONTH_CHOICES, max_length=100, verbose_name=_('Month'))
    year = models.CharField(choices=YEAR_CHOICES, max_length=100, verbose_name=_('Year'))
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Periodicals acceptance report')
        verbose_name_plural = _('Periodicals acceptance reports')


class CreateDebtorsReport(DateTimeModel):
    report_type = models.CharField(choices=DEBT_REPORT_TYPE_CHOICES, max_length=64, verbose_name=_('Report type'),
                                   null=False, blank=False)
    date = models.DateField(verbose_name=_('Date'), null=True, blank=True)
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))
    reader_id = models.IntegerField(null=True, verbose_name=_('Id number reader'), blank=True)

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Debtors report')
        verbose_name_plural = _('Debtors report')


class CreateDebtorsReportFirstClass(CreateDebtorsReport):
    class Meta:
        proxy = True
        app_label = 'kreport'
        verbose_name = _('Debtors report')
        verbose_name_plural = _('Debtors report')


class BookCirculationReport(DateTimeModel):
    report_type = models.CharField(choices=CIRC_REPORT_TYPE_CHOICES, max_length=64, verbose_name=_('Report type'),
                                   null=False, blank=False)
    year = models.IntegerField(verbose_name="Год",
                               choices=[(year, year) for year in range(2005, datetime.date.today().year + 1)],
                               blank=True, null=True)
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))
    reader_id = models.IntegerField(null=True, verbose_name=_('Id number reader'), blank=True)

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Book circulation report')
        verbose_name_plural = _('Book circulation report')


class BookCirculationReportFirstClass(BookCirculationReport):
    class Meta:
        proxy = True
        app_label = 'kreport'
        verbose_name = _('Book circulation report')
        verbose_name_plural = _('Book circulation report')


#  Отчёт Тип обслуживания
class TypeOfService(DateTimeModel):
    month = models.CharField(choices=MONTH_CHOICES, max_length=100, verbose_name=_('Month'))
    year = models.CharField(choices=YEAR_CHOICES, max_length=100, verbose_name=_('Year'))
    library = models.CharField(choices=LIBRARY_TYPE, max_length=100, verbose_name=_('Library'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Type of service')
        verbose_name_plural = _('Types of services')


# Отчёт по хранилищу
class StorageReport(DateTimeModel):
    month = models.CharField(choices=MONTH_CHOICES, max_length=100, verbose_name=_('Month'))
    year = models.CharField(choices=YEAR_CHOICES, max_length=100, verbose_name=_('Year'))
    type_of_report = models.CharField(choices=REPORT_CHOICES, max_length=100, verbose_name=_('Type of report'))

    class Meta:
        app_label = 'kreport'
        verbose_name = _('Storage report')
        verbose_name_plural = _('Storage reports')