import datetime
import re
from decimal import Decimal, DecimalException

from django.contrib.admin import SimpleListFilter
from django.db.models import F, DateField, ExpressionWrapper, Value

import logging
import requests
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.db.models import Exists, OuterRef, Q, Sum
from django.utils.html import format_html, mark_safe

from kcatalog.enums.marker_values import SINGLE_ISSUE_MARKER
from kcatalog.forms import DigitalResourceForm
from klib.utils import get_user_library, is_exist_with_number
from kuser.constants import LIBRARY_TYPE, LIBRARY_FIRST
from kuser.models import AbstractUser, Worker, Reader
from kcatalog.models import Belmarc, Sku
from kcatalog.utils import create_belmarc_by_edition, unpublish_index_by_sku
from klib.document_generator import generate_act_document_files, \
    generate_act_document_not_periodicals, generate_act_document_journal, generate_act_document_depository, \
    generate_act_document_replacement
from klib.forms import JournalOrderForm, NewspaperOrderForm, NonPeriodicalOrderElementForm, ReplacementActForm, \
    WriteOffActForm, \
    WriteOffActFormTest, DepositoryFundElementForms
from klib.models import AbstractOrder, Company, BaseEdition, BaseOrder, BaseOrderEdition, PeriodicalEdition, \
    NonPeriodicalEdition, \
    NonPeriodicalOrder, JournalOrder, \
    NewspaperOrder, NonPeriodicalOrderElement, Edition, BaseArrival, BaseFundElement, ReplaceEdition, ReplacementAct, \
    ReplacementActReplace, WriteOffAct, WriteOffActJournal, \
    WriteOffActNotPeriodicals, WriteOffActFiles, BasePeriodicalOrder, BaseFundElementNewspapers, \
    BaseFundElementMagazines, DigitalResource, OpenInventory, DepositoryFundElement, \
    BaseFundElementMagazines, DigitalResource, OpenInventory, BaseFundElementNewspapersFirstClass, \
    BaseFundElementMagazinesFirstClass, BaseFundElementFirstClass, BaseOrderFirstClass, BasePeriodicalOrderFirstClass

from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.contrib import admin, messages
from django.shortcuts import redirect, render

from kuser.admin import my_admin_site

logger = logging.getLogger('main')


class LibraryFilter(admin.SimpleListFilter):
    title = 'Библиотека'
    parameter_name = 'library'

    def lookups(self, request, model_admin):
        return LIBRARY_TYPE

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(library=self.value())
        return queryset


class BaseFundElementInline(admin.StackedInline):
    model = BaseFundElement
    extra = 0
    readonly_fields = ['registration_date', 'inventory_number', 'price', 'price_with_vat', 'vat_amount',
                       'invoice_number', 'invoice_date']
    fields = ['registration_date', 'inventory_number', 'price', 'price_with_vat', 'vat_amount', 'invoice_number',
              'invoice_date']

    has_view_permission = lambda self, request, obj=None: True
    has_change_permission = lambda self, request, obj=None: request.user.has_perm('kservice.change_basearrival')
    has_add_permission = lambda self, request, obj=None: request.user.has_perm('kservice.add_basearrival')
    has_delete_permission = lambda self, request, obj=None: request.user.has_perm('kservice.delete_basearrival')

    def get_edition_subtype(self, obj):
        return obj.edition.edition_subtype

    get_edition_subtype.short_description = _('Edition type')


class NonPeriodicFilterDateOfPublication(admin.SimpleListFilter):
    title = _('Date of publication')
    parameter_name = 'date_of_publication'

    def lookups(self, request, model_admin):
        current_year = timezone.now().year
        return [(str(year), str(year)) for year in reversed(range(current_year - 500, current_year + 1))]

    def queryset(self, request, queryset):
        if self.value():
            try:
                url = (f'http://belrw-search:8080/public/search/edition/basic'
                       f'?pub_date_to={self.value()}-12-31'
                       f'&pub_date_from={self.value()}-01-01')
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()['elements']
                filtered_ids = [item['id'] for item in data]
                return queryset.filter(id__in=filtered_ids)
            except requests.exceptions.RequestException as e:
                print(f"Error filtering queryset: {e}")
                return queryset
        return queryset


class NonPeriodicalEditionFilterAuthor(admin.SimpleListFilter):
    title = _('Author')
    parameter_name = 'author'

    def lookups(self, request, model_admin):
        return [(str(author), str(author)) for author in
                NonPeriodicalEdition.objects.values_list('author', flat=True).distinct()]

    def queryset(self, request, queryset):
        if self.value():
            try:
                url = (f'http://belrw-search:8080/public/search/edition/basic'
                       f'?query={self.value()}'
                       f'&mode=match'
                       f'&field=author')
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()['elements']
                filtered_ids = [item['id'] for item in data]
                return queryset.filter(id__in=filtered_ids)
            except requests.exceptions.RequestException as e:
                print(f"Error filtering queryset: {e}")
                return queryset
        return queryset


class NonPeriodicalEditionFilterSubtype(admin.SimpleListFilter):
    title = _('Edition subtype')
    parameter_name = 'edition_subtype'

    def lookups(self, request, model_admin):
        return [(str(subtype[0]), str(subtype[1])) for subtype in Edition.NON_PERIODICAL_SUBTYPES]

    def queryset(self, request, queryset):
        if self.value():
            try:
                url = (f'http://belrw-search:8080/public/search/edition/basic'
                       f'?query={self.value()}'
                       f'&mode=term'
                       f'&field=subtype')
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()['elements']
                filtered_ids = [item['id'] for item in data]
                return queryset.filter(id__in=filtered_ids)
            except requests.exceptions.RequestException as e:
                print(f"Error filtering queryset: {e}")
                return queryset
        return queryset


class PublicationYearFilter(admin.SimpleListFilter):
    title = _('Publication year')
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        current_year = timezone.now().year
        return [(str(year), str(year)) for year in range(current_year - 500, current_year + 1)]

    def queryset(self, request, queryset):
        if self.value():
            year = self.value()
            return queryset.filter(date_of_publication__year=year)
        return queryset


class EditionTypeFilter(admin.SimpleListFilter):
    title = _('Edition type')
    parameter_name = 'edition_type'

    def lookups(self, request, model_admin):
        return [(str(type[0]), str(type[1])) for type in Edition.TYPES]

    def queryset(self, request, queryset):
        if self.value():
            try:
                url = (f'http://belrw-search:8080/public/search/edition/basic'
                       f'?query={self.value()}'
                       f'&mode=term'
                       f'&field=type')
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()['elements']
                filtered_ids = [item['id'] for item in data]
                return queryset.filter(id__in=filtered_ids)
            except requests.exceptions.RequestException as e:
                print(f"Error filtering queryset: {e}")
                return queryset
        return queryset


class EditionSubTypeFilter(admin.SimpleListFilter):
    title = _('Edition subtype')
    parameter_name = 'edition_subtype'

    def lookups(self, request, model_admin):
        return [(str(subtype[0]), str(subtype[1])) for subtype in Edition.SUBTYPES]

    def queryset(self, request, queryset):
        if self.value():
            try:
                url = (f'http://belrw-search:8080/public/search/edition/basic'
                       f'?query={self.value()}'
                       f'&mode=term'
                       f'&field=type')
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()['elements']
                filtered_ids = [item['id'] for item in data]
                return queryset.filter(id__in=filtered_ids)
            except requests.exceptions.RequestException as e:
                print(f"Error filtering queryset: {e}")
                return queryset
        return queryset


class BaseOrderInline(admin.TabularInline):
    model = BaseOrder
    fields = ['contract_number', 'contract_date', 'status', 'completion_date']
    readonly_fields = ['contract_number', 'contract_date', 'status', 'completion_date']
    extra = 0
    verbose_name = "Заказ"
    verbose_name_plural = "Заказы"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['taxpayer_number', 'official_name', 'short_name']
    readonly_fields = ['id', 'official_name']
    fields = ['legal_form', 'short_name', 'official_name', 'postal_code', 'country',
              'address', 'taxpayer_number', 'phone_1', 'phone_2', 'email', 'bank_name', 'bank_code']
    search_fields = ['short_name', 'official_name', 'taxpayer_number']
    inlines = [BaseOrderInline]


my_admin_site.register(Company, CompanyAdmin)


@admin.register(BaseEdition)
class BaseEditionAdmin(admin.ModelAdmin):
    list_display = ['title', 'edition_type', 'edition_subtype', 'author', 'year']
    readonly_fields = ['id']
    fieldsets = (
        (_('General'), {'fields': ('edition_type', 'edition_subtype', 'title', 'year', 'note')}),
        (_('Non-periodical edition'), {'fields': (
            'international_number', 'index',
            'document_number', 'responsibility_info',
            'parallel_title', 'designation',
            'title_info', 'part_number', 'part_name',
            'author', 'place_of_publication', 'publisher',
            'series_title', 'edition_info',
            'volume', 'information_carrier'
        )})
    )
    search_fields = ['title']
    list_filter = ['year', 'author', 'edition_subtype']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['edition_subtype'].choices = NonPeriodicalEdition.SUBTYPES
        return form

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if search_term:
            try:
                response = requests.get(f'http://belrw-search:8080/public/search/edition/basic'
                                        f'?types=NON_PERIODICAL'
                                        f'&query={search_term}'
                                        f'&mode=match'
                                        f'&field=title')
                if response.status_code == 200:
                    for elem in response.json()['elements']:
                        queryset |= NonPeriodicalEdition.objects.filter(pk=elem['id'])
            except requests.exceptions.RequestException as e:
                print(f"Error sending POST request: {e}")
            return queryset, False

        return super().get_search_results(request, queryset, search_term)

    def delete_queryset(self, request, queryset):
        for elem in queryset:
            elem.delete()
        queryset.delete()


my_admin_site.register(BaseEdition, BaseEditionAdmin)


@admin.register(PeriodicalEdition)
class PeriodicalEditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'edition_subtype', 'year']
    readonly_fields = ['id']
    fields = ['edition_subtype', 'title', 'year', 'note']
    search_fields = ['title']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['edition_subtype'].choices = NonPeriodicalEdition.PERIODICAL_SUBTYPES
        return form

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if search_term:
            try:
                response = requests.get(f'http://belrw-search:8080/public/search/edition/basic?types=PERIODICAL'
                                        f'&query={search_term}&mode=match&field=title')
                if response.status_code == 200:
                    for elem in response.json()['elements']:
                        queryset |= PeriodicalEdition.objects.filter(pk=elem['id'])
            except requests.exceptions.RequestException as e:
                print(f"Error sending POST request: {e}")
            return queryset, False

        return super().get_search_results(request, queryset, search_term)

    def delete_queryset(self, request, queryset):
        for elem in queryset:
            elem.delete()
        queryset.delete()


my_admin_site.register(PeriodicalEdition, PeriodicalEditionAdmin)


@admin.register(NonPeriodicalEdition)
class NonPeriodicalEditionAdmin(admin.ModelAdmin):
    list_display = ['title', 'edition_subtype', 'author', 'date_of_publication']
    readonly_fields = ['id']
    fields = ['edition_subtype', 'international_number', 'index',
              'document_number', 'responsibility_info',
              'title', 'parallel_title', 'designation',
              'title_info', 'part_number', 'part_name',
              'author', 'place_of_publication', 'publisher',
              'date_of_publication', 'series_title', 'edition_info',
              'volume', 'information_carrier', 'note']
    search_fields = ['title']
    list_filter = [NonPeriodicFilterDateOfPublication,
                   NonPeriodicalEditionFilterAuthor,
                   NonPeriodicalEditionFilterSubtype]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['edition_subtype'].choices = NonPeriodicalEdition.NON_PERIODICAL_SUBTYPES
        return form

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if search_term:
            try:
                response = requests.get(f'http://belrw-search:8080/public/search/edition/basic'
                                        f'?types=NON_PERIODICAL'
                                        f'&query={search_term}'
                                        f'&mode=match'
                                        f'&field=title')
                if response.status_code == 200:
                    for elem in response.json()['elements']:
                        queryset |= NonPeriodicalEdition.objects.filter(pk=elem['id'])
            except requests.exceptions.RequestException as e:
                print(f"Error sending POST request: {e}")
            return queryset, False

        return super().get_search_results(request, queryset, search_term)

    def delete_queryset(self, request, queryset):
        for elem in queryset:
            elem.delete()
        queryset.delete()


my_admin_site.register(NonPeriodicalEdition, NonPeriodicalEditionAdmin)


class BaseOrderEditionInline(admin.StackedInline):
    fields = ['edition', 'quantity', 'price_with_vat', 'price_without_vat', 'vat_rate', 'vat', 'balance_type',
              'register_button', ]
    readonly_fields = ['register_button', 'quantity_display']
    model = BaseOrderEdition
    extra = 0
    verbose_name = _('Base order edition name')
    verbose_name_plural = _('Base order editions names')

    def quantity_display(self, obj):
        return obj.quantity_display()

    quantity_display.short_description = _('Зарегестрировано')

    class Media:
        js = ('js/base_order_edition_inline_formulas.js',)

    has_view_permission = lambda self, request, obj=None: True
    has_change_permission = lambda self, request, obj=None: True
    has_add_permission = lambda self, request, obj=None: True
    has_delete_permission = lambda self, request, obj=None: True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "edition":
            kwargs["queryset"] = BaseEdition.objects.filter(edition_type=Edition.TYPE_NON_PERIODICAL)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def register_button(self, obj):
        if obj.pk and not (obj.quantity_display() >= obj.quantity) and obj.order.status != BaseOrder.ORDER_STATUS_DRAFT:
            logger.info(f'obj.id: {obj.order.id}')
            return format_html(
                '<a class="btn btn-success form-control" href="{}">Регистрация</a>',
                f'/admin/klib/baseorderfirstclass/register_edition/{obj.id}'
            )
        else:
            return ''

    register_button.short_description = 'Регистрация изданий'
    register_button.allow_tags = True


class BaseOrderAdmin(admin.ModelAdmin):
    list_display = ['status', 'contract_number', 'contract_date', 'company', 'completion_date']
    readonly_fields = ['id', 'edition_type',
                       'get_total_price_no_vat', 'get_total_price_with_vat', 'get_total_vat',
                       # 'total_price_no_vat', 'total_price_with_vat', 'total_vat',
                       ]
    list_filter = ['status', 'contract_number', 'contract_date', 'company', 'edition__title', 'completion_date']
    fieldsets = (
        (_('General'), {'fields': (
            'edition_type', 'company', 'payment_type', 'contract_number', 'contract_date')}),
        (_('The price of the order'), {
            'fields': (
                'currency',
                'get_total_price_no_vat',
                # 'price_per_instance_no_vat', 'vat_per_instance', 
                'get_total_price_with_vat', 'get_total_vat',
                # 'vat_rate'
            )
        })
    )

    agreement_fieldsets = (
        (_('Addition agreement'), {'fields': ('addition_agreement', 'agreement_date')}),
    )

    change_list_template = 'klib/base_order_list.html'
    change_form_template = 'klib/base_order.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['type'] = Edition.TYPE_NON_PERIODICAL
        return super().changelist_view(request, extra_context=extra_context)

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.fieldsets + self.agreement_fieldsets
        return self.fieldsets

    inlines = [BaseOrderEditionInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(edition_type=Edition.TYPE_NON_PERIODICAL)
        reader = Reader.objects.using('belrw-user-db').filter(user=request.user).first()
        user_library = getattr(reader, 'library', None)
        if user_library:
            queryset = queryset.filter(library=user_library)

        if 'status__exact' in request.GET and request.GET['status__exact'] == 'closed':
            return queryset
        return queryset.exclude(status='closed')

    def edition_name(self, obj):
        if obj.edition_type == Edition.TYPE_PERIODICAL:
            result = obj.edition.title if obj.edition else '-'
        else:
            ed = BaseOrderEdition.objects.filter(order=obj).first()
            result = ed.edition.title if ed else '-'
        return result

    edition_name.short_description = _('Title of the publication')

    def register_edition(self, request, id):
        order = self.get_object(request, id)
        if order:
            balance_type = order.balance_type
            # order_edition, created = BaseOrderEdition.objects.get_or_create(
            #     order=order,
            #     balance_type=balance_type,
            #     # edition=order.edition,
            #     # defaults={'quantity': order.quantity}
            # )
            order_edition = BaseOrderEdition.objects.get(order=order)
            logger.debug(f'{order_edition}')

            qty = order_edition.quantity - order_edition.quantity_display()
            arrival = BaseArrival.objects.create(order_edition=order_edition,
                                                 edition=order_edition.edition,
                                                 library=order_edition.order.library,
                                                 balance_type=order_edition.balance_type,
                                                 qty=qty,
                                                 amount=order_edition.price_without_vat / order_edition.quantity * qty,
                                                 amount_with_vat=order_edition.price_with_vat / order_edition.quantity * qty,
                                                 amount_vat=order_edition.vat / order_edition.quantity * qty
                                                 )
            belmarc = Belmarc.objects.filter(edition_id=order_edition.edition.id).first()
            if belmarc is None:
                create_belmarc_by_edition(edition=order.edition)
            return redirect(reverse('admin:klib_basearrival_change', args=(arrival.id,)))
        return HttpResponseNotFound('Order not found')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register_edition/<int:id>', self.admin_site.admin_view(self.register_edition),
                 name='register_edition')
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        if request.POST.get('save_draft') is not None:
            draft = True
            obj.status = AbstractOrder.ORDER_STATUS_DRAFT
        else:
            obj.status = AbstractOrder.ORDER_STATUS_ACTIVE

        if not change:
            obj.edition_type = Edition.TYPE_NON_PERIODICAL
            user = Reader.objects.using('belrw-user-db').filter(user=request.user).first()
            if user is None:
                user = Worker.objects.using('belrw-user-db').filter(user=request.user).first()
            if user:
                obj.library = user.library
            else:
                obj.library = ''
        super().save_model(request, obj, form, change)

    def get_total_price_no_vat(self, obj):
        try:
            if obj.edition_type == Edition.TYPE_NON_PERIODICAL:
                total = BaseOrderEdition.objects.filter(order=obj).aggregate(
                    total_price_no_vat=Sum('price_without_vat')
                )['total_price_no_vat']
                return total if total is not None else 0
            else:
                if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers:
                    return obj.price_per_instance_no_vat * obj.total_issue_numbers
                return 0
        except (TypeError, AttributeError):
            return 0

    def get_total_price_with_vat(self, obj):
        try:
            total_no_vat = self.get_total_price_no_vat(obj)
            total_vat = self.get_total_vat(obj)
            if total_no_vat is not None and total_vat is not None:
                return total_no_vat + total_vat
            return 0
        except (TypeError, AttributeError):
            return 0

    def get_total_vat(self, obj):
        try:
            if obj.edition_type == Edition.TYPE_NON_PERIODICAL:
                total = BaseOrderEdition.objects.filter(order=obj).aggregate(
                    total_vat=Sum('vat')
                )['total_vat']
                return total if total is not None else 0
            else:
                if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers and obj.vat_rate:
                    total_price = obj.price_per_instance_no_vat * obj.total_issue_numbers
                    return (total_price * obj.vat_rate) / 100
                return 0
        except (TypeError, AttributeError):
            return 0

    get_total_price_no_vat.short_description = _('Total price without VAT')
    get_total_price_with_vat.short_description = _('Total price with VAT')
    get_total_vat.short_description = _('Total VAT')


my_admin_site.register(BaseOrder, BaseOrderAdmin)


class BaseOrderFirstClassAdmin(admin.ModelAdmin):
    list_display = ['status', 'library', 'contract_number', 'contract_date', 'company']
    readonly_fields = ['id', 'edition_type',
                       'get_total_price_no_vat', 'get_total_price_with_vat', 'get_total_vat',
                       # 'total_price_no_vat', 'total_price_with_vat', 'total_vat',
                       ]
    # list_filter = ['status', 'contract_date', 'company', 'edition__title', 'completion_date', LibraryFilter]
    list_filter = ['status', 'contract_date', 'company', 'edition__title', 'completion_date', LibraryFilter]
    fieldsets = (
        (_('General'), {'fields': (
            'edition_type', 'company', 'payment_type', 'contract_number', 'contract_date',
            'balance_type')}),
        (_('The price of the order'), {
            'fields': (
                'currency',
                'get_total_price_no_vat',
                # 'price_per_instance_no_vat', 'vat_per_instance',
                'get_total_price_with_vat', 'get_total_vat',
                # 'vat_rate'
            )
        })
    )

    agreement_fieldsets = (
        (_('Addition agreement'), {'fields': ('addition_agreement', 'agreement_date')}),
    )

    change_list_template = 'klib/base_order_list.html'
    change_form_template = 'klib/base_order.html'

    # def get_changelist(self, request, **kwargs):
    #     ChangeList = super().get_changelist(request, **kwargs)
    #
    #     class DefaultLibraryChangeList(ChangeList):
    #         def get_filters_params(self, *args, **kwargs):
    #             params = super().get_filters_params(*args, **kwargs)
    #             if self.params.get('library') is None:
    #                 params['library'] = LIBRARY_FIRST
    #             return params
    #
    #     return DefaultLibraryChangeList


    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['type'] = Edition.TYPE_NON_PERIODICAL
        return super().changelist_view(request, extra_context=extra_context)

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.fieldsets + self.agreement_fieldsets
        return self.fieldsets

    inlines = [BaseOrderEditionInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(edition_type=Edition.TYPE_NON_PERIODICAL)

        if 'status__exact' in request.GET and request.GET['status__exact'] == 'closed':
            return queryset
        return queryset.exclude(status='closed')

    def edition_name(self, obj):
        if obj.edition_type == Edition.TYPE_PERIODICAL:
            result = obj.edition.title if obj.edition else '-'
        else:
            ed = BaseOrderEdition.objects.filter(order=obj).first()
            result = ed.edition.title if ed else '-'
        return result

    edition_name.short_description = _('Title of the publication')

    def register_edition(self, request, id):
        order_edition: BaseOrderEdition = BaseOrderEdition.objects.filter(pk=id).first()
        order: BaseOrder = order_edition.order
        if order and order_edition:
            qty = order_edition.quantity - order_edition.quantity_display()
            arrival = BaseArrival.objects.create(
                order_edition=order_edition,
                edition=order_edition.edition,
                balance_type=order_edition.balance_type,
                library=order_edition.order.library,
                qty=qty,
                amount=order_edition.price_without_vat / order_edition.quantity * qty,
                amount_with_vat=order_edition.price_with_vat / order_edition.quantity * qty,
                amount_vat=order_edition.vat / order_edition.quantity * qty
            )
            belmarc = Belmarc.objects.filter(edition_id=order_edition.edition.id).first()
            if belmarc is None:
                create_belmarc_by_edition(edition=order_edition.edition)
            editions = BaseOrderEdition.objects.filter(order=order)
            is_closed = True
            is_partly_closed = False
            for edition in editions:
                if edition.quantity_display() > 0:
                    is_partly_closed = True
                if edition.quantity_display() != edition.quantity:
                    is_closed = False
            if is_closed:
                order.status = BaseOrder.ORDER_STATUS_CLOSED
            elif is_partly_closed:
                order.status = BaseOrder.ORDER_STATUS_PARTIALLY_CLOSED
            order.save()
            return redirect(reverse('admin:klib_basearrival_change', args=(arrival.id,)))
        return HttpResponseNotFound('Order not found')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register_edition/<int:id>', self.admin_site.admin_view(self.register_edition),
                 name='register_edition')
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        if request.POST.get('save_draft') is not None:
            draft = True
            obj.status = AbstractOrder.ORDER_STATUS_DRAFT
        else:
            obj.status = AbstractOrder.ORDER_STATUS_ACTIVE
        if not change:
            obj.edition_type = Edition.TYPE_NON_PERIODICAL
        obj.library = get_user_library(request.user)
        super().save_model(request, obj, form, change)

    def get_total_price_no_vat(self, obj):
        try:
            if obj.edition_type == Edition.TYPE_NON_PERIODICAL:
                total = BaseOrderEdition.objects.filter(order=obj).aggregate(
                    total_price_no_vat=Sum('price_without_vat')
                )['total_price_no_vat']
                return total if total is not None else 0
            else:
                if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers:
                    return obj.price_per_instance_no_vat * obj.total_issue_numbers
                return 0
        except (TypeError, AttributeError):
            return 0

    def get_total_price_with_vat(self, obj):
        try:
            total_no_vat = self.get_total_price_no_vat(obj)
            total_vat = self.get_total_vat(obj)
            if total_no_vat is not None and total_vat is not None:
                return total_no_vat + total_vat
            return 0
        except (TypeError, AttributeError):
            return 0

    def get_total_vat(self, obj):
        try:
            if obj.edition_type == Edition.TYPE_NON_PERIODICAL:
                total = BaseOrderEdition.objects.filter(order=obj).aggregate(
                    total_vat=Sum('vat')
                )['total_vat']
                return total if total is not None else 0
            else:
                if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers and obj.vat_rate:
                    total_price = obj.price_per_instance_no_vat * obj.total_issue_numbers
                    return (total_price * obj.vat_rate) / 100
                return 0
        except (TypeError, AttributeError):
            return 0

    get_total_price_no_vat.short_description = _('Total price without VAT')
    get_total_price_with_vat.short_description = _('Total price with VAT')
    get_total_vat.short_description = _('Total VAT')


my_admin_site.register(BaseOrderFirstClass, BaseOrderFirstClassAdmin)


#Заказы периодики
@admin.register(BasePeriodicalOrder)
class BasePeriodicalOrderAdmin(admin.ModelAdmin):
    list_display = ['edition_name', 'year', 'status', 'contract_number', 'contract_date', 'company']
    readonly_fields = ['id', 'edition_type',
                       'get_total_price_no_vat', 'get_total_price_with_vat', 'get_total_vat']

    common_fieldsets = (
        (_('General'),
         {'fields': (
         'edition_subtype', 'edition', 'year', 'company', 'payment_type', 'currency', 'contract_number', 'contract_date',
         'duration_of_receipt', 'filing')}),
        (_('Periodical edition'),
         {'fields': ['first_number', 'last_number', 'number_of_copies', 'total_issue_numbers', 'duration_of_storage',
                     'balance_type']}),
        (_('The price of the order'),
         {'fields': (
         'price_per_instance_no_vat', 'vat_per_instance', 'total_price_no_vat', 'total_vat', 'total_price_with_vat',
         'vat_rate')}),

    )

    agreement_fieldsets = (
        (_('Addition agreement'), {'fields': ('addition_agreement', 'agreement_date')}),
    )

    def get_total_price_with_vat(self, obj):
        try:
            return obj.total_price + self.get_total_vat(obj)
        except (AttributeError, TypeError, ValueError):
            return Decimal(0)

    get_total_price_with_vat.short_description = 'Общая стоимость с НДС'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "edition":
            subtype = request.GET.get('edition_subtype')
            if subtype:
                kwargs["queryset"] = BaseEdition.objects.filter(edition_subtype=subtype)
            else:
                kwargs["queryset"] = BaseEdition.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.common_fieldsets)

        # if obj and obj.edition and obj.edition.edition_subtype == Edition.SUBTYPE_NEWSPAPER:
        #     fieldsets[1][1]['fields'] = [ 'first_number', 'last_number', 'number_of_copies', 'total_issue_numbers', 'duration_of_storage', 'subscription']
        # if obj:
        #     if obj.edition and obj.edition.edition_subtype == Edition.SUBTYPE_NEWSPAPER:
        #         fieldsets[2][1]['fields'] = [
        #             'edition', 'duration_of_receipt', 'first_number', 'last_number',
        #             'number_of_copies', 'total_issue_numbers', 'duration_of_storage',
        #             'subscription', 'balance_type'
        #         ]
        #     else:
        #         fieldsets[2][1]['fields'] = [
        #             'edition', 'duration_of_receipt', 'first_number', 'last_number',
        #             'number_of_copies', 'total_issue_numbers', 'duration_of_storage',
        #             'balance_type'
        #         ]
        #     return fieldsets + list(self.agreement_fieldsets)

        return fieldsets

    # inlines = [BaseOrderEditionInline]
    # def get_fieldsets(self, request, obj=None):
    #     if obj:
    #         return self.common_fieldsets + self.agreement_fieldsets
    #     return self.common_fieldsets

    # change_form_template = "admin/klib/baseperiodicalorder/change_form.html"

    list_filter = ['status', 'contract_number', 'contract_date', 'company', 'edition__title', 'completion_date']

    change_list_template = 'klib/base_order_list.html'
    change_form_template = 'klib/register_edition_admin.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['type'] = Edition.TYPE_PERIODICAL
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(edition_type=Edition.TYPE_PERIODICAL)
        user_library = get_user_library(request.user)
        if user_library:
            queryset = queryset.filter(library=user_library)

        if 'status__exact' in request.GET and request.GET['status__exact'] == 'closed':
            return queryset
        return queryset.exclude(status='closed')

    def edition_name(self, obj):
        if obj.edition_type == Edition.TYPE_PERIODICAL:
            result = obj.edition.title if obj.edition else '-'
        else:
            ed = BaseOrderEdition.objects.filter(order=obj).first()
            result = ed.edition.title if ed else '-'
        return result

    edition_name.short_description = _('Title of the publication')

    def edition_year(self, obj):
        return obj.edition.year if obj.edition else '-'

    edition_year.short_description = _('Год')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register_edition/<int:id>/', self.admin_site.admin_view(self.register_edition),
                 name='register_edition'),
        ]
        return custom_urls + urls

    # def custom_button(self, obj):
    #     if obj.pk:
    #         buttons_html = '<div class="submit-row" style="display: flex; flex-direction: column; gap: 10px; padding-top: 15px;">'

    #         # Добавляем кнопку "Регистрация", если статус не черновик
    #         if obj.status != AbstractOrder.ORDER_STATUS_DRAFT:
    #             buttons_html += '<a class="btn btn-success form-control" href="{}" style="margin-top: 14px;">Регистрация</a>'.format(
    #                 reverse('admin:register_edition', args=[obj.pk])
    #             )

    #     # Добавляем кнопку "Сохранить как черновик"
    #     buttons_html += '<a href="{}?draft=True">'.format(reverse('admin:register_edition', args=[obj.pk]))
    #     buttons_html += '<button type="submit" class="btn btn-success form-control" name="save_draft">'
    #     buttons_html += 'Сохранить как черновик'
    #     buttons_html += '</button></a></div>'

    #     return format_html(buttons_html)

    #     return ''

    # custom_button.short_description = 'Регистрация изданий'
    # custom_button.allow_tags = True

    def register_edition(self, request, id):
        order = self.get_object(request, id)
        if order:
            order_edition, created = BaseOrderEdition.objects.get_or_create(
                order=order,
                edition=order.edition,
                defaults={'quantity': order.quantity}
            )

            user = Worker.objects.get(user=request.user)
            logger.debug(f'{order.library}')
            logger.debug(f'{user.library}')

            qty = order_edition.quantity - order_edition.quantity_display()
            arrival = BaseArrival.objects.create(
                order_edition=order_edition,
                edition=order_edition.edition,
                filing=order.subscription or '',
                qty=qty,
                amount=order_edition.price_without_vat / order_edition.quantity * qty,
                amount_with_vat=order_edition.price_with_vat / order_edition.quantity * qty,
                amount_vat=order_edition.vat / order_edition.quantity * qty
            )

            belmarc = Belmarc.objects.filter(edition_id=order.edition.id).first()
            if belmarc is None:
                create_belmarc_by_edition(edition=order.edition)
            return redirect(reverse('admin:klib_basearrival_change', args=(arrival.id,)))

        return HttpResponseNotFound('Order not found')

    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            obj = self.get_object(request, object_id)
            extra_context['status'] = obj.status
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if request.POST.get('save_draft') is not None:
            draft = True
            obj.status = AbstractOrder.ORDER_STATUS_DRAFT
        else:
            obj.status = AbstractOrder.ORDER_STATUS_ACTIVE
        obj.quantity = obj.total_issue_numbers
        user = Worker.objects.using('belrw-user-db').filter(user=request.user).first()
        if user:
            obj.library = user.library
        else:
            obj.library = ''
        if not change:
            # edition_type = request.GET.get('type', Edition.TYPE_PERIODICAL)
            edition_type = Edition.TYPE_PERIODICAL
            edition_subtype = BaseEdition.objects.get(pk=obj.edition.pk).get_edition_subtype_display()
            obj.edition_type = edition_type
            obj.edition_subtype = edition_subtype
        super().save_model(request, obj, form, change)

    def get_total_price_no_vat(self, obj):
        try:
            if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers:
                return obj.price_per_instance_no_vat * obj.total_issue_numbers
            return 0
        except (TypeError, AttributeError):
            return 0

    def get_total_vat(self, obj):
        try:
            if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers and obj.vat_rate:
                total_price = obj.price_per_instance_no_vat * obj.total_issue_numbers
                return (total_price * obj.vat_rate) / 100
            return 0
        except (TypeError, AttributeError):
            return 0

    get_total_price_no_vat.short_description = _('Total price without VAT')
    get_total_vat.short_description = _('Total VAT')

    class Media:
        js = ('js/formulas.js', 'js/dynamic_edition_filter.js', 'js/subtype_order_filing.js',)


my_admin_site.register(BasePeriodicalOrder, BasePeriodicalOrderAdmin)


class BasePeriodicalOrderFirstClassAdmin(admin.ModelAdmin):
    list_display = ['edition_subtype', 'edition_name', 'library', 'year', 'status', 'contract_number', 'contract_date', 'company']
    readonly_fields = ['id', 'edition_type',
                       'get_total_price_no_vat', 'get_total_price_with_vat', 'get_total_vat', 'quantity_getted']

    common_fieldsets = (
        (_('General'),
         {
             'fields': (
                 'edition_subtype',
                 'edition',
                 'year',
                 'company',
                 'payment_type',
                 'currency',
                 'contract_number',
                 'contract_date',
                 'balance_type',
                 'duration_of_receipt',
                 'filing'
             )
         }
         ),

        (_('Periodical edition'),
         {
             'fields': [
                 'first_number',
                 'last_number',
                 'number_of_copies',
                 'total_issue_numbers',
                 'duration_of_storage',
                 'quantity_getted'
             ]
         }
         ),

        (_('The price of the order'),
         {
             'fields': (
                 'price_per_instance_no_vat',
                 'vat_per_instance',
                 'total_price_no_vat',
                 'total_vat',
                 'total_price_with_vat',
                 'vat_rate'
             )
         }
         ),
    )

    agreement_fieldsets = (
        (_('Addition agreement'), {'fields': ('addition_agreement', 'agreement_date')}),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['type'] = 'PERIODICAL'
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                extra_context['status'] = obj.status
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.common_fieldsets)

        if obj and obj.edition and obj.edition.edition_subtype == Edition.SUBTYPE_NEWSPAPER:
            fieldsets[1][1]['fields'] = ['first_number', 'last_number', 'number_of_copies', 'total_issue_numbers',
                                         'duration_of_storage', 'subscription']
        if obj:
            return fieldsets + list(self.agreement_fieldsets)

        return fieldsets

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "edition":
            subtype = request.GET.get('edition_subtype')
            if subtype:
                kwargs["queryset"] = BaseEdition.objects.filter(edition_subtype=subtype)
            else:
                kwargs["queryset"] = BaseEdition.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # inlines = [BaseOrderEditionInline]
    # def get_fieldsets(self, request, obj=None):
    #     if obj:
    #         return self.common_fieldsets + self.agreement_fieldsets
    #     return self.common_fieldsets

    # change_form_template = "admin/klib/baseperiodicalorder/change_form.html"

    # list_filter = ['status', 'contract_number', 'contract_date', 'company', 'edition__title', 'completion_date', LibraryFilter]
    list_filter = ['status', 'edition_subtype', 'contract_number', 'contract_date', 'company', 'edition__title', 'completion_date']

    change_list_template = 'klib/base_order_list.html'
    change_form_template = 'klib/register_edition_admin.html'

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(edition_type=Edition.TYPE_PERIODICAL)
        if 'status__exact' in request.GET and request.GET['status__exact'] == 'closed':
            return queryset
        return queryset.exclude(status='closed')

    def edition_name(self, obj):
        if obj.edition_type == Edition.TYPE_PERIODICAL:
            result = obj.edition.title if obj.edition else '-'
        else:
            ed = BaseOrderEdition.objects.filter(order=obj).first()
            result = ed.edition.title if ed else '-'
        return result

    edition_name.short_description = _('Title of the publication')

    def edition_year(self, obj):
        return obj.edition.year if obj.edition else '-'

    edition_year.short_description = _('Год')

    def quantity_getted(self, obj):
        return obj.get_quantity_getted()

    quantity_getted.short_description = _('Количество поступивших номеров')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register_edition_admin/<int:id>/', self.admin_site.admin_view(self.register_edition),
                 name='register_edition_admin'),
        ]
        return custom_urls + urls

    # def custom_button(self, obj):
    #     if obj.pk:
    #         return format_html(
    #             '<a class="btn btn-success form-control" href="{}" style="margin-top: 14px;">Регистрация</a>',
    #             reverse('admin:register_edition_admin', args=[obj.pk])
    #     return ''
    #
    # custom_button.short_description = 'Регистрация изданий'
    # custom_button.allow_tags = True

    def register_edition(self, request, id):
        order = self.get_object(request, id)
        if order:
            order_edition, created = BaseOrderEdition.objects.get_or_create(
                order=order,
                edition=order.edition,
                balance_type=order.balance_type,
                defaults={'quantity': order.quantity}
            )

            user = Worker.objects.get(user=request.user)

            qty = order.number_of_copies
            arrival = BaseArrival.objects.create(
                order_edition=order_edition,
                edition=order_edition.edition,
                balance_type=order_edition.balance_type,
                filing=order.subscription or '',
                qty=qty,
                amount=order.price_per_instance_no_vat * qty,
                amount_with_vat=order.price_per_instance_no_vat * qty + order.vat_per_instance * qty,
                amount_vat=order.vat_per_instance * qty
            )

            belmarc = Belmarc.objects.filter(edition_id=order.edition.id).first()
            if belmarc is None:
                create_belmarc_by_edition(edition=order.edition)
            return redirect(reverse('admin:klib_basearrival_change', args=(arrival.id,)))

        return HttpResponseNotFound('Order not found')

    # def change_view(self, request, object_id=None, form_url='', extra_context=None):
    #     extra_context = extra_context or {}
    #     if object_id:
    #         obj = self.get_object(request, object_id)
    #         extra_context['custom_button'] = self.custom_button(obj)
    #     return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if request.POST.get('save_draft') is not None:
            draft = True
            obj.status = AbstractOrder.ORDER_STATUS_DRAFT
        else:
            obj.status = AbstractOrder.ORDER_STATUS_ACTIVE
        obj.quantity = obj.total_issue_numbers
        user = Worker.objects.using('belrw-user-db').filter(user=request.user).first()
        if user:
            obj.library = user.library
        else:
            obj.library = ''
        if not change:
            obj.edition_type = Edition.TYPE_PERIODICAL
            obj.edition_subtype = BaseEdition.objects.get(pk=obj.edition.pk).get_edition_subtype_display()
        super().save_model(request, obj, form, change)

    def get_total_price_no_vat(self, obj):
        try:
            if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers:
                return obj.price_per_instance_no_vat * obj.total_issue_numbers
            return 0
        except (TypeError, AttributeError):
            return 0

    def get_total_vat(self, obj):
        try:
            if obj and obj.price_per_instance_no_vat and obj.total_issue_numbers and obj.vat_rate:
                total_price = obj.price_per_instance_no_vat * obj.total_issue_numbers
                return (total_price * obj.vat_rate) / 100
            return 0
        except (TypeError, AttributeError):
            return 0

    get_total_price_no_vat.short_description = _('Total price without VAT')
    get_total_vat.short_description = _('Total VAT')

    class Media:
        js = ('js/formulas.js', 'js/dynamic_edition_filter.js', 'js/subtype_order_filing.js',)


my_admin_site.register(BasePeriodicalOrderFirstClass, BasePeriodicalOrderFirstClassAdmin)


class OrderAdmin(admin.ModelAdmin):
    def save_as_draft(self, request):
        if request.method == "POST":
            form = self.get_form(request)(data=request.POST)

            if form.is_valid():
                order = form.save(commit=False)
                order.status = 'DRAFT'
                order.save()
                self.message_user(request, _('Order draft created'))
                return redirect(request.META.get('HTTP_REFERER'))
            else:
                error_messages = '\n'.join(
                    [f"Тест: {field}: {', '.join(errors)}" for field, errors in form.errors.items()])
                messages.error(request, _('Error saving draft. Please correct the errors below:\n') + error_messages)
                messages.error(request, 'Message')
                request.session['form_data'] = request.POST
                return redirect(request.META.get('HTTP_REFERER'))

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)
        if obj is not None and obj.status == 'CLOSED':
            for instance in inline_instances:
                instance.opts.can_delete = False
                instance.opts.can_add = False
        return inline_instances


class PeriodicalOrderAdmin(OrderAdmin):
    def get_edition_subtype(self, obj):
        return obj.edition.get_edition_subtype_display() if obj.edition else ''

    get_edition_subtype.short_description = _('Edition type')

    def get_edition_year(self, obj):
        return obj.edition.year if obj.edition else ''

    get_edition_year.short_description = _('Year')

    def get_vat_per_instance(self, obj):
        try:
            price_amount = Decimal(obj.price_per_instance.amount)
            return (Decimal(obj.vat_rate) / Decimal(100)) * price_amount
        except (AttributeError, TypeError, ValueError, DecimalException):
            return Decimal(0)

    get_vat_per_instance.short_description = _('Vat per instance')

    def get_total_vat(self, obj):
        try:
            return self.get_vat_per_instance(obj) * obj.total_issue_numbers
        except (AttributeError, TypeError, ValueError):
            return Decimal(0)

    get_total_vat.short_description = _('Total vat')

    def get_total_price_with_vat(self, obj):
        try:
            return obj.total_price + self.get_total_vat(obj)
        except (AttributeError, TypeError, ValueError):
            return Decimal(0)

    get_total_price_with_vat.short_description = _('Total price with vat')


@admin.register(JournalOrder)
class JournalOrderAdmin(PeriodicalOrderAdmin):
    form = JournalOrderForm
    list_display = ['edition', 'get_edition_year', 'get_edition_subtype',
                    'contract_number', 'contract_date', 'status',
                    'company', 'completion_date']

    readonly_fields = ['id', 'get_edition_subtype', 'get_edition_year', 'total_issue_numbers',
                       'get_vat_per_instance', 'total_price',
                       'get_total_vat', 'get_total_price_with_vat']

    fieldsets = (
        ('Создание заказа на периодику',
         {
             'fields': (('get_edition_subtype', 'edition_year'), 'edition',
                        'contract_number', 'contract_date', 'company',
                        'duration_of_receipt_months', 'duration_of_receipt_years',
                        'first_number', 'last_number',
                        'number_of_copies', 'total_issue_numbers',
                        'duration_of_storage_months', 'duration_of_storage_years',
                        'price_per_instance',
                        'get_vat_per_instance',
                        'total_price', 'get_total_price_with_vat',
                        'get_total_vat',
                        'balance_type', 'vat_rate',
                        )
         }),
        ('Дополнительное соглашение',
         {
             'fields': (
                 'addition_agreement', 'agreement_date',
             )
         }),
    )

    change_form_template = "klib/save_as_draft_journal.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('save-as-draft-journal/', self.admin_site.admin_view(self.save_as_draft),
                 name='save-as-draft-journal'),
        ]
        return custom_urls + urls


my_admin_site.register(JournalOrder, JournalOrderAdmin)


@admin.register(NewspaperOrder)
class NewspaperOrderAdmin(PeriodicalOrderAdmin):
    form = NewspaperOrderForm

    list_display = ['edition', 'get_edition_year', 'get_edition_subtype',
                    'contract_number', 'contract_date', 'status',
                    'company', 'completion_date']

    readonly_fields = ['id', 'get_edition_subtype', 'get_edition_year', 'total_issue_numbers',
                       'get_vat_per_instance', 'total_price',
                       'get_total_vat', 'get_total_price_with_vat']

    fieldsets = (
        ('Создание заказа на периодику',
         {
             'fields': (('get_edition_subtype', 'edition_year'), 'edition',
                        'contract_number', 'contract_date', 'company',
                        'duration_of_receipt_months', 'duration_of_receipt_years',
                        'first_number', 'last_number',
                        'number_of_copies', 'total_issue_numbers',
                        'duration_of_storage_months', 'duration_of_storage_years',
                        'bound_year',
                        'price_per_instance',
                        'get_vat_per_instance',
                        'total_price', 'get_total_price_with_vat',
                        'get_total_vat',
                        'balance_type', 'vat_rate',
                        )
         }),
        ('Дополнительное соглашение',
         {
             'fields': (
                 'addition_agreement', 'agreement_date',
             )
         }))

    change_form_template = "klib/save_as_draft_newspaper.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('save-as-draft/', self.admin_site.admin_view(self.save_as_draft), name='save-as-draft-newspaper'),
        ]
        return custom_urls + urls


my_admin_site.register(NewspaperOrder, NewspaperOrderAdmin)


class NonPeriodicalOrderElementInline(admin.StackedInline):
    model = NonPeriodicalOrderElement
    extra = 0
    min_num = 1
    form = NonPeriodicalOrderElementForm
    readonly_fields = ['get_edition_subtype', 'get_price_with_vat', 'get_vat']
    fields = ['get_edition_subtype', 'edition', 'number_of_copies',
              'price', 'vat_rate', 'get_price_with_vat', 'get_vat']

    def get_edition_subtype(self, obj):
        return obj.edition.get_edition_subtype_display() if obj.edition else ''

    get_edition_subtype.short_description = _('Edition type')

    def get_vat(self, obj):
        vat_rate = obj.vat_rate if obj.vat_rate is not None else 0
        price = obj.price if obj.price is not None else 0
        return (Decimal(vat_rate) / Decimal(100)) * price

    get_vat.short_description = _('Vat')

    def get_price_with_vat(self, obj):
        price = obj.price if obj.price is not None else 0
        return price + self.get_vat(obj)

    get_price_with_vat.short_description = _('Price with vat')


@admin.register(NonPeriodicalOrder)
class NonPeriodicalOrderAdmin(OrderAdmin):
    inlines = [NonPeriodicalOrderElementInline]
    list_display = ['edition', 'status', 'contract_number', 'contract_date', 'company', 'completion_date']
    readonly_fields = ['id', 'total_price', 'get_total_price_with_vat', 'total_vat', 'edition']
    fields = ['currency', 'balance_type', 'contract_number', 'contract_date', 'company', 'total_price',
              'get_total_price_with_vat', 'total_vat']

    labels = {
        'currency': 'Издание'
    }

    def edition(self, obj):
        edte = NonPeriodicalOrderElement.objects.filter(order=obj).first()
        edt = edte.edition if edte else None
        return edt.title if edt else ''

    edition.short_description = _('Title of the publication')

    def get_total_price_with_vat(self, obj):
        total_price = obj.total_price if obj.total_price is not None else 0
        total_vat = obj.total_vat if obj.total_vat is not None else 0
        return total_price + total_vat

    get_total_price_with_vat.short_description = _('Total order price with vat')

    change_form_template = "klib/save_as_draft_non.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('save-as-draft-journal/', self.admin_site.admin_view(self.save_as_draft),
                 name='save-as-draft-journal')
        ]
        return custom_urls + urls

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.save()

        super().save_model(request, obj, form, change)

    @transaction.atomic
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)


my_admin_site.register(NonPeriodicalOrder, NonPeriodicalOrderAdmin)

#поступления
@admin.register(BaseArrival)
class BaseArrivalAdmin(admin.ModelAdmin):
    SUBTYPES = {
        BaseEdition.SUBTYPE_BOOK: 1,
        BaseEdition.SUBTYPE_BROCHURE: 2,
        BaseEdition.SUBTYPE_STD: 2,
        BaseEdition.SUBTYPE_INFORMATION_FLYER: 5,
        BaseEdition.SUBTYPE_STD_CHANGES: 6,
        BaseEdition.SUBTYPE_E_RESOURCE: 8,
        BaseEdition.SUBTYPE_MAGAZINE: 3,
        BaseEdition.SUBTYPE_NEWSPAPER: 4,
    }

    # inlines = [BaseFundElementInline]
    list_display = ['order_edition', 'qty', 'amount', 'amount_with_vat', 'amount_vat', 'invoice_number', 'invoice_date',
                    'balance_type']
    class Media:
        js = ('js/base_arrival_formulas.js',)

    labels = {
        'currency': 'Издание'
    }

    def get_fields(self, request, obj=None):
        fields = ['id', 'company', 'edition', 'qty', 'amount', 'amount_with_vat', 'amount_vat', 'invoice_number', 'invoice_date']
        self.readonly_fields = ['id', 'balance_type', 'amount', 'amount_with_vat', 'amount_vat']
        edition_type = request.GET.get('type')

        if edition_type == 'PERIODICAL':
            fields.remove('amount')
            fields.remove('amount_with_vat')
            fields.remove('amount_vat')

        if edition_type == 'NON_PERIODICAL':
            fields.remove('amount')
            fields.remove('amount_with_vat')
            fields.remove('amount_vat')

        if obj:
            if obj.order_edition:
                fields.insert(1, 'order_edition')
                self.readonly_fields.extend(['order_edition', 'edition'])
            if obj.edition.edition_type == Edition.TYPE_PERIODICAL:
                fields.extend(['double_number', 'edition_number', 'second_edition_number'])
        else:
            if edition_type == 'PERIODICAL':
                fields.extend(['double_number', 'edition_number', 'second_edition_number'])

        return fields

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        obj = None
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if request.resolver_match.kwargs.get('object_id'):
            obj = self.get_object(request, request.resolver_match.kwargs.get('object_id'))

        if db_field.name in ['amount_with_vat', 'amount_vat', 'amount', 'invoice_number', 'invoice_date',
                             'edition_number']:
            if obj and obj.order_edition:
                db_field.blank = False
            else:
                db_field.blank = True

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "edition":
            edition_type = request.GET.get('type')
            if edition_type:
                kwargs["queryset"] = BaseEdition.objects.filter(edition_type=edition_type)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @transaction.atomic
    def save_model(self, request, obj: BaseArrival, form, change):
        if obj.pk is None:
            worker = Worker.objects.filter(user_id=request.user.id).first() or \
                     Reader.objects.filter(user_id=request.user.id).first()
            if worker is None:
                self.message_user(request, 'Пользователь не является работником', level=messages.WARNING)
                if obj.order_edition:
                    obj.library = obj.order_edition.order.library
                else:
                    self.message_user(request, 'Заказ не указан', level=messages.WARNING)
                    return redirect(reverse('admin:klib_basearrival_changelist'))
            else:
                obj.library = worker.library

        obj.save(request=request)  # Передаем request в save

        element = BaseFundElement.objects.filter(arrival=obj).first()
        if element is None and obj.qty:
            try:
                price = obj.amount / obj.qty
                price_with_vat = obj.amount_with_vat / obj.qty
                vat_amount = obj.amount_vat / obj.qty
            except Exception as _:
                price = None
                price_with_vat = None
                vat_amount = None

            number_prefix = self.SUBTYPES[obj.edition.edition_subtype]
            last_fund_element: BaseFundElement = BaseFundElement.objects.filter(
                edition__edition_subtype=obj.edition.edition_subtype).last()
            index = 1
            if last_fund_element:
                index = int(last_fund_element.inventory_number.split('/')[1]) + 1

            for i in range(index, index + obj.qty):
                BaseFundElement.objects.create(
                    arrival=obj,
                    inventory_number=f'{number_prefix}/{i}',
                    price=price,
                    price_with_vat=price_with_vat,
                    vat_amount=vat_amount,
                    registration_date=datetime.date.today(),
                    invoice_number=obj.invoice_number,
                    invoice_date=obj.invoice_date,
                    edition=obj.edition,
                    subscription=obj.order_edition.order.filing,
                    library=obj.library,
                    balance_type=obj.balance_type
                )

        obj.save(request=request)
        super().save_model(request, obj, form, change)

    def response_change(self, request, obj: BaseArrival):
        if obj.edition.edition_subtype == Edition.SUBTYPE_MAGAZINE:
            redirect_url = reverse('admin:klib_basefundelementmagazines_changelist')
        elif obj.edition.edition_subtype == Edition.SUBTYPE_NEWSPAPER:
            redirect_url = reverse('admin:klib_basefundelementnewspapers_changelist')
        else:
            redirect_url = reverse('admin:klib_basefundelement_changelist')
        return HttpResponseRedirect(redirect_url)

    def response_add(self, request, obj, post_url_continue=None):
        if obj.edition.edition_subtype == Edition.SUBTYPE_MAGAZINE:
            redirect_url = reverse('admin:klib_basefundelementmagazines_changelist')
        elif obj.edition.edition_subtype == Edition.SUBTYPE_NEWSPAPER:
            redirect_url = reverse('admin:klib_basefundelementnewspapers_changelist')
        else:
            redirect_url = reverse('admin:klib_basefundelement_changelist')
        return HttpResponseRedirect(redirect_url)


my_admin_site.register(BaseArrival, BaseArrivalAdmin)


class EditionTitleFilter(SimpleListFilter):
    title = _('Edition title')
    parameter_name = 'edition_title'

    def lookups(self, request, model_admin):
        titles = set([e.title for e in BaseEdition.objects.all()])
        return [(title, title) for title in titles]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(edition__title=self.value())
        return queryset


class EditionAuthorFilter(SimpleListFilter):
    title = _('Author')
    parameter_name = 'Author'

    def lookups(self, request, model_admin):
        authors = set([e.author for e in BaseEdition.objects.all()])
        return [(author, author) for author in authors]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(edition__author=self.value())
        return queryset


class WriteOffActNumberFilter(admin.SimpleListFilter):
    title = _('Номер акта списания')
    parameter_name = 'write_off_act_number'

    def lookups(self, request, model_admin):
        acts_journal = WriteOffActJournal.objects.values_list('id', flat=True)
        acts_not_periodicals = WriteOffActNotPeriodicals.objects.values_list('id', flat=True)
        acts_files = WriteOffActFiles.objects.values_list('id', flat=True)
        acts_depository = DepositoryFundElement.objects.values_list('id', flat=True)
        acts_ids = set(acts_journal) | set(acts_not_periodicals) | set(acts_files) | set(acts_depository)
        return [(act_id, f'Акт №{act_id}') for act_id in acts_ids]

    def queryset(self, request, queryset):
        if self.value():
            act_id = self.value()

            queryset = queryset.filter(
                inventory_number__in=WriteOffActJournal.objects.filter(id=act_id).values_list('inventory_number',
                                                                                              flat=True)
            ) | queryset.filter(
                inventory_number__in=WriteOffActNotPeriodicals.objects.filter(id=act_id).values_list('inventory_number',
                                                                                                     flat=True)
            ) | queryset.filter(
                inventory_number__in=WriteOffActFiles.objects.filter(id=act_id).values_list('inventory_number',
                                                                                            flat=True)
            ) | queryset.filter(
                inventory_number__in=DepositoryFundElement.objects.filter(id=act_id).values_list('inventory_number',
                                                                                                 flat=True)
            )
        return queryset


# Фонд все остальное
@admin.register(BaseFundElement)
class BaseFundElementAdmin(admin.ModelAdmin):
    list_display = ['registration_date', 'inventory_number', 'author', 'title', 'year', 'invoice_number',
                    'edition_type', 'edition_subtype', 'publication_status', 'write_off_act_link', 'is_booked',
                    'balance_type']
    readonly_fields = ['id', 'registration_date', 'inventory_number', 'price', 'author', 'title', 'year',
                       'price_with_vat', 'vat_amount', 'invoice_number', 'invoice_date', 'edition_type',
                       'edition_subtype', 'publication_status', 'edition_number', 'double_number',
                       'second_edition_number', 'is_booked', 'balance_type']

    labels = {
        'currency': 'Издание'
    }

    list_filter = [EditionTitleFilter, EditionAuthorFilter, 'edition__edition_subtype', 'publication_status', WriteOffActNumberFilter, 'inventory_number']

    actions = ['mark_as_written_off', 'create_depository_fund_element', 'replacement']

    def has_add_permission(self, request, obj=None):
        return False

    def double_number(self, obj: BaseFundElement):
        return 'Да' if obj.arrival.double_number else 'Нет'

    def edition_number(self, obj: BaseFundElement):
        return obj.arrival.edition_number if obj.arrival.edition_number else '-'

    def second_edition_number(self, obj: BaseFundElement):
        return obj.arrival.second_edition_number if obj.arrival.second_edition_number else '-'

    double_number.short_description = _('Double number')
    edition_number.short_description = _('Edition Number')
    second_edition_number.short_description = _('Second Edition Number')

    def get_fields(self, request, obj=None):
        if obj:
            fields = ['id', 'registration_date', 'inventory_number', 'author', 'title', 'year', 'invoice_number',
                      'edition_type', 'edition_subtype', 'publication_status', 'is_booked', 'balance_type']
            if obj.edition.edition_type == Edition.TYPE_PERIODICAL:
                fields.extend(['double_number', 'edition_number'])
                if obj.arrival.double_number:
                    fields.append('second_edition_number')
        else:
            fields = ['edition']

        return fields

    def write_off_act_link(self, obj):
        if not obj.inventory_number:
            return '-'
        inventory_numbers = re.split(r',\s*', obj.inventory_number)
        write_off_acts_journal = WriteOffActJournal.objects.filter(inventory_number__icontains=obj.inventory_number)
        write_off_acts_not_periodicals = WriteOffActNotPeriodicals.objects.filter(
            inventory_number__icontains=obj.inventory_number)
        write_off_acts_files = WriteOffActFiles.objects.filter(inventory_number__icontains=obj.inventory_number)
        write_off_acts_depository = DepositoryFundElement.objects.filter(inventory_number__in=inventory_numbers)

        write_off_acts = list(write_off_acts_journal) + list(write_off_acts_not_periodicals) + list(
            write_off_acts_files) + list(write_off_acts_depository)

        if write_off_acts:
            urls = []
            for write_off_act in write_off_acts:
                if isinstance(write_off_act, WriteOffActJournal):
                    url = f'/admin/klib/writeoffactjournal/{write_off_act.id}/change/'
                    act_name = 'Журнал'
                elif isinstance(write_off_act, WriteOffActNotPeriodicals):
                    url = f'/admin/klib/writeoffactnotperiodicals/{write_off_act.id}/change/'
                    act_name = 'Непериодические издания'
                elif isinstance(write_off_act, WriteOffActFiles):
                    url = f'/admin/klib/writeoffactfiles/{write_off_act.id}/change/'
                    act_name = 'Файлы'
                elif isinstance(write_off_act, DepositoryFundElement):
                    url = f'/admin/klib/depositoryfundelement/{write_off_act.id}/change/'
                    act_name = 'Депозитарий'
                else:
                    continue

                urls.append(f'<a href="{url}">Акт списания {act_name} №{write_off_act.id}</a>')

            return format_html('<br>'.join(urls))

        return '-'

    write_off_act_link.short_description = _("Viewing the debit statement")

    def get_display_name(self, key, choices):
        for choice_key, display_name in choices:
            if choice_key == key:
                return display_name
        return key

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.exclude(edition__edition_subtype__in=['MAGAZINES', 'NEWSPAPERS'])
        publication_status = request.GET.get('publication_status__exact')
        if publication_status:
            qs = qs.filter(publication_status=publication_status)
        edition_type = request.GET.get('types')
        if edition_type:
            qs = qs.filter(edition__edition_type=edition_type)

        user_library = get_user_library(request.user)
        if user_library:
            qs = qs.filter(library=user_library)

        edition_subtype = request.GET.get('PERIODICAL_SUBTYPES')
        if edition_type:
            qs = qs.filter(edition__edition_subtype=edition_subtype)

        return qs

    def author(self, obj: BaseFundElement):
        try:
            return obj.edition.author if obj.edition.author else '-'
        except Exception as e:
            return ''

    author.short_description = _('Author')

    def title(self, obj: BaseFundElement):
        try:
            return obj.edition.title if obj.edition.title else '-'
        except Exception as e:
            return ''

    title.short_description = _('Edition title')

    def edition_type(self, obj: BaseFundElement):
        try:
            edition_type_value = obj.edition.edition_type
            if edition_type_value:
                return dict(obj.edition.TYPES).get(edition_type_value, '-')
            return '-'
        except Exception as _:
            return ''

    edition_type.short_description = _('Edition type')

    def edition_subtype(self, obj: BaseFundElement):
        try:
            edition_subtype_value = obj.edition.edition_subtype
            if edition_subtype_value:
                return dict(obj.edition.SUBTYPES).get(edition_subtype_value, '-')
            return '-'
        except:
            return ''

    edition_subtype.short_description = _('Edition subtype')

    def year(self, obj: BaseFundElement):
        try:
            return obj.edition.year if obj.edition.year else '-'
        except:
            return ''

    year.short_description = _('Year')

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = True
        return super(BaseFundElementAdmin, self).changeform_view(request, object_id, extra_context=extra_context)

    def has_edit_permission(self, request, obj=None):
        return False

    def edition(self, obj: BaseFundElement):
        return obj.arrival if obj.arrival else ''

    @transaction.atomic
    def save_model(self, request, obj: BaseFundElement, form, change):
        if obj.pk is None:
            last_fund_element: BaseFundElement = BaseFundElement.objects.filter(
                edition__edition_subtype=obj.edition.edition_subtype).last()
            index = 1
            if last_fund_element:
                index = int(last_fund_element.inventory_number.split('/')[1])
            number_prefix = BaseArrivalAdmin.SUBTYPES[obj.edition.edition_subtype]
            obj.inventory_number = f'{number_prefix}/{index + 1}'
        if obj.arrival:
            obj.library = obj.arrival.library
        else:
            user = Worker.objects.filter(id=request.user.id).first()
            if user:
                obj.library = user.library
            else:
                obj.library = ''
                # obj.save()

        super().save_model(request, obj, form, change)

    @transaction.atomic
    def mark_as_written_off(self, request, queryset):
        if request.method == "POST":
            elements_with_links = []
            for element in queryset:
                if self.write_off_act_link(element) != "-":
                    elements_with_links.append(element.inventory_number)

            if elements_with_links:
                element_ids = ", ".join(map(str, elements_with_links))
                messages.error(
                    request,
                    f"Невозможно списать: для следующих элементов уже существуют акты списания: {element_ids}"
                )
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            already_written_off = queryset.filter(publication_status='WRITTEN_OFF')
            if already_written_off.exists():
                element_ids = ", ".join(map(str, already_written_off.values_list('inventory_number', flat=True)))
                messages.error(request, f"Следующие элементы уже были списаны: {element_ids}")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            basis_for_write_off = request.POST.get('basis_for_write_off', '')

            selected_elements = queryset.values('id', 'inventory_number',
                                                'edition__edition_subtype',
                                                'edition__edition_type')

            unique_types = set(
                selected_elements.values_list('edition__edition_type', flat=True))

            if len(unique_types) > 1:
                messages.error(request,
                               "Выбранные элементы должны быть одного типа: либо периодические, либо непериодические.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            edition_type = list(unique_types)[0]
            if edition_type == 'PERIODICAL':
                unique_subtypes = set(
                    selected_elements.values_list('edition__edition_subtype', flat=True))
                if len(unique_subtypes) > 1:
                    messages.error(request,
                                   "Все выбранные элементы должны быть одного подтипа (например, только MAGAZINES или только NEWSPAPERS).")
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            element_count_by_type = {}
            inventory_numbers = []
            write_off_acts = {}

            for element in selected_elements:
                inventory_number = element.get('inventory_number')
                if inventory_number is None:
                    continue

                inventory_numbers.append(inventory_number)
                edition_type = element['edition__edition_subtype']

                if edition_type not in element_count_by_type:
                    element_count_by_type[edition_type] = 0
                element_count_by_type[edition_type] += 1

                if edition_type in ['MAGAZINES', 'NEWSPAPERS']:
                    act_key = 'MAGAZINES' if edition_type == 'MAGAZINES' else 'NEWSPAPERS'
                    if act_key not in write_off_acts:
                        write_off_acts[act_key] = WriteOffActJournal.objects.create(
                            basis_for_write_off=basis_for_write_off,
                            submitted_by=request.user.id,
                            registered_by=request.user.id
                        ) if edition_type == 'MAGAZINES' else WriteOffActFiles.objects.create(
                            basis_for_write_off=basis_for_write_off,
                            submitted_by=request.user.id,
                            registered_by=request.user.id
                        )
                elif edition_type in dict(BaseFundElement.NON_PERIODICAL_SUBTYPES).keys():
                    if 'NON_PERIODICAL' not in write_off_acts:
                        write_off_acts['NON_PERIODICAL'] = WriteOffActNotPeriodicals.objects.create(
                            basis_for_write_off=basis_for_write_off,
                            submitted_by=request.user.id,
                            registered_by=request.user.id,
                        )

            for act_type, write_off_act in write_off_acts.items():
                elements_info = []

                for edition_type, count in element_count_by_type.items():
                    year = ""
                    for element in selected_elements:
                        if element['edition__edition_subtype'] == edition_type:
                            year = element.get('edition__year', '')
                            break

                    if year:
                        elements_info.append(
                            f"{self.get_display_name(edition_type, BaseFundElement.TYPES)} - {year} - {count}")
                    else:
                        elements_info.append(f"{self.get_display_name(edition_type, BaseFundElement.TYPES)} - {count}")

                write_off_act.selected_elements_info = "\n".join(elements_info)
                write_off_act.inventory_number = ", ".join(inventory_numbers)
                write_off_act.total_excluded = queryset.count()
                write_off_act.save()

            queryset.update(publication_status='WRITTEN_OFF')

            selected_ids = list(queryset.values_list('id', flat=True))
            selected_ids_str = ",".join(map(str, selected_ids))
            redirect_url = None

            for act_type, write_off_act in write_off_acts.items():
                if act_type == 'MAGAZINES':
                    redirect_url = f"/admin/klib/writeoffactjournal/{write_off_act.pk}/change/?selected_ids={selected_ids_str}"
                elif act_type == 'NEWSPAPERS':
                    redirect_url = f"/admin/klib/writeoffactfiles/{write_off_act.pk}/change/?selected_ids={selected_ids_str}"
                elif act_type == 'NON_PERIODICAL':
                    redirect_url = f"/admin/klib/writeoffactnotperiodicals/{write_off_act.pk}/change/?selected_ids={selected_ids_str}"

                editions_without_active_elements = (
                    BaseEdition.objects.annotate(
                        has_active_elements=Exists(
                            BaseFundElement.objects.filter(
                                edition=OuterRef('pk')
                            ).exclude(publication_status='WRITTEN_OFF')
                        )
                    ).filter(has_active_elements=False).values('id', 'title')
                )

                if editions_without_active_elements.exists():
                    for edition in editions_without_active_elements:
                        sku = Belmarc.objects.filter(edition_id=edition['id']).first()
                        if sku:
                            try:
                                unpublish_index_by_sku(sku)
                            except Exception as e:
                                logger.error(f"Error unpublishing index: {e}")

            if redirect_url:
                return HttpResponseRedirect(redirect_url)

    mark_as_written_off.short_description = _("Mark as decommissioned")

    @transaction.atomic
    def create_depository_fund_element(self, request, queryset):

        elements_with_links = []
        for element in queryset:
            if self.write_off_act_link(element) != "-":
                elements_with_links.append(element.inventory_number)

        if elements_with_links:
            element_ids = ", ".join(map(str, elements_with_links))
            messages.error(
                request,
                f"Невозможно создать депонированный фонд: для следующих элементов уже существуют акты списания: {element_ids}"
            )
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        selected_elements = queryset.values('id', 'inventory_number', 'edition__edition_subtype',
                                            'edition__edition_type')
        unique_types = set(selected_elements.values_list('edition__edition_type', flat=True))

        if len(unique_types) > 1:
            messages.error(request, "Выбранные элементы должны быть одного типа.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        edition_type = list(unique_types)[0]

        depository_fund_element = DepositoryFundElement.objects.create(
            act_date=timezone.now(),
            basis_for_write_off="Основание для депонирования",
            submitted_by=request.user.id,
            registered_by=request.user.id
        )

        inventory_numbers = []
        elements_info = []
        for element in selected_elements:
            inventory_number = element.get('inventory_number')
            if inventory_number:
                inventory_numbers.append(inventory_number)
                edition_subtype = element.get('edition__edition_subtype')
                year = element.get('edition__year', '-')
                elements_info.append(
                    f"{self.get_display_name(edition_subtype, BaseFundElement.STATUS)} - {year} - {inventory_number}"
                )

        depository_fund_element.selected_elements_info = "\n".join(elements_info)
        depository_fund_element.inventory_number = ", ".join(inventory_numbers)
        depository_fund_element.total_excluded = queryset.count()
        depository_fund_element.save()

        queryset.update(publication_status='IN_THE_DEPOSITORY_FUND')

        selected_ids = list(queryset.values_list('id', flat=True))
        selected_ids_str = ",".join(map(str, selected_ids))
        redirect_url = f"/admin/klib/depositoryfundelement/{depository_fund_element.pk}/change/?selected_ids={selected_ids_str}"

        return HttpResponseRedirect(redirect_url)

    create_depository_fund_element.short_description = "Депозитарный фонд"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('replacement/',
                 self.admin_site.admin_view(self.replacement_view),
                 name='klib_basefundelement_changelist_replacement'),
        ]
        return custom_urls + urls

    def replacement(self, request, queryset):
        if not queryset:
            messages.error(request, "Не выбраны элементы для замены")
            return

        replacement_act = ReplacementAct.objects.create(
            # basis_for_write_off="Основание для замены",
            submitted_by=request.user.id,
            registered_by=request.user.id
        )
        request.session['replacement_act_id'] = replacement_act.pk
        request.session['replacement_queue'] = list(queryset.values_list('id', flat=True))

        return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist_replacement'))

    def replacement_view(self, request):

        if 'replacement_queue' not in request.session:
            logger.warning("No replacement queue in session")
            messages.error(request, "Нет элементов для замены")
            return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist'))

        if not request.session['replacement_queue']:
            logger.info("Queue is empty, redirecting to act page")
            act_id = request.session['replacement_act_id']
            del request.session['replacement_queue']
            del request.session['replacement_act_id']
            return HttpResponseRedirect(f"/admin/klib/replacementact/{act_id}/change/")

        try:
            element_id = request.session['replacement_queue'][0]

            element = BaseFundElement.objects.get(id=element_id)
            replacement_act = ReplacementAct.objects.get(pk=request.session['replacement_act_id'])

            existing_replace = ReplaceEdition.objects.filter(
                replaceable_edition=element,
                act=replacement_act
            ).first()

            if existing_replace:
                logger.warning(f"ReplaceEdition already exists for element_id={element_id}")
                request.session['replacement_queue'] = request.session['replacement_queue'][1:]
                request.session.modified = True
                return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist_replacement'))

            replace_edition = ReplaceEdition.objects.create(
                replaceable_edition=element,
                act=replacement_act
            )
            logger.info(f"Created new ReplaceEdition with id={replace_edition.pk}")

            return HttpResponseRedirect(f"/admin/klib/replaceedition/{replace_edition.pk}/change/")
        except (BaseFundElement.DoesNotExist, ReplacementAct.DoesNotExist) as e:
            messages.error(request, f"Ошибка при создании замены: {str(e)}")
            return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist'))

    replacement.short_description = "Замена"


my_admin_site.register(BaseFundElement, BaseFundElementAdmin)


@admin.register(ReplaceEdition)
class ReplaceEditionAdmin(admin.ModelAdmin):
    fields = ['replaceable_edition', 'replaceable_title', 'replacing_edition']
    readonly_fields = ['replaceable_edition', 'replaceable_title']

    def response_change(self, request, obj):
        """
        Переопределяем поведение после сохранения формы
        """
        if 'replacement_queue' in request.session and request.session['replacement_queue']:
            request.session['replacement_queue'] = request.session['replacement_queue'][1:]
            request.session.modified = True

            url = reverse('admin:klib_basefundelement_changelist_replacement')
            return HttpResponseRedirect(url)
        elif 'replacement_act_id' in request.session:
            logger.info("Queue is empty, redirecting to act page")
            act_id = request.session['replacement_act_id']
            del request.session['replacement_queue']
            del request.session['replacement_act_id']
            return HttpResponseRedirect(f"/admin/klib/replacementact/{act_id}/change/")

        return super().response_change(request, obj)


my_admin_site.register(ReplaceEdition, ReplaceEditionAdmin)


@admin.register(ReplacementAct)
class ReplacementActAdmin(admin.ModelAdmin):
    fields = [
        'act_number',
        'act_date',
        'replace_editions_display',
        'socio_economic_count',
        'technical_count',
        'other_count',
        'railway_theme_count',
        'chairman',
        'vice_chairman',
        'member_1',
        'member_2',
        'member_3',
        'submitted_by',
        'registered_by'
    ]
    readonly_fields = ['replace_editions_display']

    change_form_template = 'klib/change_replacement_act.html'

    form = ReplacementActForm

    def approve(self, request, object_id):
        logger.info(f'=== Approving ReplacementAct {object_id} ===')
        try:
            act = ReplacementAct.objects.get(pk=object_id)
            replace_editions = act.get_replace_editions()

            for replace_edition in replace_editions:
                replace_edition.replaceable_edition.publication_status = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
                replace_edition.replaceable_edition.save()

                replace_edition.replacing_fund_element.publication_status = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
                replace_edition.replacing_fund_element.inventory_number = replace_edition.replaceable_edition.inventory_number
                replace_edition.replacing_fund_element.invoice_date = replace_edition.replaceable_edition.invoice_date
                replace_edition.replacing_fund_element.save()
                logger.info(f'Replacing fund element {replace_edition.replacing_fund_element.id} updated')

            messages.success(request, 'Акт успешно подтвержден')
        except Exception as e:
            logger.error(f'Error approving act: {e}')
            messages.error(request, 'Ошибка при подтверждении акта')

        return HttpResponseRedirect(
            reverse('admin:klib_replacementact_change', args=[object_id])
        )

    def disapprove(self, request, object_id):
        logger.info(f'=== Disapproving ReplacementAct {object_id} ===')
        try:
            act = ReplacementAct.objects.get(pk=object_id)
            replace_editions = act.get_replace_editions()

            for replace_edition in replace_editions:
                replace_edition.replaceable_edition.publication_status = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
                replace_edition.replaceable_edition.save()

                replace_edition.replacing_fund_element.delete()
                logger.info(f'Replacing fund element {replace_edition.replacing_fund_element.id} updated')

            messages.success(request, 'Акт успешно отклонен')
        except Exception as e:
            logger.error(f'Error disapproving act: {e}')
            messages.error(request, 'Ошибка при подтверждении акта')

        return HttpResponseRedirect(
            reverse('admin:klib_replacementact_change', args=[object_id])
        )

    def save_model(self, request, obj, form, change):
        logger.info("=== Saving ReplacementAct ===")
        logger.info(f"Form data: {form.cleaned_data}")
        logger.info(f"Form errors: {form.errors}")

        if not obj.pk:
            obj.submitted_by = request.user.id
            obj.registered_by = request.user.id

        super().save_model(request, obj, form, change)

        for replace_edition in obj.get_replace_editions():
            replace_edition.replaceable_edition.publication_status = BaseFundElement.PUBLICATION_STATUS_REPLACEABLE
            replace_edition.replaceable_edition.save()

            replacing_fund_element = BaseFundElement.objects.create(
                edition=replace_edition.replacing_edition,
                publication_status=BaseFundElement.PUBLICATION_STATUS_REPLACING,
                library=replace_edition.replaceable_edition.library
            )
            replace_edition.replacing_fund_element = replacing_fund_element
            replace_edition.save()

    def replace_editions_display(self, obj):
        if not obj:
            return "—"

        editions = obj.get_replace_editions()
        if not editions:
            return "Нет замен изданий"

        html = ['<table style="width:100%">']
        html.append('<tr><th>Заменяемое издание</th><th>Просмотр</th></tr>')

        for edition in editions:
            replaceable = edition.replaceable_edition

            html.append('<tr>')
            html.append(f'<td>{replaceable.edition.title if replaceable and replaceable.edition else "—"}</td>')
            html.append(f'<td><a href="{f"/admin/klib/replaceedition/{edition.pk}/change/"}">Посмотреть</a></td>')
            html.append('</tr>')

        html.append('</table>')

        return mark_safe(''.join(html))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/approve/',
                self.admin_site.admin_view(self.approve),
                name='approve'
            ),
            path(
                '<path:object_id>/print/',
                self.admin_site.admin_view(self.print_act),
                name='print_act'
            ),
            path(
                '<path:object_id>/disapprove/',
                self.admin_site.admin_view(self.disapprove),
                name='disapprove'
            ),
        ]
        return custom_urls + urls

    def print_act(self, request, object_id):
        obj = self.get_object(request, object_id)
        document_stream = generate_act_document_replacement(obj)
        response = HttpResponse(
            document_stream,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response

    def response_post_save_change(self, request, obj):
        return HttpResponseRedirect(
            reverse(
                'admin:klib_replacementact_change',
                args=[obj.pk],
            )
        )

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(
            reverse(
                'admin:klib_replacementact_change',
                args=[obj.pk],
            )
        )

    replace_editions_display.short_description = 'Замены изданий'


my_admin_site.register(ReplacementAct, ReplacementActAdmin)


class BaseFundElementFirstClassAdmin(admin.ModelAdmin):
    list_display = ['registration_date', 'library', 'inventory_number', 'author', 'title', 'year', 'invoice_number',
                    'edition_type', 'edition_subtype', 'publication_status', 'write_off_act_link', 'is_booked']
    readonly_fields = ['id', 'registration_date', 'inventory_number', 'price', 'author', 'title', 'year',
                       'price_with_vat', 'vat_amount', 'invoice_number', 'invoice_date', 'edition_type',
                       'edition_subtype', 'publication_status', 'edition_number', 'double_number',
                       'second_edition_number', 'is_booked']

    labels = {
        'currency': 'Издание'
    }

    def has_add_permission(self, request, obj=None):
        return False

    def double_number(self, obj: BaseFundElement):
        return 'Да' if obj.arrival.double_number else 'Нет'

    def edition_number(self, obj: BaseFundElement):
        return obj.arrival.edition_number if obj.arrival.edition_number else '-'

    def second_edition_number(self, obj: BaseFundElement):
        return obj.arrival.second_edition_number if obj.arrival.second_edition_number else '-'

    double_number.short_description = _('Double number')
    edition_number.short_description = _('Edition Number')
    second_edition_number.short_description = _('Second Edition Number')

    def get_fields(self, request, obj=None):
        if obj:
            fields = ['id', 'registration_date', 'library', 'inventory_number', 'author', 'title', 'year',
                      'invoice_number',
                      'edition_type', 'edition_subtype', 'publication_status', 'is_booked']
            if obj.edition.edition_type == Edition.TYPE_PERIODICAL:
                fields.extend(['double_number', 'edition_number'])
                if obj.arrival.double_number:
                    fields.append('second_edition_number')
        else:
            fields = ['edition']

        return fields

    def write_off_act_link(self, obj):
        write_off_acts_journal = WriteOffActJournal.objects.filter(inventory_number=obj.inventory_number)
        write_off_acts_not_periodicals = WriteOffActNotPeriodicals.objects.filter(
            inventory_number=obj.inventory_number)
        write_off_acts_files = WriteOffActFiles.objects.filter(inventory_number=obj.inventory_number)
        write_off_acts_depository = DepositoryFundElement.objects.filter(inventory_number=obj.inventory_number)

        write_off_acts = list(write_off_acts_journal) + list(write_off_acts_not_periodicals) + list(
            write_off_acts_files) + list(write_off_acts_depository)

        if write_off_acts:
            urls = []
            for write_off_act in write_off_acts:
                if isinstance(write_off_act, WriteOffActJournal):
                    url = f'/admin/klib/writeoffactjournal/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActNotPeriodicals):
                    url = f'/admin/klib/writeoffactnotperiodicals/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActFiles):
                    url = f'/admin/klib/writeoffactfiles/{write_off_act.id}/change/'
                elif isinstance(write_off_act, DepositoryFundElement):
                    url = f'/admin/klib/depositoryfundelement/{write_off_act.id}/change/'
                else:
                    continue

                urls.append(f'<a href="{url}">акт списания {write_off_act.id}</a>')

            return format_html('<br>'.join(urls))
        return '-'

    write_off_act_link.short_description = _("Viewing the debit statement")

    def get_display_name(self, key, choices):
        for choice_key, display_name in choices:
            if choice_key == key:
                return display_name
        return key

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.exclude(edition__edition_subtype__in=['MAGAZINES', 'NEWSPAPERS'])
        publication_status = request.GET.get('publication_status__exact')
        if publication_status:
            qs = qs.filter(publication_status=publication_status)
        edition_type = request.GET.get('types')
        if edition_type:
            qs = qs.filter(edition__edition_type=edition_type)

        edition_subtype = request.GET.get('PERIODICAL_SUBTYPES')
        if edition_type:
            qs = qs.filter(edition__edition_subtype=edition_subtype)

        return qs

    list_filter = ['publication_status', 'edition__edition_type',
                   'edition__edition_subtype', LibraryFilter]

    actions = ['mark_as_written_off', 'create_depository_fund_element', 'replacement']

    def author(self, obj: BaseFundElement):
        try:
            return obj.edition.author if obj.edition.author else '-'
        except Exception as e:
            return ''

    author.short_description = _('Author')

    def title(self, obj: BaseFundElement):
        try:
            return obj.edition.title if obj.edition.title else '-'
        except Exception as e:
            return ''

    title.short_description = _('Edition title')

    def edition_type(self, obj: BaseFundElement):
        try:
            edition_type_value = obj.edition.edition_type
            if edition_type_value:
                return dict(obj.edition.TYPES).get(edition_type_value, '-')
            return '-'
        except Exception as _:
            return ''

    edition_type.short_description = _('Edition type')

    def edition_subtype(self, obj: BaseFundElement):
        try:
            edition_subtype_value = obj.edition.edition_subtype
            if edition_subtype_value:
                return dict(obj.edition.SUBTYPES).get(edition_subtype_value, '-')
            return '-'
        except:
            return ''

    edition_subtype.short_description = _('Edition subtype')

    def year(self, obj: BaseFundElement):
        try:
            return obj.edition.year if obj.edition.year else '-'
        except:
            return ''

    year.short_description = _('Year')

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = True
        return super(BaseFundElementFirstClassAdmin, self).changeform_view(request, object_id,
                                                                           extra_context=extra_context)

    def has_edit_permission(self, request, obj=None):
        return False

    def edition(self, obj: BaseFundElement):
        return obj.arrival if obj.arrival else ''

    @transaction.atomic
    def save_model(self, request, obj: BaseFundElement, form, change):
        if obj.pk is None:
            last_fund_element: BaseFundElement = BaseFundElement.objects.filter(
                edition__edition_subtype=obj.edition.edition_subtype).last()
            index = 1
            if last_fund_element:
                index = int(last_fund_element.inventory_number.split('/')[1])
            number_prefix = BaseArrivalAdmin.SUBTYPES[obj.edition.edition_subtype]
            obj.inventory_number = f'{number_prefix}/{index + 1}'
            if obj.arrival:
                obj.library = obj.arrival.library
            else:
                user = Reader.objects.filter(user=request.user).first()
                if user:
                    obj.library = user.library
                else:
                    obj.library = ''
            obj.save()

        super().save_model(request, obj, form, change)

    @transaction.atomic
    def mark_as_written_off(self, request, queryset):
        if request.method == "POST":

            elements_with_links = []
            for element in queryset:
                if self.write_off_act_link(element) != "-":
                    elements_with_links.append(element.inventory_number)

            if elements_with_links:
                element_ids = ", ".join(map(str, elements_with_links))
                messages.error(
                    request,
                    f"Невозможно списать: для следующих элементов уже существуют акты списания: {element_ids}"
                )
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            already_written_off = queryset.filter(publication_status='WRITTEN_OFF')
            if already_written_off.exists():
                element_ids = ", ".join(map(str, already_written_off.values_list('inventory_number', flat=True)))
                messages.error(request, f"Следующие элементы уже были списаны: {element_ids}")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            basis_for_write_off = request.POST.get('basis_for_write_off', '')

            selected_elements = queryset.values('id', 'inventory_number',
                                                'edition__edition_subtype',
                                                'edition__edition_type')

            unique_types = set(
                selected_elements.values_list('edition__edition_type', flat=True))

            if len(unique_types) > 1:
                messages.error(request,
                               "Выбранные элементы должны быть одного типа: либо периодические, либо непериодические.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            edition_type = list(unique_types)[0]
            if edition_type == 'PERIODICAL':
                unique_subtypes = set(
                    selected_elements.values_list('edition__edition_subtype', flat=True))
                if len(unique_subtypes) > 1:
                    messages.error(request,
                                   "Все выбранные элементы должны быть одного подтипа (например, только MAGAZINES или только NEWSPAPERS).")
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            element_count_by_type = {}
            inventory_numbers = []
            write_off_acts = {}

            for element in selected_elements:
                inventory_number = element.get('inventory_number')
                if inventory_number is None:
                    continue

                inventory_numbers.append(inventory_number)
                edition_type = element['edition__edition_subtype']

                if edition_type not in element_count_by_type:
                    element_count_by_type[edition_type] = 0
                element_count_by_type[edition_type] += 1

                if edition_type in ['MAGAZINES', 'NEWSPAPERS']:
                    act_key = 'MAGAZINES' if edition_type == 'MAGAZINES' else 'NEWSPAPERS'
                    if act_key not in write_off_acts:
                        write_off_acts[act_key] = WriteOffActJournal.objects.create(
                            basis_for_write_off=basis_for_write_off,
                            submitted_by=request.user.id,
                            registered_by=request.user.id
                        ) if edition_type == 'MAGAZINES' else WriteOffActFiles.objects.create(
                            basis_for_write_off=basis_for_write_off,
                            submitted_by=request.user.id,
                            registered_by=request.user.id
                        )
                elif edition_type in dict(BaseFundElement.NON_PERIODICAL_SUBTYPES).keys():
                    if 'NON_PERIODICAL' not in write_off_acts:
                        write_off_acts['NON_PERIODICAL'] = WriteOffActNotPeriodicals.objects.create(
                            basis_for_write_off=basis_for_write_off,
                            submitted_by=request.user.id,
                            registered_by=request.user.id,
                        )

            for act_type, write_off_act in write_off_acts.items():
                elements_info = []

                for edition_type, count in element_count_by_type.items():
                    year = ""
                    for element in selected_elements:
                        if element['edition__edition_subtype'] == edition_type:
                            year = element.get('edition__year', '')
                            break

                    if year:
                        elements_info.append(
                            f"{self.get_display_name(edition_type, BaseFundElement.TYPES)} - {year} - {count}")
                    else:
                        elements_info.append(f"{self.get_display_name(edition_type, BaseFundElement.TYPES)} - {count}")

                write_off_act.selected_elements_info = "\n".join(elements_info)
                write_off_act.inventory_number = ", ".join(inventory_numbers)
                write_off_act.total_excluded = queryset.count()
                write_off_act.save()

            queryset.update(publication_status='WRITTEN_OFF')

            selected_ids = list(queryset.values_list('id', flat=True))
            selected_ids_str = ",".join(map(str, selected_ids))
            redirect_url = None

            for act_type, write_off_act in write_off_acts.items():
                if act_type == 'MAGAZINES':
                    redirect_url = f"/admin/klib/writeoffactjournal/{write_off_act.pk}/change/?selected_ids={selected_ids_str}"
                elif act_type == 'NEWSPAPERS':
                    redirect_url = f"/admin/klib/writeoffactfiles/{write_off_act.pk}/change/?selected_ids={selected_ids_str}"
                elif act_type == 'NON_PERIODICAL':
                    redirect_url = f"/admin/klib/writeoffactnotperiodicals/{write_off_act.pk}/change/?selected_ids={selected_ids_str}"

                # request.session['write_off_act_id'] = write_off_act.id

                editions_without_active_elements = (
                    BaseEdition.objects.annotate(
                        has_active_elements=Exists(
                            BaseFundElement.objects.filter(
                                edition=OuterRef('pk')
                            ).exclude(publication_status='WRITTEN_OFF')
                        )
                    ).filter(has_active_elements=False).values('id', 'title')
                )

                if editions_without_active_elements.exists():
                    for edition in editions_without_active_elements:
                        sku = Belmarc.objects.filter(edition_id=edition['id']).first()
                        if sku:
                            try:
                                url = f'http://belrw-search:8080/public/search/sku/delete/{sku.id}'
                                response = requests.get(url)
                                response.raise_for_status()
                            except requests.exceptions.RequestException as e:
                                logger.error(f"Error sending DELETE request: {e}")

            if redirect_url:
                return HttpResponseRedirect(redirect_url)

    mark_as_written_off.short_description = _("Mark as decommissioned")

    @transaction.atomic
    def create_depository_fund_element(self, request, queryset):

        elements_with_links = []
        for element in queryset:
            if self.write_off_act_link(element) != "-":
                elements_with_links.append(element.inventory_number)

        if elements_with_links:
            element_ids = ", ".join(map(str, elements_with_links))
            messages.error(
                request,
                f"Невозможно создать депонированный фонд: для следующих элементов уже существуют акты списания: {element_ids}"
            )
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        selected_elements = queryset.values('id', 'inventory_number', 'edition__edition_subtype',
                                            'edition__edition_type')
        unique_types = set(selected_elements.values_list('edition__edition_type', flat=True))

        if len(unique_types) > 1:
            messages.error(request, "Выбранные элементы должны быть одного типа.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        edition_type = list(unique_types)[0]

        depository_fund_element = DepositoryFundElement.objects.create(
            act_date=timezone.now(),
            basis_for_write_off="Основание для депонирования",
            submitted_by=request.user.id,
            registered_by=request.user.id
        )

        inventory_numbers = []
        elements_info = []
        for element in selected_elements:
            inventory_number = element.get('inventory_number')
            if inventory_number:
                inventory_numbers.append(inventory_number)
                edition_subtype = element.get('edition__edition_subtype')
                year = element.get('edition__year', '-')
                elements_info.append(
                    f"{self.get_display_name(edition_subtype, BaseFundElement.STATUS)} - {year} - {inventory_number}"
                )

        depository_fund_element.selected_elements_info = "\n".join(elements_info)
        depository_fund_element.inventory_number = ", ".join(inventory_numbers)
        depository_fund_element.total_excluded = queryset.count()
        depository_fund_element.save()

        queryset.update(publication_status='IN_THE_DEPOSITORY_FUND')

        selected_ids = list(queryset.values_list('id', flat=True))
        selected_ids_str = ",".join(map(str, selected_ids))
        redirect_url = f"/admin/klib/depositoryfundelement/{depository_fund_element.pk}/change/?selected_ids={selected_ids_str}"

        return HttpResponseRedirect(redirect_url)

    create_depository_fund_element.short_description = "Депозитарный фонд"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('replacement/',
                 self.admin_site.admin_view(self.replacement_view),
                 name='klib_basefundelement_changelist_replacement'),
        ]
        return custom_urls + urls

    def replacement(self, request, queryset):
        # Метод для обработки action
        if not queryset:
            messages.error(request, "Не выбраны элементы для замены")
            return

        replacement_act = ReplacementAct.objects.create(
            # basis_for_write_off="Основание для замены",
            submitted_by=request.user.id,
            registered_by=request.user.id
        )
        request.session['replacement_act_id'] = replacement_act.pk
        request.session['replacement_queue'] = list(queryset.values_list('id', flat=True))

        return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist_replacement'))

    def replacement_view(self, request):

        if 'replacement_queue' not in request.session:
            logger.warning("No replacement queue in session")
            messages.error(request, "Нет элементов для замены")
            return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist'))

        if not request.session['replacement_queue']:
            logger.info("Queue is empty, redirecting to act page")
            act_id = request.session['replacement_act_id']
            del request.session['replacement_queue']
            del request.session['replacement_act_id']
            return HttpResponseRedirect(f"/admin/klib/replacementact/{act_id}/change/")

        try:
            element_id = request.session['replacement_queue'][0]

            element = BaseFundElement.objects.get(id=element_id)
            replacement_act = ReplacementAct.objects.get(pk=request.session['replacement_act_id'])

            existing_replace = ReplaceEdition.objects.filter(
                replaceable_edition=element,
                act=replacement_act
            ).first()

            if existing_replace:
                logger.warning(f"ReplaceEdition already exists for element_id={element_id}")
                # Удаляем обработанный элемент из очереди
                request.session['replacement_queue'] = request.session['replacement_queue'][1:]
                request.session.modified = True
                return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist_replacement'))

            replace_edition = ReplaceEdition.objects.create(
                replaceable_edition=element,
                act=replacement_act
            )
            logger.info(f"Created new ReplaceEdition with id={replace_edition.pk}")

            return HttpResponseRedirect(f"/admin/klib/replaceedition/{replace_edition.pk}/change/")
        except (BaseFundElement.DoesNotExist, ReplacementAct.DoesNotExist) as e:
            messages.error(request, f"Ошибка при создании замены: {str(e)}")
            return HttpResponseRedirect(reverse('admin:klib_basefundelement_changelist'))

    replacement.short_description = "Замена"


my_admin_site.register(BaseFundElementFirstClass, BaseFundElementFirstClassAdmin)


# Фонд газеты
@admin.register(BaseFundElementNewspapers)
class BaseFundElementNewspapersAdmin(admin.ModelAdmin):
    list_display = ['registration_date', 'inventory_number', 'title', 'year', 'invoice_number',
                    'publication_status', 'write_off_act_link', 'is_booked']
    readonly_fields = ['id', 'registration_date', 'inventory_number', 'price', 'author', 'title', 'year',
                       'price_with_vat', 'vat_amount', 'invoice_number', 'invoice_date', 'edition_type',
                       'edition_subtype', 'publication_status', 'edition_number', 'double_number',
                       'second_edition_number', 'is_booked', 'subscription']

    list_filter = ['arrival__order_edition__edition__title',
                   'inventory_number',
                   'publication_status',
                   'arrival__order_edition__order__completion_date']
    search_fields = ['inventory_number']

    labels = {
        'currency': 'Издание'
    }
    actions = ['mark_as_written_off']

    def has_add_permission(self, request, obj=None):
        return False

    def double_number(self, obj: BaseFundElementNewspapers):
        return 'Да' if obj.arrival.double_number else 'Нет'

    def edition_number(self, obj: BaseFundElementNewspapers):
        return obj.arrival.edition_number if obj.arrival.edition_number else '-'

    def second_edition_number(self, obj: BaseFundElementNewspapers):
        return obj.arrival.second_edition_number if obj.arrival.second_edition_number else '-'

    double_number.short_description = _('Double number')
    edition_number.short_description = _('Edition Number')
    second_edition_number.short_description = _('Second Edition Number')

    def write_off_act_link(self, obj):
        inventory_numbers = re.split(r',\s*', obj.inventory_number)

        write_off_acts_journal = WriteOffActJournal.objects.filter(inventory_number__icontains=obj.inventory_number)
        write_off_acts_not_periodicals = WriteOffActNotPeriodicals.objects.filter(
            inventory_number__icontains=obj.inventory_number)
        write_off_acts_files = WriteOffActFiles.objects.filter(inventory_number__icontains=obj.inventory_number)

        write_off_acts = list(write_off_acts_journal) + list(write_off_acts_not_periodicals) + list(
            write_off_acts_files)

        if write_off_acts:
            urls = []
            for write_off_act in write_off_acts:
                if isinstance(write_off_act, WriteOffActJournal):
                    url = f'/admin/klib/writeoffactjournal/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActNotPeriodicals):
                    url = f'/admin/klib/writeoffactnotperiodicals/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActFiles):
                    url = f'/admin/klib/writeoffactfiles/{write_off_act.id}/change/'
                else:
                    continue

                urls.append(f'<a href="{url}">акт списания {write_off_act.id}</a>')

            return format_html('<br>'.join(urls))
        return '-'

    write_off_act_link.short_description = _("Viewing the debit statement")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(edition__edition_subtype='NEWSPAPERS')

        publication_status = request.GET.get('publication_status__exact')
        if publication_status:
            qs = qs.filter(publication_status=publication_status)

        user_library = get_user_library(request.user)
        if user_library:
            qs = qs.filter(library=user_library)

        return qs

    def author(self, obj: BaseFundElementNewspapers):
        try:
            return obj.arrival.order_edition.edition.author if obj.arrival.order_edition.edition.author else '-'
        except Exception:
            return ''

    author.short_description = _('Author')

    def title(self, obj: BaseFundElementNewspapers):
        try:
            return obj.arrival.order_edition.edition.title if obj.arrival.order_edition.edition.title else '-'
        except Exception:
            return ''

    title.short_description = _('Edition title')

    def edition_type(self, obj: BaseFundElementNewspapers):
        try:
            edition_type_value = obj.arrival.order_edition.edition.edition_type
            if edition_type_value:
                return dict(obj.arrival.order_edition.edition.TYPES).get(edition_type_value, '-')
            return '-'
        except Exception:
            return ''

    edition_type.short_description = _('Edition type')

    def edition_subtype(self, obj: BaseFundElementNewspapers):
        try:
            edition_subtype_value = obj.arrival.order_edition.edition.edition_subtype
            if edition_subtype_value:
                return dict(obj.arrival.order_edition.edition.SUBTYPES).get(edition_subtype_value, '-')
            return '-'
        except Exception:
            return ''

    edition_subtype.short_description = _('Edition subtype')

    def year(self, obj: BaseFundElementNewspapers):
        try:
            return obj.arrival.order_edition.order.year if obj.arrival.order_edition.order.year else '-'
        except:
            return ''

    year.short_description = _('Year')

    @transaction.atomic
    def mark_as_written_off(self, request, queryset):
        if not queryset:
            queryset = self.get_queryset(request)

        current_date = timezone.now().date()
        expired_elements = queryset.filter(
            arrival__order_edition__order__contract_date__isnull=False,
            arrival__order_edition__order__duration_of_storage__isnull=False
        ).annotate(
            expiry_date=ExpressionWrapper(
                F('arrival__order_edition__order__contract_date') +
                ExpressionWrapper(F('arrival__order_edition__order__duration_of_storage') * Value(30),
                                  output_field=DateField()),
                output_field=DateField()
            )
        ).filter(expiry_date__lt=current_date)

        if not expired_elements.exists():
            messages.error(request, "Нет элементов с истекшим сроком хранения для списания.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        basis_for_write_off = request.POST.get('basis_for_write_off', '')
        write_off_acts = {}
        inventory_numbers = []

        for element in expired_elements:
            inventory_numbers.append(element.inventory_number)
            edition_type = element.arrival.order_edition.edition.edition_subtype
            subscription_value = element.subscription

            if edition_type == 'MAGAZINES':
                if 'MAGAZINES' not in write_off_acts:
                    write_off_acts['MAGAZINES'] = WriteOffActJournal.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id
                    )
            elif edition_type == 'NEWSPAPERS':
                if 'NEWSPAPERS' not in write_off_acts:
                    write_off_acts['NEWSPAPERS'] = WriteOffActFiles.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id,
                        subscription=subscription_value
                    )
            else:
                if 'NON_PERIODICAL' not in write_off_acts:
                    write_off_acts['NON_PERIODICAL'] = WriteOffActNotPeriodicals.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id,
                    )

        for act_type, write_off_act in write_off_acts.items():
            if write_off_act:
                write_off_act.inventory_number = ", ".join(inventory_numbers)
                write_off_act.total_excluded = expired_elements.count()
                write_off_act.save()

        updated_count = expired_elements.update(publication_status='WRITTEN_OFF')
        messages.success(request, "Акты списания успешно созданы для выбранных элементов с истекшим сроком хранения.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

    mark_as_written_off.short_description = _("Mark as decommissioned")

    # для автоматического выбора всех записей при пустом выборе
    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] == 'mark_as_written_off' and not request.POST.getlist(
                '_selected_action'):
            post = request.POST.copy()
            post.setlist('_selected_action', [str(obj.id) for obj in self.get_queryset(request)])
            request._set_post(post)

        return super().changelist_view(request, extra_context)


my_admin_site.register(BaseFundElementNewspapers, BaseFundElementNewspapersAdmin)


class BaseFundElementNewspapersFirstClassAdmin(admin.ModelAdmin):
    list_display = ['registration_date', 'library', 'inventory_number', 'author', 'title', 'year', 'invoice_number',
                    'edition_type', 'edition_subtype', 'publication_status', 'write_off_act_link', 'is_booked']
    readonly_fields = ['id', 'registration_date', 'inventory_number', 'price', 'author', 'title', 'year',
                       'price_with_vat', 'vat_amount', 'invoice_number', 'invoice_date', 'edition_type',
                       'edition_subtype', 'publication_status', 'edition_number', 'double_number',
                       'second_edition_number', 'is_booked', 'subscription']

    list_filter = ['publication_status', 'edition__edition_type',
                   'edition__edition_subtype', LibraryFilter]

    labels = {
        'currency': 'Издание'
    }
    actions = ['mark_as_written_off']

    def has_add_permission(self, request, obj=None):
        return False

    def double_number(self, obj: BaseFundElementNewspapersFirstClass):
        return 'Да' if obj.arrival.double_number else 'Нет'

    def edition_number(self, obj: BaseFundElementNewspapersFirstClass):
        return obj.arrival.edition_number if obj.arrival.edition_number else '-'

    def second_edition_number(self, obj: BaseFundElementNewspapersFirstClass):
        return obj.arrival.second_edition_number if obj.arrival.second_edition_number else '-'

    double_number.short_description = _('Double number')
    edition_number.short_description = _('Edition Number')
    second_edition_number.short_description = _('Second Edition Number')

    def write_off_act_link(self, obj):
        inventory_numbers = re.split(r',\s*', obj.inventory_number)

        write_off_acts_journal = WriteOffActJournal.objects.filter(inventory_number__icontains=obj.inventory_number)
        write_off_acts_not_periodicals = WriteOffActNotPeriodicals.objects.filter(
            inventory_number__icontains=obj.inventory_number)
        write_off_acts_files = WriteOffActFiles.objects.filter(inventory_number__icontains=obj.inventory_number)

        write_off_acts = list(write_off_acts_journal) + list(write_off_acts_not_periodicals) + list(
            write_off_acts_files)

        if write_off_acts:
            urls = []
            for write_off_act in write_off_acts:
                if isinstance(write_off_act, WriteOffActJournal):
                    url = f'/admin/klib/writeoffactjournal/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActNotPeriodicals):
                    url = f'/admin/klib/writeoffactnotperiodicals/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActFiles):
                    url = f'/admin/klib/writeoffactfiles/{write_off_act.id}/change/'
                else:
                    continue

                urls.append(f'<a href="{url}">акт списания {write_off_act.id}</a>')

            return format_html('<br>'.join(urls))
        return '-'

    write_off_act_link.short_description = _("Viewing the debit statement")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(edition__edition_subtype='NEWSPAPERS')

        publication_status = request.GET.get('publication_status__exact')
        if publication_status:
            qs = qs.filter(publication_status=publication_status)

        return qs

    def author(self, obj: BaseFundElementNewspapersFirstClass):
        try:
            return obj.arrival.order_edition.edition.author if obj.arrival.order_edition.edition.author else '-'
        except Exception:
            return ''

    author.short_description = _('Author')

    def title(self, obj: BaseFundElementNewspapersFirstClass):
        try:
            return obj.arrival.order_edition.edition.title if obj.arrival.order_edition.edition.title else '-'
        except Exception:
            return ''

    title.short_description = _('Edition title')

    def edition_type(self, obj: BaseFundElementNewspapersFirstClass):
        try:
            edition_type_value = obj.arrival.order_edition.edition.edition_type
            if edition_type_value:
                return dict(obj.arrival.order_edition.edition.TYPES).get(edition_type_value, '-')
            return '-'
        except Exception:
            return ''

    edition_type.short_description = _('Edition type')

    def edition_subtype(self, obj: BaseFundElementNewspapersFirstClass):
        try:
            edition_subtype_value = obj.arrival.order_edition.edition.edition_subtype
            if edition_subtype_value:
                return dict(obj.arrival.order_edition.edition.SUBTYPES).get(edition_subtype_value, '-')
            return '-'
        except Exception:
            return ''

    edition_subtype.short_description = _('Edition subtype')

    def year(self, obj: BaseFundElementNewspapersFirstClass):
        try:
            return obj.arrival.order_edition.order.year if obj.arrival.order_edition.order.year else '-'
        except:
            return ''

    year.short_description = _('Year')

    @transaction.atomic
    def mark_as_written_off(self, request, queryset):
        if not queryset:
            queryset = self.get_queryset(request)

        objects_with_write_off_link = [
            obj for obj in queryset if self.write_off_act_link(obj) != '-'
        ]

        if objects_with_write_off_link:
            messages.error(request,
                           "Невозможно выполнить действие, так как для некоторых элементов уже существуют записи в поле 'акт списания'.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        current_date = timezone.now().date()
        expired_elements = queryset.filter(
            arrival__order_edition__order__contract_date__isnull=False,
            arrival__order_edition__order__duration_of_storage__isnull=False
        ).annotate(
            expiry_date=ExpressionWrapper(
                F('arrival__order_edition__order__contract_date') +
                ExpressionWrapper(F('arrival__order_edition__order__duration_of_storage') * Value(30),
                                  output_field=DateField()),
                output_field=DateField()
            )
        ).filter(expiry_date__lt=current_date)

        if not expired_elements.exists():
            messages.error(request, "Нет элементов с истекшим сроком хранения для списания.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        basis_for_write_off = request.POST.get('basis_for_write_off', '')
        write_off_acts = {}
        inventory_numbers = []

        for element in expired_elements:
            inventory_numbers.append(element.inventory_number)
            edition_type = element.arrival.order_edition.edition.edition_subtype
            subscription_value = element.subscription

            if edition_type == 'MAGAZINES':
                if 'MAGAZINES' not in write_off_acts:
                    write_off_acts['MAGAZINES'] = WriteOffActJournal.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id
                    )
            elif edition_type == 'NEWSPAPERS':
                if 'NEWSPAPERS' not in write_off_acts:
                    write_off_acts['NEWSPAPERS'] = WriteOffActFiles.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id,
                        subscription=subscription_value
                    )
            else:
                if 'NON_PERIODICAL' not in write_off_acts:
                    write_off_acts['NON_PERIODICAL'] = WriteOffActNotPeriodicals.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id,
                    )

        for act_type, write_off_act in write_off_acts.items():
            if write_off_act:
                write_off_act.inventory_number = ", ".join(inventory_numbers)
                write_off_act.total_excluded = expired_elements.count()
                write_off_act.save()

        updated_count = expired_elements.update(publication_status='WRITTEN_OFF')
        messages.success(request, "Акты списания успешно созданы для выбранных элементов с истекшим сроком хранения.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

    mark_as_written_off.short_description = _("Mark as decommissioned")

    # для автоматического выбора всех записей при пустом выборе
    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] == 'mark_as_written_off' and not request.POST.getlist(
                '_selected_action'):
            post = request.POST.copy()
            post.setlist('_selected_action', [str(obj.id) for obj in self.get_queryset(request)])
            request._set_post(post)

        return super().changelist_view(request, extra_context)


my_admin_site.register(BaseFundElementNewspapersFirstClass, BaseFundElementNewspapersFirstClassAdmin)


# Фонд журналы
@admin.register(BaseFundElementMagazines)
class BaseFundElementMagazinesAdmin(admin.ModelAdmin):
    list_display = ['registration_date', 'inventory_number', 'title', 'year', 'invoice_number',
                    'publication_status', 'write_off_act_link', 'is_booked']
    readonly_fields = ['id', 'registration_date', 'inventory_number', 'price', 'author', 'title', 'year',
                       'price_with_vat', 'vat_amount', 'invoice_number', 'invoice_date', 'edition_type',
                       'edition_subtype', 'publication_status', 'edition_number', 'double_number',
                       'second_edition_number', 'is_booked']

    list_filter = ['arrival__order_edition__edition__title',
                   'inventory_number',
                   'publication_status',
                   'arrival__order_edition__order__completion_date']
    search_fields = ['inventory_number']
    labels = {'currency': 'Издание'}
    actions = ['mark_as_written_off']

    def has_add_permission(self, request, obj=None):
        return False

    def double_number(self, obj):
        return 'Да' if obj.arrival.double_number else 'Нет'

    def edition_number(self, obj):
        return obj.arrival.edition_number if obj.arrival.edition_number else '-'

    def second_edition_number(self, obj):
        return obj.arrival.second_edition_number if obj.arrival.second_edition_number else '-'

    double_number.short_description = _('Double number')
    edition_number.short_description = _('Edition Number')
    second_edition_number.short_description = _('Second Edition Number')

    def write_off_act_link(self, obj):
        inventory_numbers = re.split(r',\s*', obj.inventory_number)

        write_off_acts_journal = WriteOffActJournal.objects.filter(inventory_number__icontains=obj.inventory_number)
        write_off_acts_not_periodicals = WriteOffActNotPeriodicals.objects.filter(
            inventory_number__icontains=obj.inventory_number)
        write_off_acts_files = WriteOffActFiles.objects.filter(inventory_number__icontains=obj.inventory_number)

        write_off_acts = list(write_off_acts_journal) + list(write_off_acts_not_periodicals) + list(
            write_off_acts_files)

        if write_off_acts:
            urls = []
            for write_off_act in write_off_acts:
                if isinstance(write_off_act, WriteOffActJournal):
                    url = f'/admin/klib/writeoffactjournal/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActNotPeriodicals):
                    url = f'/admin/klib/writeoffactnotperiodicals/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActFiles):
                    url = f'/admin/klib/writeoffactfiles/{write_off_act.id}/change/'
                else:
                    continue

                urls.append(f'<a href="{url}">акт списания {write_off_act.id}</a>')

            return format_html('<br>'.join(urls))
        return '-'

    write_off_act_link.short_description = _("Viewing the debit statement")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(edition__edition_subtype='MAGAZINES')

        publication_status = request.GET.get('publication_status__exact')
        if publication_status:
            qs = qs.filter(publication_status=publication_status)

        user_library = get_user_library(request.user)
        if user_library:
            qs = qs.filter(library=user_library)

        return qs

    def author(self, obj):
        try:
            return obj.arrival.order_edition.edition.author if obj.arrival.order_edition.edition.author else '-'
        except Exception:
            return ''

    author.short_description = _('Author')

    def title(self, obj):
        try:
            return obj.arrival.order_edition.edition.title if obj.arrival.order_edition.edition.title else '-'
        except Exception:
            return ''

    title.short_description = _('Edition title')

    def edition_type(self, obj):
        try:
            edition_type_value = obj.arrival.order_edition.edition.edition_type
            if edition_type_value:
                return dict(obj.arrival.order_edition.edition.TYPES).get(edition_type_value, '-')
            return '-'
        except Exception:
            return ''

    edition_type.short_description = _('Edition type')

    def edition_subtype(self, obj):
        try:
            edition_subtype_value = obj.arrival.order_edition.edition.edition_subtype
            if edition_subtype_value:
                return dict(obj.arrival.order_edition.edition.SUBTYPES).get(edition_subtype_value, '-')
            return '-'
        except Exception:
            return ''

    edition_subtype.short_description = _('Edition subtype')

    def year(self, obj):
        try:
            return obj.arrival.order_edition.order.year if obj.arrival.order_edition.order.year else '-'
        except:
            return ''

    year.short_description = _('Year')

    @transaction.atomic
    def mark_as_written_off(self, request, queryset):
        if not queryset:
            queryset = self.get_queryset(request)

        objects_with_write_off_link = [
            obj for obj in queryset if self.write_off_act_link(obj) != '-'
        ]

        if objects_with_write_off_link:
            messages.error(request,
                           "Невозможно выполнить действие, так как для некоторых элементов уже существуют записи в поле 'акт списания'.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        current_date = timezone.now().date()
        expired_elements = queryset.filter(
            arrival__order_edition__order__contract_date__isnull=False,
            arrival__order_edition__order__duration_of_storage__isnull=False
        ).annotate(
            expiry_date=ExpressionWrapper(
                F('arrival__order_edition__order__contract_date') +
                ExpressionWrapper(F('arrival__order_edition__order__duration_of_storage') * Value(30),
                                  output_field=DateField()),
                output_field=DateField()
            )
        ).filter(expiry_date__lt=current_date)

        if not expired_elements.exists():
            messages.error(request, "Нет элементов с истекшим сроком хранения для списания.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        basis_for_write_off = request.POST.get('basis_for_write_off', '')
        write_off_acts = {}
        inventory_numbers = []

        for element in expired_elements:
            inventory_numbers.append(element.inventory_number)
            edition_type = element.arrival.order_edition.edition.edition_subtype

            if edition_type == 'MAGAZINES':
                if 'MAGAZINES' not in write_off_acts:
                    write_off_acts['MAGAZINES'] = WriteOffActJournal.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id
                    )
            elif edition_type == 'NEWSPAPERS':
                if 'NEWSPAPERS' not in write_off_acts:
                    write_off_acts['NEWSPAPERS'] = WriteOffActFiles.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id
                    )
            else:
                if 'NON_PERIODICAL' not in write_off_acts:
                    write_off_acts['NON_PERIODICAL'] = WriteOffActNotPeriodicals.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id,
                    )

        for act_type, write_off_act in write_off_acts.items():
            if write_off_act:
                write_off_act.inventory_number = ", ".join(inventory_numbers)
                write_off_act.total_excluded = expired_elements.count()
                write_off_act.save()

        updated_count = expired_elements.update(publication_status='WRITTEN_OFF')
        messages.success(request, "Акты списания успешно созданы для выбранных элементов с истекшим сроком хранения.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

    mark_as_written_off.short_description = _("Mark as decommissioned")

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] == 'mark_as_written_off' and not request.POST.getlist(
                '_selected_action'):
            post = request.POST.copy()
            post.setlist('_selected_action', [str(obj.id) for obj in self.get_queryset(request)])
            request._set_post(post)

        return super().changelist_view(request, extra_context)


my_admin_site.register(BaseFundElementMagazines, BaseFundElementMagazinesAdmin)


# Фонд журналы для первого класса
class BaseFundElementMagazinesFirstClassAdmin(admin.ModelAdmin):
    list_display = ['registration_date', 'inventory_number', 'author', 'title', 'year', 'invoice_number',
                    'edition_type', 'edition_subtype', 'publication_status', 'write_off_act_link', 'is_booked']
    readonly_fields = ['id', 'registration_date', 'inventory_number', 'price', 'author', 'title', 'year',
                       'price_with_vat', 'vat_amount', 'invoice_number', 'invoice_date', 'edition_type',
                       'edition_subtype', 'publication_status', 'edition_number', 'double_number',
                       'second_edition_number', 'is_booked']

    list_filter = ['publication_status', 'arrival__order_edition__edition__edition_type',
                   'arrival__order_edition__edition__edition_subtype', LibraryFilter]
    labels = {'currency': 'Издание'}
    actions = ['mark_as_written_off']

    def has_add_permission(self, request, obj=None):
        return False

    def double_number(self, obj):
        return 'Да' if obj.arrival.double_number else 'Нет'

    def edition_number(self, obj):
        return obj.arrival.edition_number if obj.arrival.edition_number else '-'

    def second_edition_number(self, obj):
        return obj.arrival.second_edition_number if obj.arrival.second_edition_number else '-'

    double_number.short_description = _('Double number')
    edition_number.short_description = _('Edition Number')
    second_edition_number.short_description = _('Second Edition Number')

    def write_off_act_link(self, obj):
        inventory_numbers = re.split(r',\s*', obj.inventory_number)

        write_off_acts_journal = WriteOffActJournal.objects.filter(inventory_number__icontains=obj.inventory_number)
        write_off_acts_not_periodicals = WriteOffActNotPeriodicals.objects.filter(
            inventory_number__icontains=obj.inventory_number)
        write_off_acts_files = WriteOffActFiles.objects.filter(inventory_number__icontains=obj.inventory_number)

        write_off_acts = list(write_off_acts_journal) + list(write_off_acts_not_periodicals) + list(
            write_off_acts_files)

        if write_off_acts:
            urls = []
            for write_off_act in write_off_acts:
                if isinstance(write_off_act, WriteOffActJournal):
                    url = f'/admin/klib/writeoffactjournal/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActNotPeriodicals):
                    url = f'/admin/klib/writeoffactnotperiodicals/{write_off_act.id}/change/'
                elif isinstance(write_off_act, WriteOffActFiles):
                    url = f'/admin/klib/writeoffactfiles/{write_off_act.id}/change/'
                else:
                    continue

                urls.append(f'<a href="{url}">акт списания {write_off_act.id}</a>')

            return format_html('<br>'.join(urls))
        return '-'

    write_off_act_link.short_description = _("Viewing the debit statement")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(edition__edition_subtype='MAGAZINES')

        publication_status = request.GET.get('publication_status__exact')
        if publication_status:
            qs = qs.filter(publication_status=publication_status)

        return qs

    def author(self, obj):
        try:
            return obj.arrival.order_edition.edition.author if obj.arrival.order_edition.edition.author else '-'
        except Exception:
            return ''

    author.short_description = _('Author')

    def title(self, obj):
        try:
            return obj.arrival.order_edition.edition.title if obj.arrival.order_edition.edition.title else '-'
        except Exception:
            return ''

    title.short_description = _('Edition title')

    def edition_type(self, obj):
        try:
            edition_type_value = obj.arrival.order_edition.edition.edition_type
            if edition_type_value:
                return dict(obj.arrival.order_edition.edition.TYPES).get(edition_type_value, '-')
            return '-'
        except Exception:
            return ''

    edition_type.short_description = _('Edition type')

    def edition_subtype(self, obj):
        try:
            edition_subtype_value = obj.arrival.order_edition.edition.edition_subtype
            if edition_subtype_value:
                return dict(obj.arrival.order_edition.edition.SUBTYPES).get(edition_subtype_value, '-')
            return '-'
        except Exception:
            return ''

    edition_subtype.short_description = _('Edition subtype')

    def year(self, obj):
        try:
            return obj.arrival.order_edition.order.year if obj.arrival.order_edition.order.year else '-'
        except:
            return ''

    year.short_description = _('Year')

    @transaction.atomic
    def mark_as_written_off(self, request, queryset):
        if not queryset:
            queryset = self.get_queryset(request)

        objects_with_write_off_link = [
            obj for obj in queryset if self.write_off_act_link(obj) != '-'
        ]

        if objects_with_write_off_link:
            messages.error(request,
                           "Невозможно выполнить действие, так как для некоторых элементов уже существуют записи в поле 'акт списания'.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        current_date = timezone.now().date()
        expired_elements = queryset.filter(
            arrival__order_edition__order__contract_date__isnull=False,
            arrival__order_edition__order__duration_of_storage__isnull=False
        ).annotate(
            expiry_date=ExpressionWrapper(
                F('arrival__order_edition__order__contract_date') +
                ExpressionWrapper(F('arrival__order_edition__order__duration_of_storage') * Value(30),
                                  output_field=DateField()),
                output_field=DateField()
            )
        ).filter(expiry_date__lt=current_date)

        if not expired_elements.exists():
            messages.error(request, "Нет элементов с истекшим сроком хранения для списания.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        basis_for_write_off = request.POST.get('basis_for_write_off', '')
        write_off_acts = {}
        inventory_numbers = []

        for element in expired_elements:
            inventory_numbers.append(element.inventory_number)
            edition_type = element.arrival.order_edition.edition.edition_subtype

            if edition_type == 'MAGAZINES':
                if 'MAGAZINES' not in write_off_acts:
                    write_off_acts['MAGAZINES'] = WriteOffActJournal.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id
                    )
            elif edition_type == 'NEWSPAPERS':
                if 'NEWSPAPERS' not in write_off_acts:
                    write_off_acts['NEWSPAPERS'] = WriteOffActFiles.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id
                    )
            else:
                if 'NON_PERIODICAL' not in write_off_acts:
                    write_off_acts['NON_PERIODICAL'] = WriteOffActNotPeriodicals.objects.create(
                        basis_for_write_off=basis_for_write_off,
                        submitted_by=request.user.id,
                        registered_by=request.user.id,
                    )

        for act_type, write_off_act in write_off_acts.items():
            if write_off_act:
                write_off_act.inventory_number = ", ".join(inventory_numbers)
                write_off_act.total_excluded = expired_elements.count()
                write_off_act.save()

        updated_count = expired_elements.update(publication_status='WRITTEN_OFF')
        messages.success(request, "Акты списания успешно созданы для выбранных элементов с истекшим сроком хранения.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

    mark_as_written_off.short_description = _("Mark as decommissioned")

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] == 'mark_as_written_off' and not request.POST.getlist(
                '_selected_action'):
            post = request.POST.copy()
            post.setlist('_selected_action', [str(obj.id) for obj in self.get_queryset(request)])
            request._set_post(post)

        return super().changelist_view(request, extra_context)


my_admin_site.register(BaseFundElementMagazinesFirstClass, BaseFundElementMagazinesFirstClassAdmin)


@admin.register(WriteOffActJournal)
class WriteOffActJournalAdmin(admin.ModelAdmin):
    list_display = ('act_number', 'act_date', 'basis_for_write_off', 'total_excluded', 'selected_elements_info')
    readonly_fields = ('act_number', 'act_date', 'total_excluded', 'selected_elements_info')
    fields = ['act_number', 'act_date', 'basis_for_write_off', 'selected_elements_info',
              'total_excluded', 'socio_economic_count', 'technical_count',
              'other_count', 'railway_theme_count', 'chairman', 'vice_chairman', 'member_1', 'member_2', 'member_3',
              'submitted_by', 'registered_by']

    form = WriteOffActForm

    def has_add_permission(self, request, obj=None):
        return False

    def get_display_name(self, key, choices):
        for choice_key, display_name in choices:
            if choice_key == key:
                return display_name
        return key

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_delete'] = False
        extra_context['show_history'] = False
        extra_context['show_close'] = False

        selected_ids = request.GET.get('selected_ids', '')
        if selected_ids:
            extra_context['selected_ids'] = selected_ids.split(',')

        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        selected_ids = request.GET.get('selected_ids', '')

        extra_context = extra_context or {}
        extra_context['selected_ids'] = selected_ids

        self.extra_context = extra_context
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)
        obj.act_number = obj.id
        obj.save(update_fields=['act_number'])

    def response_post_save_change(self, request, obj):
        document_stream = generate_act_document_journal(obj)

        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response

    def response_add(self, request, obj, post_url_continue=None):
        document_stream = generate_act_document_journal(obj)
        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response


my_admin_site.register(WriteOffActJournal, WriteOffActJournalAdmin)


@admin.register(WriteOffActNotPeriodicals)
class WriteOffActNotPeriodicalsAdmin(admin.ModelAdmin):
    list_display = ('act_number', 'act_date', 'basis_for_write_off', 'total_excluded', 'selected_elements_info')
    readonly_fields = ('act_number', 'act_date', 'total_excluded', 'selected_elements_info')
    fields = ['act_number', 'act_date', 'basis_for_write_off', 'selected_elements_info',
              'total_excluded', 'socio_economic_count', 'technical_count',
              'other_count', 'railway_theme_count', 'chairman', 'vice_chairman', 'member_1', 'member_2', 'member_3',
              'submitted_by', 'registered_by']

    form = WriteOffActForm

    def has_add_permission(self, request, obj=None):
        return False

    def get_display_name(self, key, choices):
        for choice_key, display_name in choices:
            if choice_key == key:
                return display_name
        return key

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_delete'] = False
        extra_context['show_history'] = False
        extra_context['show_close'] = False

        selected_ids = request.GET.get('selected_ids', '')
        if selected_ids:
            extra_context['selected_ids'] = selected_ids.split(',')

        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        selected_ids = request.GET.get('selected_ids', '')

        extra_context = extra_context or {}
        extra_context['selected_ids'] = selected_ids

        self.extra_context = extra_context
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)
        obj.act_number = obj.id
        obj.save(update_fields=['act_number'])

    def response_post_save_change(self, request, obj):
        document_stream = generate_act_document_not_periodicals(obj)

        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response

    def response_add(self, request, obj, post_url_continue=None):
        document_stream = generate_act_document_not_periodicals(obj)
        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response


my_admin_site.register(WriteOffActNotPeriodicals, WriteOffActNotPeriodicalsAdmin)


@admin.register(WriteOffActFiles)
class WriteOffActFilesAdmin(admin.ModelAdmin):
    list_display = ('act_number', 'act_date', 'basis_for_write_off', 'total_excluded', 'selected_elements_info')
    readonly_fields = ('act_number', 'act_date', 'total_excluded', 'selected_elements_info', 'subscription')
    fields = ['act_number', 'act_date', 'basis_for_write_off', 'selected_elements_info',
              'subscription', 'total_excluded', 'socio_economic_count', 'technical_count',
              'other_count', 'railway_theme_count', 'chairman', 'vice_chairman', 'member_1', 'member_2', 'member_3',
              'submitted_by', 'registered_by']

    form = WriteOffActFormTest

    def has_add_permission(self, request, obj=None):
        return False

    def get_display_name(self, key, choices):
        for choice_key, display_name in choices:
            if choice_key == key:
                return display_name
        return key

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_delete'] = False
        extra_context['show_history'] = False
        extra_context['show_close'] = False

        selected_ids = request.GET.get('selected_ids', '')
        if selected_ids:
            extra_context['selected_ids'] = selected_ids.split(',')

        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        selected_ids = request.GET.get('selected_ids', '')

        extra_context = extra_context or {}
        extra_context['selected_ids'] = selected_ids

        self.extra_context = extra_context
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)
        obj.act_number = obj.id
        obj.save(update_fields=['act_number'])

    def response_post_save_change(self, request, obj):
        document_stream = generate_act_document_files(obj)

        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response

    def response_add(self, request, obj, post_url_continue=None):
        document_stream = generate_act_document_files(obj)
        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response


my_admin_site.register(WriteOffActFiles, WriteOffActFilesAdmin)


@admin.register(DepositoryFundElement)
class DepositoryFundElementAdmin(admin.ModelAdmin):
    list_display = ('act_number', 'act_date', 'basis_for_write_off', 'total_excluded', 'selected_elements_info')
    readonly_fields = ('act_number', 'act_date', 'total_excluded', 'selected_elements_info')
    fields = ['act_number', 'act_date', 'basis_for_write_off', 'selected_elements_info',
              'total_excluded', 'socio_economic_count', 'technical_count',
              'other_count', 'railway_theme_count', 'chairman', 'vice_chairman', 'member_1', 'member_2', 'member_3',
              'submitted_by', 'registered_by']

    form = DepositoryFundElementForms

    def has_add_permission(self, request, obj=None):
        return False

    def get_display_name(self, key, choices):
        for choice_key, display_name in choices:
            if choice_key == key:
                return display_name
        return key

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_delete'] = False
        extra_context['show_history'] = False
        extra_context['show_close'] = False

        selected_ids = request.GET.get('selected_ids', '')
        if selected_ids:
            extra_context['selected_ids'] = selected_ids.split(',')

        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        selected_ids = request.GET.get('selected_ids', '')

        extra_context = extra_context or {}
        extra_context['selected_ids'] = selected_ids

        self.extra_context = extra_context
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)
        obj.act_number = obj.id
        obj.save(update_fields=['act_number'])

    def response_post_save_change(self, request, obj):
        document_stream = generate_act_document_depository(obj)

        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response

    def response_add(self, request, obj, post_url_continue=None):
        document_stream = generate_act_document_depository(obj)
        response = HttpResponse(document_stream,
                                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=act_{obj.act_number}.docx'
        return response


my_admin_site.register(DepositoryFundElement, DepositoryFundElementAdmin)


@admin.register(DigitalResource)
class DigitalResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'fund', 'resource', 'type', 'copyright')
    readonly_fields = ['id']
    fields = ['title', 'fund', 'resource', 'type', 'copyright']
    list_filter = ['title', 'fund', 'type']

    form = DigitalResourceForm

    def save_model(self, request, obj: DigitalResource, form, change):
        if obj.fund:
            obj.title = obj.fund.edition.title
        super().save_model(request, obj, form, change)


my_admin_site.register(DigitalResource, DigitalResourceAdmin)


@admin.register(OpenInventory)
class OpenInventoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


my_admin_site.register(OpenInventory, OpenInventoryAdmin)
