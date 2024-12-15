import json
import logging
from datetime import datetime, timedelta, date

from django.contrib import admin
from django.db.models import Sum
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.db.models import Count

from klib.models import BaseFundElement, BaseEdition, BaseOrder, BaseArrival, Edition, BaseOrderEdition
from kreport.constans import FIRST_BOOK_TYPE, SECOND_BOOK_TYPE, THEAD_BOOK_TYPE, MONTH_CHOICES, ALL_YEAR
from kreport.document_calculations import calculate_doc_start_total_document, calculate_doc_received_total_document, \
    calculate_doc_end_document, calculate_doc_start_accepted_to_balance, calculate_doc_received_accepted_to_balance, \
    calculate_doc_end_accepted_to_balance, calculate_doc_start_books, calculate_doc_received_books, \
    calculate_doc_end_books, calculate_doc_start_electronic_resources, calculate_doc_received_electronic_resources, \
    calculate_doc_end_electronic_resources, calculate_doc_start_brochures, calculate_doc_received_brochures, \
    calculate_doc_end_brochures, calculate_doc_start_ntd, calculate_doc_received_ntd, calculate_doc_end_ntd, \
    calculate_doc_start_information_sheets, calculate_doc_received_information_sheets, \
    calculate_doc_end_information_sheets, calculate_doc_start_magazines, calculate_doc_received_magazines, \
    calculate_doc_end_magazines, calculate_doc_start_newspapers, calculate_doc_received_newspapers, \
    calculate_doc_end_newspapers, get_month_date_range
from kreport.document_generator import build_context_document, create_docx
from kreport.forms import CreateInventoryBookForm, OrganisationForm, UserAccountingForm, DebtorsForm, CirculationForm
from kreport.models import CreateInventoryBook, CreateWorkplaceReport, BookIncompleteEdition, \
    CreateEducationReport, TotalBook, WorkplaceReportFirstClass, CreateEducationReportFirstClass, \
    UserAccountingFirstClass, BookIncompleteEditionNonPeriodicals, AccountiongStatement, \
    CertificateAcceptancePeriodicals, PeriodicalsAcceptanceReport, CreateDebtorsReport, CreateDebtorsReportFirstClass, \
    TypeOfService, BookCirculationReport, StorageReport, BookCirculationReportFirstClass
from kreport.models import CreateInventoryBook, CreateWorkplaceReport, BookIncompleteEdition, \
    CreateEducationReport, TotalBook, WorkplaceReportFirstClass, CreateEducationReportFirstClass, UserAccounting
from kreport.views import generate_workplace_report, generate_education_report, generate_book_incomplete_edition_report, \
    generate_workplace_report_first_class, generate_education_report_first_class, generate_total_book_report, \
    inventory_book_report, generate_user_accounting, generate_user_accounting_first_class, debtors_report, \
    debtors_report_first_class, generate_book_incomplete_edition_report_non_per, accountiong_statement_report, \
    certificate_acceptance_periodicals_report, periodicals_acceptance_report, typeofservice_report, \
    storage_report_admin, circulation_report, circulation_report_first_class
from kservice.models import Debtors, BookCirculation, EditionElement

from kuser.admin import my_admin_site
from django.http import HttpResponse

from kuser.constants import EDUCATION_TYPE
from kuser.models import Reader

logger = logging.getLogger('main')


@admin.register(CreateInventoryBook)
class CreateInventoryBookAdmin(admin.ModelAdmin):
    list_display = ['template_type', 'first_inventory_number', 'last_inventory_number', 'all_edition',
                    'display_excluded_editions', 'display_current_editions', 'date_of_create']
    readonly_fields = ['report_preview']
    form = CreateInventoryBookForm

    change_form_template = 'kreport/delete_button_create_inventory_book.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['template_type', 'library', 'first_inventory_number', 'last_inventory_number', 'all_edition',
                    'display_excluded_editions', 'display_current_editions', 'date_of_create']
        return ['template_type', 'library', 'first_inventory_number', 'last_inventory_number', 'all_edition',
                'display_excluded_editions', 'display_current_editions', 'date_of_create', 'report_preview']

    def report_preview(self, obj):
        rows = ""

        first_inventory_number = BaseFundElement.objects.filter(
            pk=obj.first_inventory_number
        ).first()

        last_inventory_number = BaseFundElement.objects.filter(
            pk=obj.last_inventory_number
        ).first()

        if not first_inventory_number or not last_inventory_number:
            return mark_safe("<p>Не указаны начальный или конечный инвентарные номера для этой библиотеки.</p>")

        try:
            first_prefix, first_suffix = map(int, first_inventory_number.inventory_number.split('/'))
            last_prefix, last_suffix = map(int, last_inventory_number.inventory_number.split('/'))
        except ValueError:
            return mark_safe("<p>Некорректный формат инвентарных номеров.</p>")

        if first_prefix != last_prefix:
            return mark_safe("<p>Префиксы начального и конечного номеров не совпадают.</p>")

        publication_status = None
        if obj.display_excluded_editions:
            publication_status = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
        elif obj.display_current_editions:
            publication_status = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF

        fund_elements = BaseFundElement.objects.filter(
            inventory_number__startswith=f"{first_prefix}/",
            library=obj.library
        )

        if publication_status is not None:
            fund_elements = fund_elements.filter(publication_status=publication_status)

        if obj.template_type:
            fund_elements = fund_elements.filter(edition__edition_subtype=obj.template_type)

        fund_elements_in_range = [
            el for el in fund_elements
            if first_suffix <= int(el.inventory_number.split('/')[1]) <= last_suffix
        ]

        for el in fund_elements_in_range:
            edition = el.get_edition()
            row = f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ccc;">{edition.created_at.strftime('%Y-%m-%d')}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{el.inventory_number}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{edition.year}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{edition.title}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{edition.author}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{el.get_publication_status_display()}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{el.invoice_number or 'N/A'}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{el.invoice_date.strftime('%Y-%m-%d') if el.invoice_date else 'N/A'}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{el.price}</td>
                    </tr>
                """
            rows += row

        if not rows:
            return mark_safe("<p>Не найдено записей для отображения.</p>")

        table_html = f"""
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="padding: 8px; border: 1px solid #ccc;">Дата регистрации</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Инвентарные номера</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Год публикации</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Название</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Автор</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Статус</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Номер накладной</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Дата накладной</th>
                            <th style="padding: 8px; border: 1px solid #ccc;">Цена без НДС</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            """
        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/inventory_book/', inventory_book_report,
                 name='inventorybook_report'),
        ]
        return custom_urls + urls

    # def response_add(self, request, obj, post_url_continue=None):
    #     return HttpResponseRedirect(reverse('admin:kreport_inventorybook_changelist'))
    #
    # def response_change(self, request, obj):
    #     return HttpResponseRedirect(reverse('admin:kreport_inventorybook_changelist'))


my_admin_site.register(CreateInventoryBook, CreateInventoryBookAdmin)


class CreateWorkplaceReportAdmin(admin.ModelAdmin):
    list_display = ['organization', 'position', 'year', 'add_excluded']
    readonly_fields = ['id', 'report_preview_field']

    form = OrganisationForm

    change_form_template = 'kreport/workplace_report.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['organization', 'position', 'year', 'add_excluded']
        return ['organization', 'position', 'year', 'add_excluded', 'report_preview_field']

    def report_preview(self, obj, request):
        readers = Reader.objects.using('belrw-user-db').all()
        user = Reader.objects.using('belrw-user-db').get(user=request.user)

        if user.library is not None:
            readers = readers.filter(library=user.library)

        if obj.organization is not None:
            readers = readers.filter(organization__name=obj.organization)

        if obj.position is not None:
            readers = readers.filter(position__name=obj.position)

        if obj.year is not None:
            readers = readers.filter(registration_date__year=obj.year)

        if not obj.add_excluded:
            readers = readers.exclude(exclusion=True)

        table_rows = ""
        for reader in readers:
            table_rows += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.organization}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.department}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.registration_date.strftime("%d.%m.%Y")}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.work_type}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.notes or ''}</td>
                </tr>
                """

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Организация</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Отдел</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Пользователь</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Дата регистрации</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Статус</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Примечание</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request  # Set request so it can be used in report_preview_field
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/workplace_report/', self.admin_site.admin_view(generate_workplace_report),
                 name='workplace_report'),
        ]
        return custom_urls + urls

    def workplace_report(self):
        return redirect(reverse('admin:create_workplace_report'))


my_admin_site.register(CreateWorkplaceReport, CreateWorkplaceReportAdmin)


class CreateWorkplaceReportFirstClassAdmin(admin.ModelAdmin):
    list_display = ['organization', 'library', 'position', 'year', 'add_excluded']
    readonly_fields = ['id', 'report_preview']

    form = OrganisationForm

    change_form_template = 'kreport/workplace_report_admin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['organization', 'position', 'library', 'year', 'add_excluded']
        return ['organization', 'position', 'library', 'year', 'add_excluded', 'report_preview']

    def report_preview(self, obj):
        readers = Reader.objects.using('belrw-user-db').all()

        if obj.library is not None:
            readers = readers.filter(library=obj.library)

        if obj.organization is not None:
            readers = readers.filter(organization__name=obj.organization)

        if obj.position is not None:
            readers = readers.filter(position__name=obj.position)

        if obj.year is not None:
            readers = readers.filter(registration_date__year=obj.year)

        if not obj.add_excluded:
            readers = readers.exclude(exclusion=True)

        table_rows = ""
        for reader in readers:
            table_rows += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.organization}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.department}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.registration_date.strftime("%d.%m.%Y")}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.work_type}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.notes or ''}</td>
                </tr>
                """

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Организация</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Отдел</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Пользователь</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Дата регистрации</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Статус</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Примечание</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/workplace_report_admin/',
                 self.admin_site.admin_view(generate_workplace_report_first_class),
                 name='workplace_report_admin'),
        ]
        return custom_urls + urls

    def workplace_report(self):
        return redirect(reverse('admin:create_workplace_report'))


my_admin_site.register(WorkplaceReportFirstClass, CreateWorkplaceReportFirstClassAdmin)


# Книга недополученных изданий
class BookIncompleteEditionAdmin(admin.ModelAdmin):
    list_display = ['year', 'moth']
    readonly_fields = ['id', 'report_preview']

    change_form_template = 'kreport/book_incomplete_edition.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['year', 'moth']
        return ['year', 'moth', 'report_preview']

    def report_preview(self, obj):
        start_date = datetime(obj.year, obj.moth, 1)
        end_date = (start_date + timedelta(days=31)).replace(day=1)

        editions = BaseEdition.objects.all()
        rows = ""

        for edition in editions:
            number_of_copies = BaseOrder.objects.filter(
                edition_id=edition.id
            ).aggregate(total_copies=Sum('number_of_copies'))['total_copies'] or 0

            received_copies = BaseFundElement.objects.filter(
                edition=edition,
                registration_date__gte=start_date,
                registration_date__lt=end_date
            ).count()

            missing_copies = max(0, number_of_copies - received_copies)

            if missing_copies == 0:
                continue
            elif received_copies == 0:
                continue

            base_order = BaseOrder.objects.filter(edition=edition).first()

            if base_order is None:
                company = "-"
                contract_number = "-"
            else:
                company = base_order.company if base_order.company else "-"
                contract_number = base_order.contract_number if base_order.contract_number else "-"

            row = f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{dict(Edition.SUBTYPES).get(edition.edition_subtype, "N/A")}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{edition.title}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{missing_copies}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{company}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{contract_number}</td>
                </tr>
            """
            rows += row

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                   <thead>
                       <tr style="background-color: #f2f2f2;">
                           <th style="padding: 8px; border: 1px solid #ccc;">Тип издания</th>
                           <th style="padding: 8px; border: 1px solid #ccc;">Наименование</th>
                           <th style="padding: 8px; border: 1px solid #ccc;">Недостающие экземпляры</th>
                           <th style="padding: 8px; border: 1px solid #ccc;">Организация</th>
                           <th style="padding: 8px; border: 1px solid #ccc;">Договор</th>
                       </tr>
                   </thead>
                   <tbody>
                       {rows} 
                   </tbody>
               </table>
        """
        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generate_report/',
                 self.admin_site.admin_view(generate_book_incomplete_edition_report),
                 name='book_incomplete_edition_report'),
        ]
        return custom_urls + urls


my_admin_site.register(BookIncompleteEdition, BookIncompleteEditionAdmin)


class CreateEducationReportAdmin(admin.ModelAdmin):
    list_display = ['education', 'year', 'add_excluded']
    readonly_fields = ['id', 'report_preview_field']

    change_form_template = 'kreport/education_report.html'

    def get_education_name(self, education):
        for key, value in EDUCATION_TYPE:
            if key == education:
                return value
        return None

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['education', 'year', 'add_excluded']
        return ['education', 'year', 'add_excluded', 'report_preview_field']

    def report_preview(self, obj, request):
        readers = Reader.objects.using('belrw-user-db').all()
        user = Reader.objects.using('belrw-user-db').get(user=request.user)
        edu = ''

        if user.library is not None:
            readers = readers.filter(library=user.library)

        if obj.education is not None:
            readers = readers.filter(education=obj.education)
            edu = self.get_education_name(obj.education)

        if obj.year is not None:
            readers = readers.filter(registration_date__year=obj.year)

        if not obj.add_excluded:
            readers = readers.exclude(exclusion=True)

        table_rows = ""
        for reader in readers:
            table_rows += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.organization}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{edu}</td>
                </tr>
                """

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Номер билета</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Организация</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Уровень образования</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request  # Set request so it can be used in report_preview_field
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/education_report/', self.admin_site.admin_view(generate_education_report),
                 name='education_report'),
        ]
        return custom_urls + urls

    def education_report(self):
        return redirect(reverse('admin:education_report'))


my_admin_site.register(CreateEducationReport, CreateEducationReportAdmin)


class CreateEducationReportFirstClassAdmin(admin.ModelAdmin):
    list_display = ['education', 'library', 'year', 'add_excluded']
    readonly_fields = ['id', 'report_preview']

    change_form_template = 'kreport/education_report_admin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['education', 'year', 'library', 'add_excluded']
        return ['education', 'year', 'library', 'add_excluded', 'report_preview']

    def get_education_name(self, education):
        for key, value in EDUCATION_TYPE:
            if key == education:
                return value
        return None

    def report_preview(self, obj):
        readers = Reader.objects.using('belrw-user-db').all()
        edu = ''

        if obj.library is not None:
            readers = readers.filter(library=obj.library)

        if obj.education is not None:
            readers = readers.filter(education=obj.education)
            edu = self.get_education_name(obj.education)

        if obj.year is not None:
            readers = readers.filter(registration_date__year=obj.year)

        if not obj.add_excluded:
            readers = readers.exclude(exclusion=True)

        table_rows = ""
        for reader in readers:
            table_rows += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.organization}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{edu}</td>
                </tr>
                """

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Номер билета</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Организация</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Уровень образования</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/education_report_admin/',
                 self.admin_site.admin_view(generate_education_report_first_class),
                 name='education_report_admin'),
        ]
        return custom_urls + urls

    def education_report(self):
        return redirect(reverse('admin:education_report'))


my_admin_site.register(CreateEducationReportFirstClass, CreateEducationReportFirstClassAdmin)


class TotalBookAdmin(admin.ModelAdmin):
    list_display = ['book_type', 'library', 'month', 'year']
    readonly_fields = ['id', 'report_preview']
    change_form_template = 'kreport/delete_button_total_book.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['book_type', 'library', 'month', 'year']
        return ['book_type', 'library', 'month', 'year', 'report_preview']

    def report_preview(self, obj):
        year = int(obj.year)

        if obj.month == "ALL_YEAR":
            month = "ALL_YEAR"
        else:
            try:
                month = int(obj.month)
            except ValueError:
                raise ValueError("Некорректное значение месяца. Ожидалось число или 'весь год'.")

        library = obj.library
        book_type = obj.book_type

        # if obj.book_type == FIRST_BOOK_TYPE:
        #     publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
        # elif obj.book_type == SECOND_BOOK_TYPE:
        #     publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
        # else:
        #     publication_status_filter = None

        if obj.book_type == FIRST_BOOK_TYPE:
            document_data = [
                {"doc_name": "Всего документов", "doc_start": calculate_doc_start_total_document(year, month, library, book_type),
                 "doc_received": calculate_doc_received_total_document(year, month, library, book_type),
                 "doc_end": calculate_doc_end_document(year, month, library, book_type)},
                {"doc_name": "В.т.ч принятых на баланс",
                 "doc_start": calculate_doc_start_accepted_to_balance(year, month, library, book_type),
                 "doc_received": calculate_doc_received_accepted_to_balance(year, month, library, book_type),
                 "doc_end": calculate_doc_end_accepted_to_balance(year, month, library, book_type)},
                {"doc_name": "Книги", "doc_start": calculate_doc_start_books(year, month, library, book_type),
                 "doc_received": calculate_doc_received_books(year, month, library, book_type),
                 "doc_end": calculate_doc_end_books(year, month, library, book_type)},
                {"doc_name": "Электронные ресурсы", "doc_start": calculate_doc_start_electronic_resources(year, month, library, book_type),
                 "doc_received": calculate_doc_received_electronic_resources(year, month, library, book_type),
                 "doc_end": calculate_doc_end_electronic_resources(year, month, library, book_type)},
                {"doc_name": "Брошюры", "doc_start": calculate_doc_start_brochures(year, month, library, book_type),
                 "doc_received": calculate_doc_received_brochures(year, month, library, book_type),
                 "doc_end": calculate_doc_end_brochures(year, month, library, book_type)},
                {"doc_name": "НТД", "doc_start": calculate_doc_start_ntd(year, month, library, book_type),
                 "doc_received": calculate_doc_received_ntd(year, month, library, book_type),
                 "doc_end": calculate_doc_end_ntd(year, month, library, book_type)},
                {"doc_name": "Информационные листки", "doc_start": calculate_doc_start_information_sheets(year, month, library, book_type),
                 "doc_received": calculate_doc_received_information_sheets(year, month, library, book_type),
                 "doc_end": calculate_doc_end_information_sheets(year, month, library, book_type)},
                {"doc_name": "Журналы", "doc_start": calculate_doc_start_magazines(year, month, library, book_type),
                 "doc_received": calculate_doc_received_magazines(year, month, library, book_type),
                 "doc_end": calculate_doc_end_magazines(year, month, library, book_type)},
                {"doc_name": "Газеты", "doc_start": calculate_doc_start_newspapers(year, month, library, book_type),
                 "doc_received": calculate_doc_received_newspapers(year, month, library, book_type),
                 "doc_end": calculate_doc_end_newspapers(year, month, library, book_type)},
            ]

        elif obj.book_type == SECOND_BOOK_TYPE:
            document_data = [
                {"doc_name": "Всего документов", "doc_start": calculate_doc_start_total_document(year, month, library, book_type),
                 "doc_received": calculate_doc_received_total_document(year, month, library, book_type),
                 "doc_end": calculate_doc_end_document(year, month, library, book_type)},
                {"doc_name": "В.т.ч принятых на баланс",
                 "doc_start": calculate_doc_start_accepted_to_balance(year, month, library, book_type),
                 "doc_received": calculate_doc_received_accepted_to_balance(year, month, library, book_type),
                 "doc_end": calculate_doc_end_accepted_to_balance(year, month, library, book_type)},
                {"doc_name": "Книги", "doc_start": calculate_doc_start_books(year, month, library, book_type),
                 "doc_received": calculate_doc_received_books(year, month, library, book_type),
                 "doc_end": calculate_doc_end_books(year, month, library, book_type)},
                {"doc_name": "Электронные ресурсы", "doc_start": calculate_doc_start_electronic_resources(year, month, library, book_type),
                 "doc_received": calculate_doc_received_electronic_resources(year, month, library, book_type),
                 "doc_end": calculate_doc_end_electronic_resources(year, month, library, book_type)},
                {"doc_name": "Брошюры", "doc_start": calculate_doc_start_brochures(year, month, library, book_type),
                 "doc_received": calculate_doc_received_brochures(year, month, library, book_type),
                 "doc_end": calculate_doc_end_brochures(year, month, library, book_type)},
                {"doc_name": "НТД", "doc_start": calculate_doc_start_ntd(year, month, library, book_type),
                 "doc_received": calculate_doc_received_ntd(year, month, library, book_type),
                 "doc_end": calculate_doc_end_ntd(year, month, library, book_type)},
                {"doc_name": "Информационные листки", "doc_start": calculate_doc_start_information_sheets(year, month, library, book_type),
                 "doc_received": calculate_doc_received_information_sheets(year, month, library, book_type),
                 "doc_end": calculate_doc_end_information_sheets(year, month, library, book_type)},
                {"doc_name": "Журналы", "doc_start": calculate_doc_start_magazines(year, month, library, book_type),
                 "doc_received": calculate_doc_received_magazines(year, month, library, book_type),
                 "doc_end": calculate_doc_end_magazines(year, month, library, book_type)},
                {"doc_name": "Газеты", "doc_start": calculate_doc_start_newspapers(year, month, library, book_type),
                 "doc_received": calculate_doc_received_newspapers(year, month, library, book_type),
                 "doc_end": calculate_doc_end_newspapers(year, month, library, book_type)},
            ]

        elif obj.book_type == THEAD_BOOK_TYPE:
            document_data = [
                {"doc_name": "Всего документов", "doc_start": calculate_doc_start_total_document(year, month, library, book_type),
                 "doc_received": calculate_doc_received_total_document(year, month, library, book_type),
                 "doc_end": calculate_doc_end_document(year, month, library, book_type)},
                {"doc_name": "В.т.ч принятых на баланс",
                 "doc_start": calculate_doc_start_accepted_to_balance(year, month, library, book_type),
                 "doc_received": calculate_doc_received_accepted_to_balance(year, month, library, book_type),
                 "doc_end": calculate_doc_end_accepted_to_balance(year, month, library, book_type)},
                {"doc_name": "Книги", "doc_start": calculate_doc_start_books(year, month, library, book_type),
                 "doc_received": calculate_doc_received_books(year, month, library, book_type),
                 "doc_end": calculate_doc_end_books(year, month, library, book_type)},
                {"doc_name": "Электронные ресурсы", "doc_start": calculate_doc_start_electronic_resources(year, month, library, book_type),
                 "doc_received": calculate_doc_received_electronic_resources(year, month, library, book_type),
                 "doc_end": calculate_doc_end_electronic_resources(year, month, library, book_type)},
                {"doc_name": "Брошюры", "doc_start": calculate_doc_start_brochures(year, month, library, book_type),
                 "doc_received": calculate_doc_received_brochures(year, month, library, book_type),
                 "doc_end": calculate_doc_end_brochures(year, month, library, book_type)},
                {"doc_name": "НТД", "doc_start": calculate_doc_start_ntd(year, month, library, book_type),
                 "doc_received": calculate_doc_received_ntd(year, month, library, book_type),
                 "doc_end": calculate_doc_end_ntd(year, month, library, book_type)},
                {"doc_name": "Информационные листки", "doc_start": calculate_doc_start_information_sheets(year, month, library, book_type),
                 "doc_received": calculate_doc_received_information_sheets(year, month, library, book_type),
                 "doc_end": calculate_doc_end_information_sheets(year, month, library, book_type)},
                {"doc_name": "Журналы", "doc_start": calculate_doc_start_magazines(year, month, library, book_type),
                 "doc_received": calculate_doc_received_magazines(year, month, library, book_type),
                 "doc_end": calculate_doc_end_magazines(year, month, library, book_type)},
                {"doc_name": "Газеты", "doc_start": calculate_doc_start_newspapers(year, month, library, book_type),
                 "doc_received": calculate_doc_received_newspapers(year, month, library, book_type),
                 "doc_end": calculate_doc_end_newspapers(year, month, library, book_type)},
            ]
        else:
            document_data = []

        rows = ""

        def get_month_date_range(year, month):
            if month == 'ALL_YEAR':
                first_day = date(year, 1, 1)
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                first_day = date(year, int(month), 1)
                if int(month) == 12:
                    last_day = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    last_day = date(year, int(month) + 1, 1) - timedelta(days=1)
            return first_day, last_day

        for doc in document_data:

            library = obj.library
            first_day, last_day = get_month_date_range(year, month)

            if doc["doc_name"] == "Всего документов":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "В.т.ч принятых на баланс":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "Книги":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    edition__edition_subtype=BaseEdition.SUBTYPE_BOOK,
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "Электронные ресурсы":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    edition__edition_subtype=BaseEdition.SUBTYPE_E_RESOURCE,
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "Брошюры":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    edition__edition_subtype=BaseEdition.SUBTYPE_BROCHURE,
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "НТД":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    edition__edition_subtype=BaseEdition.SUBTYPE_STD,
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "Информационные листки":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    edition__edition_subtype=BaseEdition.SUBTYPE_INFORMATION_FLYER,
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "Журналы":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    edition__edition_subtype=BaseEdition.SUBTYPE_MAGAZINE,
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            elif doc["doc_name"] == "Газеты":
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    edition__edition_subtype=BaseEdition.SUBTYPE_NEWSPAPER,
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )
            else:
                base_arrival_entries = BaseArrival.objects.select_related('edition', 'order_edition').filter(
                    library=library,
                    invoice_date__gte=first_day,
                    invoice_date__lte=last_day
                )

            if book_type == "ADMISSION_TO_THE_FUND":
                base_arrival_entries = base_arrival_entries.filter(
                    balance_type=BaseArrival.BALANCE_TYPE_1
                )
            elif book_type == "RETIREMENT_FROM_THE_FOUND":
                base_arrival_entries = base_arrival_entries.filter(
                    balance_type=BaseArrival.BALANCE_TYPE_2
                )
            elif book_type == "RESULTS_OF_THE_FOUND_MOVEMENT":
                base_arrival_entries = base_arrival_entries.filter(
                    balance_type__in=[BaseArrival.BALANCE_TYPE_1, BaseArrival.BALANCE_TYPE_2]
                )

            document_reg_data = [
                {
                    "doc_reg_name": entry.edition.title if entry.edition else None,
                    "doc_reg_instances": entry.qty
                }
                for entry in base_arrival_entries
            ]

            doc_reg_data_str = json.dumps(document_reg_data)

            row = f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{doc['doc_name']}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{doc['doc_start']}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{doc['doc_received']}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{doc['doc_end']}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">
                        <button type="button" class="btn btn-primary" 
                                data-doc-name="{doc['doc_name']}" 
                                data-doc-data='{doc_reg_data_str}' 
                                onclick="openModal(this)">
                            Расшифровка
                        </button>
                    </td>
                </tr>
            """
            rows += row

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Тип документа</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">На начало периода</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Поступило</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">На конец периода</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Расшифровка</th>
                    </tr>
                </thead>
                <tbody>
                    {rows} 
                </tbody>
            </table>
        """

        modal_html = render_to_string('kreport/decoding_button.html')
        return mark_safe(modal_html + table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generate_report/',
                 self.admin_site.admin_view(generate_total_book_report),
                 name='total_book_report'),
        ]
        return custom_urls + urls


my_admin_site.register(TotalBook, TotalBookAdmin)


class UserAccountingAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'year', 'month', 'day']
    readonly_fields = ['id', 'report_preview_field']
    form = UserAccountingForm

    change_form_template = 'kreport/user_accounting.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['report_type', 'year', 'month', 'day']
        return ['report_type', 'year', 'month', 'day', 'report_preview_field']

    def report_preview(self, obj, request):
        readers = Reader.objects.using('belrw-user-db').all()
        user = Reader.objects.using('belrw-user-db').get(user=request.user)

        if user.library is not None:
            readers = readers.filter(library=user.library)

        if obj.month is not None and obj.month != 0:
            readers = readers.filter(registration_date__month=obj.month)

        if obj.year is not None:
            readers = readers.filter(registration_date__year=obj.year)

        if obj.day is not None and obj.day != 0 and obj.month is not None and obj.month != 0:
            readers = readers.filter(registration_date__day=obj.day)


        if obj.report_type == 'Registered':
            table_rows = ""
            for reader in readers:
                table_rows += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.registration_date.strftime("%d.%m.%Y")}</td>
                            </tr>
                            """

            table_html = f"""
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                            <thead>
                                <tr style="background-color: #f2f2f2;">
                                    <th style="padding: 8px; border: 1px solid #ccc;">Номер билета</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Дата регистрации</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                        """
        else:
            table_rows = ""
            for reader in readers:
                if reader.reregistration_dates:
                    for rereg_date in reader.reregistration_dates.split():
                        rereg_date_obj = datetime.strptime(rereg_date, "%Y-%m-%d").date()

                        if (obj.year is None or rereg_date_obj.year == obj.year) and \
                                (obj.month == 0 or rereg_date_obj.month == obj.month):
                            table_rows += f"""
                                    <tr>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{rereg_date_obj.strftime("%d.%m.%Y")}</td>
                                    </tr>
                                """

            table_html = f"""
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                <th style="padding: 8px; border: 1px solid #ccc;">Номер билета</th>
                                <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                                <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                                <th style="padding: 8px; border: 1px solid #ccc;">Дата перерегистрации</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                    """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/user_accounting/', self.admin_site.admin_view(generate_user_accounting),
                 name='user_accounting'),
        ]
        return custom_urls + urls


my_admin_site.register(UserAccounting, UserAccountingAdmin)


class UserAccountingFirstClassAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'library', 'year', 'month', 'day']
    readonly_fields = ['id', 'report_preview_field']
    form = UserAccountingForm

    change_form_template = 'kreport/user_accounting_admin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['report_type', 'library', 'year', 'month', 'day']
        return ['report_type', 'library', 'year', 'month', 'day', 'report_preview_field']

    def report_preview(self, obj, request):
        readers = Reader.objects.using('belrw-user-db').all()

        if obj.library is not None:
            readers = readers.filter(library=obj.library)

        if obj.month is not None and obj.month != 0:
            readers = readers.filter(registration_date__month=obj.month)

        if obj.year is not None:
            readers = readers.filter(registration_date__year=obj.year)

        if obj.day is not None and obj.day != 0 and obj.month is not None and obj.month != 0:
            readers = readers.filter(registration_date__day=obj.day)


        if obj.report_type == 'Registered':
            table_rows = ""
            for reader in readers:
                table_rows += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.registration_date.strftime("%d.%m.%Y")}</td>
                            </tr>
                            """

            table_html = f"""
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                            <thead>
                                <tr style="background-color: #f2f2f2;">
                                    <th style="padding: 8px; border: 1px solid #ccc;">Номер билета</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Дата регистрации</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                        """
        else:
            table_rows = ""
            for reader in readers:
                if reader.reregistration_dates:
                    for rereg_date in reader.reregistration_dates.split():
                        rereg_date_obj = datetime.strptime(rereg_date, "%Y-%m-%d").date()

                        if (obj.year is None or rereg_date_obj.year == obj.year) and \
                                (obj.month == 0 or rereg_date_obj.month == obj.month):
                            table_rows += f"""
                                    <tr>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{reader.user}</td>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{reader.middle_name} {reader.user.first_name} {reader.user.last_name}</td>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{reader.position}</td>
                                        <td style="padding: 8px; border: 1px solid #ccc;">{rereg_date_obj.strftime("%d.%m.%Y")}</td>
                                    </tr>
                                """

            table_html = f"""
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                <th style="padding: 8px; border: 1px solid #ccc;">Номер билета</th>
                                <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                                <th style="padding: 8px; border: 1px solid #ccc;">Должность</th>
                                <th style="padding: 8px; border: 1px solid #ccc;">Дата перерегистрации</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                    """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/user_accounting_admin/',
                 self.admin_site.admin_view(generate_user_accounting_first_class),
                 name='user_accounting_admin'),
        ]
        return custom_urls + urls


my_admin_site.register(UserAccountingFirstClass, UserAccountingFirstClassAdmin)


# Книга недополученных изданий (Непериодика)
class BookIncompleteEditionNonPeriodicalsAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'library']
    readonly_fields = ['id', 'report_preview']
    change_form_template = 'kreport/change_form_bookIncompleteeditionnonperiodicalsadmin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['year', 'month']
        return ['year', 'month', 'report_preview']

    def report_preview(self, obj):
        try:
            year = int(obj.year)
            if obj.month == ALL_YEAR:
                start_date = datetime(year, 1, 1)
                end_date = datetime(year + 1, 1, 1)
            else:
                month = int(obj.month)
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)

            editions = BaseEdition.objects.filter(edition_type=Edition.TYPE_NON_PERIODICAL)
            rows = ""

            for edition in editions:
                total_ordered_copies = BaseOrderEdition.objects.filter(edition=edition).aggregate(
                    total_quantity=Sum('quantity')
                )['total_quantity'] or 0

                received_copies = BaseArrival.objects.filter(
                    edition=edition,
                    invoice_date__gte=start_date,
                    invoice_date__lt=end_date
                ).aggregate(total_qty=Sum('qty'))['total_qty'] or 0

                missing_copies = max(0, total_ordered_copies - received_copies)

                if missing_copies == 0:
                    continue

                base_order = BaseOrder.objects.filter(edition=edition).first()

                if base_order is None:
                    company = "-"
                    contract_number = "-"
                else:
                    company = base_order.company if base_order.company else "-"
                    contract_number = base_order.contract_number if base_order.contract_number else "-"

                row = f"""
                       <tr>
                           <td style="padding: 8px; border: 1px solid #ccc;">{dict(Edition.SUBTYPES).get(edition.edition_subtype, "N/A")}</td>
                           <td style="padding: 8px; border: 1px solid #ccc;">{edition.title}</td>
                           <td style="padding: 8px; border: 1px solid #ccc;">{missing_copies}</td>
                           <td style="padding: 8px; border: 1px solid #ccc;">{company}</td>
                           <td style="padding: 8px; border: 1px solid #ccc;">{contract_number}</td>
                       </tr>
                   """
                rows += row

            table_html = f"""
                   <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                       <thead>
                           <tr style="background-color: #f2f2f2;">
                               <th style="padding: 8px; border: 1px solid #ccc;">Тип издания</th>
                               <th style="padding: 8px; border: 1px solid #ccc;">Наименование</th>
                               <th style="padding: 8px; border: 1px solid #ccc;">Недостающие экземпляры</th>
                               <th style="padding: 8px; border: 1px solid #ccc;">Организация</th>
                               <th style="padding: 8px; border: 1px solid #ccc;">Договор</th>
                           </tr>
                       </thead>
                       <tbody>
                           {rows} 
                       </tbody>
                   </table>
               """
            return mark_safe(table_html)
        except ValueError as e:
            return mark_safe(f"<p style='color: red;'>Ошибка в обработке данных: {e}</p>")

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generate_report_new/', generate_book_incomplete_edition_report_non_per,
                 name='incomplete_edition_report'),
        ]
        return custom_urls + urls


my_admin_site.register(BookIncompleteEditionNonPeriodicals, BookIncompleteEditionNonPeriodicalsAdmin)


# Бухгалтерской ведомость
class AccountiongStatementAdmin(admin.ModelAdmin):
    list_display = ['year', 'library']
    readonly_fields = ['id', 'report_preview']
    change_form_template = 'kreport/change_form_accountiongstatementadmin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['year', 'month']
        return ['year', 'month', 'report_preview']

    def report_preview(self, obj):
        year = int(obj.year)
        month = int(obj.month)

        arrivals = BaseArrival.objects.filter(
            invoice_date__year=year,
            invoice_date__month=month
        ).order_by('order_edition__order__company')

        grouped_data = {}
        for arrival in arrivals:
            company = (
                arrival.order_edition.order.company
                if arrival.order_edition and arrival.order_edition.order
                else "Без компании"
            )
            if company not in grouped_data:
                grouped_data[company] = []
            grouped_data[company].append(arrival)

        rows = ""

        for company, company_arrivals in grouped_data.items():
            company_total_amount_with_vat = 0
            company_total_balance_qty = 0
            company_total_balance_amount = 0
            company_total_balance_vat = 0
            company_total_no_balance_qty = 0
            company_total_no_balance_amount = 0
            company_total_no_balance_vat = 0

            rows += f"""
                <tr style="background-color: #e9e9e9; font-weight: bold;">
                    <td colspan="8" style="padding: 8px; border: 1px solid #ccc;">{company}</td>
                </tr>
            """

            for arrival in company_arrivals:
                balance_qty = arrival.qty if arrival.balance_type == BaseArrival.BALANCE_TYPE_1.lower() else ""
                balance_amount = arrival.amount if arrival.balance_type == BaseArrival.BALANCE_TYPE_1.lower() else ""
                balance_vat = arrival.amount_vat if arrival.balance_type == BaseArrival.BALANCE_TYPE_1.lower() else ""

                no_balance_qty = arrival.qty if arrival.balance_type == BaseArrival.BALANCE_TYPE_2.lower() else ""
                no_balance_amount = arrival.amount if arrival.balance_type == BaseArrival.BALANCE_TYPE_2.lower() else ""
                no_balance_vat = arrival.amount_vat if arrival.balance_type == BaseArrival.BALANCE_TYPE_2.lower() else ""

                rows += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ccc;">{company}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{arrival.filing or ""}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{arrival.invoice_number or ""}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{arrival.invoice_date or ""}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{arrival.amount_with_vat or 0}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{balance_qty} / {balance_amount} / {balance_vat}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{no_balance_qty} / {no_balance_amount} / {no_balance_vat}</td>
                    </tr>
                """

                company_total_amount_with_vat += arrival.amount_with_vat or 0

                if arrival.balance_type == BaseArrival.BALANCE_TYPE_1.lower():
                    company_total_balance_qty += arrival.qty
                    company_total_balance_amount += arrival.amount
                    company_total_balance_vat += arrival.amount_vat

                if arrival.balance_type == BaseArrival.BALANCE_TYPE_2.lower():
                    company_total_no_balance_qty += arrival.qty
                    company_total_no_balance_amount += arrival.amount
                    company_total_no_balance_vat += arrival.amount_vat

            rows += f"""
                <tr style="font-weight: bold;">
                    <td style="padding: 8px; border: 1px solid #ccc;" colspan="4">Итого по {company}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{company_total_amount_with_vat}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">
                        {company_total_balance_qty} / {company_total_balance_amount} / {company_total_balance_vat}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ccc;">-</td>
                </tr>
            """

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Компания</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Тип сопр. документа</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Номер документа</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Дата документа</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Сумма с НДС</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">На балансе (Кол-во/Сумма/НДС)</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Не на балансе (Кол-во/Сумма/НДС)</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/accountiong_statement_report/', accountiong_statement_report,
                 name='accountiong_statement_report'),
        ]
        return custom_urls + urls


my_admin_site.register(AccountiongStatement, AccountiongStatementAdmin)


# Акт приёмки периодики
class CertificateAcceptancePeriodicalsAdmin(admin.ModelAdmin):
    list_display = ['year', 'library']
    readonly_fields = ['id', 'report_preview']
    change_form_template = 'kreport/change_form_certificateacceptanceperiodicalsadmin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['year']
        return ['year', 'report_preview']

    def report_preview(self, obj):
        year = int(obj.year)
        editions = BaseArrival.objects.filter(invoice_date__year=year)

        grouped_data = {}
        for edition in editions:
            name = edition.edition.title if edition.edition else "N/A"
            if name not in grouped_data:
                grouped_data[name] = {
                    "years": set(),
                    "numbers": {},
                    "double_numbers": [],
                    "total_qty": 0
                }
            grouped_data[name]["years"].add(edition.invoice_date.year if edition.invoice_date else "N/A")
            invoice_number = edition.invoice_number if edition.invoice_number else "N/A"
            grouped_data[name]["numbers"].setdefault(invoice_number, 0)
            grouped_data[name]["numbers"][invoice_number] += edition.qty or 0
            grouped_data[name]["double_numbers"].append(
                "Да" if edition.double_number and edition.double_number.is_double else "Нет")
            grouped_data[name]["total_qty"] += edition.qty or 0

        rows = ""
        grand_total = 0

        for name, data in grouped_data.items():
            total_copies = data["total_qty"]
            grand_total += total_copies

            years = ', '.join(map(str, data["years"]))
            invoice_details = ', '.join([num for num in data["numbers"].keys()])
            double_numbers = ', '.join(data["double_numbers"])
            quantities = ', '.join([str(qty) for qty in data["numbers"].values()])

            row = f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{name}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{years}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{invoice_details}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{double_numbers}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{quantities}</td>
                </tr>
            """
            rows += row

            rows += f"""
                <tr style="font-weight: bold; background-color: #f9f9f9;">
                    <td colspan="4" style="padding: 8px; border: 1px solid #ccc;">Итого для «{name}»</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{total_copies}</td>
                </tr>
            """

        rows += f"""
            <tr style="font-weight: bold; background-color: #e0e0e0;">
                <td colspan="4" style="padding: 8px; border: 1px solid #ccc;">Общий итог</td>
                <td style="padding: 8px; border: 1px solid #ccc;">{grand_total}</td>
            </tr>
        """

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Наименование</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Год</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Номер (Количество)</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Сдвоенный</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Итого экземпляров</th>
                    </tr>
                </thead>
                <tbody>
                    {rows} 
                </tbody>
            </table>
        """
        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/certificate_report/',
                 self.admin_site.admin_view(certificate_acceptance_periodicals_report),
                 name='certificate_acceptance_periodicals_report'),
        ]
        return custom_urls + urls


my_admin_site.register(CertificateAcceptancePeriodicals, CertificateAcceptancePeriodicalsAdmin)


# Отчёт приёмки периодики
class PeriodicalsAcceptanceReportAdmin(admin.ModelAdmin):
    list_display = ['month', 'year', 'library']
    readonly_fields = ['id', 'report_preview']
    change_form_template = 'kreport/change_form_periodicalsacceptancereportadmin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['year', 'month']
        return ['year', 'month', 'report_preview']

    def report_preview(self, obj):
        year = int(obj.year)
        month = int(obj.month)
        arrivals = BaseArrival.objects.filter(
            invoice_date__year=year,
            invoice_date__month=month
        ).select_related('edition', 'order_edition__order__company')
        grouped_data = {}

        for arrival in arrivals:
            company = arrival.order_edition.order.company
            edition_name = arrival.edition.title if arrival.edition else "—"
            qty = arrival.qty
            amount_no_vat = arrival.amount
            vat_amount = arrival.amount_vat
            contract_number = arrival.order_edition.order.contract_number or "—"
            contract_date = arrival.order_edition.order.contract_date.strftime(
                '%d.%m.%Y') if arrival.order_edition.order.contract_date else "—"

            if company not in grouped_data:
                grouped_data[company] = {}

            if edition_name not in grouped_data[company]:
                grouped_data[company][edition_name] = {
                    "arrivals": [],
                    "total_qty": 0,
                    "total_amount_no_vat": 0,
                    "total_vat": 0
                }

            grouped_data[company][edition_name]["arrivals"].append({
                "qty": qty,
                "amount_no_vat": amount_no_vat,
                "vat_amount": vat_amount,
                "contract_number": contract_number,
                "contract_date": contract_date
            })
            grouped_data[company][edition_name]["total_qty"] += qty
            grouped_data[company][edition_name]["total_amount_no_vat"] += amount_no_vat
            grouped_data[company][edition_name]["total_vat"] += vat_amount

        rows = ""
        grand_total_qty = 0
        grand_total_amount_no_vat = 0
        grand_total_vat = 0

        for company, editions in grouped_data.items():
            total_qty_company = 0
            total_amount_no_vat_company = 0
            total_vat_company = 0

            for edition_name, data in editions.items():
                arrivals = data["arrivals"]
                total_qty = data["total_qty"]
                total_amount_no_vat = data["total_amount_no_vat"]
                total_vat = data["total_vat"]

                invoice_details = ', '.join(
                    [f"{arrival['contract_number']} ({arrival['qty']})" for arrival in arrivals])
                rows += f"""
                    <tr>
                        <td rowspan="{len(arrivals)}" style="padding: 8px; border: 1px solid #ccc;">{company}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{edition_name}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{invoice_details}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{total_amount_no_vat:.2f}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{total_vat:.2f}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{arrivals[0]['contract_number']}</td>
                        <td style="padding: 8px; border: 1px solid #ccc;">{arrivals[0]['contract_date']}</td>
                    </tr>
                """

                # Обновление итогов для организации
                total_qty_company += total_qty
                total_amount_no_vat_company += total_amount_no_vat
                total_vat_company += total_vat

                # Подсчет итогов для общего количества
                grand_total_qty += total_qty
                grand_total_amount_no_vat += total_amount_no_vat
                grand_total_vat += total_vat

            # Итог по организации
            rows += f"""
                <tr style="font-weight: bold; background-color: #f9f9f9;">
                    <td colspan="2" style="padding: 8px; border: 1px solid #ccc;">Итого для «{company}»</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{total_qty_company}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{total_amount_no_vat_company:.2f}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{total_vat_company:.2f}</td>
                    <td colspan="2" style="padding: 8px; border: 1px solid #ccc;"></td>
                </tr>
            """

        # Итог по всем организациям
        rows += f"""
            <tr style="font-weight: bold; background-color: #e0e0e0;">
                <td colspan="2" style="padding: 8px; border: 1px solid #ccc;">Общий итог</td>
                <td style="padding: 8px; border: 1px solid #ccc;">{grand_total_qty}</td>
                <td style="padding: 8px; border: 1px solid #ccc;">{grand_total_amount_no_vat:.2f}</td>
                <td style="padding: 8px; border: 1px solid #ccc;">{grand_total_vat:.2f}</td>
                <td colspan="2" style="padding: 8px; border: 1px solid #ccc;"></td>
            </tr>
        """

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Организация</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Наименование периодического издания</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">№ (Количество)</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Цена</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">НДС</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Номер договора</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Дата договора</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        """
        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/periodicals_acceptance_report/',
                 self.admin_site.admin_view(periodicals_acceptance_report),
                 name='periodicals_acceptance_report'),
        ]
        return custom_urls + urls


my_admin_site.register(PeriodicalsAcceptanceReport, PeriodicalsAcceptanceReportAdmin)


class CreateDebtorsReportAdmin(admin.ModelAdmin):
    list_display = ['report_type']
    readonly_fields = ['id', 'report_preview_field']
    form = DebtorsForm

    change_form_template = 'kreport/debtors_report.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['report_type', 'reader_id', 'date']
        return ['report_type', 'reader_id', 'date', 'report_preview_field']

    def report_preview(self, obj, request):
        table_html = ''
        debtors = Debtors.objects.using('belrw-service-db').all()
        user = Reader.objects.using('belrw-user-db').get(user=request.user)

        if user.library is not None:
            debtors = debtors.filter(library=user.library)

        if obj.date is not None:
            debtors = debtors.filter(refund_date__lt=obj.date)

        if obj.report_type == 'Date':
            table_rows = ""
            for debtor in debtors:
                reader = Reader.objects.using('belrw-user-db').get(pk=debtor.reader_id)
                table_rows += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ccc;">{reader.user.last_name} {reader.user.first_name} {reader.middle_name}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{debtor.inv_number}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{debtor.service_type}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{debtor.refund_date.strftime("%d.%m.%Y")}</td>
                                 <td style="padding: 8px; border: 1px solid #ccc;">{debtor.delay_days}</td>
                            </tr>
                            """

                table_html = f"""
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                            <thead>
                                <tr style="background-color: #f2f2f2;">
                                    <th style="padding: 8px; border: 1px solid #ccc;">ФИО должника</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Вид обслуживания</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Дней просрочено</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                        """
        else:
            debtors = debtors.filter(reader_id=obj.reader_id)
            table_rows = ""
            for debtor in debtors:
                logger.debug(f'{debtor.service_type}')
                circ = BookCirculation.objects.using('belrw-service-db').filter(pk=debtor.circulation_id).first()
                logger.debug(f'{circ}')
                table_rows += f"""
                                                    <tr>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.inv_number}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.service_type}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{circ.status}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.refund_date.strftime("%d.%m.%Y")}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.delay_days}</td>
                                                    </tr>
                                                """

                table_html = f"""
                                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                                        <thead>
                                            <tr style="background-color: #f2f2f2;">
                                                <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Вид обслуживания</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Статус</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Дней просрочено</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {table_rows}
                                        </tbody>
                                    </table>
                                    """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/debtors_report/', self.admin_site.admin_view(debtors_report),
                 name='debtors_report'),
        ]
        return custom_urls + urls

    class Media:
        js = ('js/selection.js',)


my_admin_site.register(CreateDebtorsReport, CreateDebtorsReportAdmin)


class CreateDebtorsReportFirstClassAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'date', 'library']
    readonly_fields = ['id', 'report_preview_field']
    form = DebtorsForm

    change_form_template = 'kreport/debtors_report_admin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['report_type', 'date', 'reader_id', 'library']
        return ['report_type', 'date', 'reader_id', 'library', 'report_preview_field']

    def report_preview(self, obj, request):
        debtors = Debtors.objects.using('belrw-service-db').all()

        if obj.library is not None:
            debtors = debtors.filter(library=obj.library)

        if obj.date is not None:
            debtors = debtors.filter(refund_date__lt=obj.date)


        if obj.report_type == 'Date':
            table_rows = ""
            for debtor in debtors:
                reader = Reader.objects.using('belrw-user-db').get(pk=debtor.reader_id)
                table_rows += f"""
                            <tr>
                                 <td style="padding: 8px; border: 1px solid #ccc;">{reader.user.last_name} {reader.user.first_name} {reader.middle_name}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{debtor.inv_number}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{debtor.service_type}</td>
                                <td style="padding: 8px; border: 1px solid #ccc;">{debtor.refund_date.strftime("%d.%m.%Y")}</td>
                                 <td style="padding: 8px; border: 1px solid #ccc;">{debtor.delay_days}</td>
                            </tr>
                            """

            table_html = f"""
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                            <thead>
                                <tr style="background-color: #f2f2f2;">
                                    <th style="padding: 8px; border: 1px solid #ccc;">ФИО должника</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Вид обслуживания</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                    <th style="padding: 8px; border: 1px solid #ccc;">Дней просрочено</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                        """
        else:
            table_rows = ""
            for debtor in debtors:
                circ = BookCirculation.objects.using('belrw-service-db').filter(pk=debtor.circulation_id).first()
                table_rows += f"""
                                    <tr>
                                         <tr>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.inv_number}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.service_type}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{circ.status}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.refund_date.strftime("%d.%m.%Y")}</td>
                                                        <td style="padding: 8px; border: 1px solid #ccc;">{debtor.delay_days}</td>
                                                    </tr>
                                    </tr>
                                """

            table_html = f"""
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                    <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Вид обслуживания</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Статус</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                                <th style="padding: 8px; border: 1px solid #ccc;">Дней просрочено</th>
                                </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                    """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/debtors_report_admin/', self.admin_site.admin_view(debtors_report_first_class),
                 name='debtors_report_admin'),
        ]
        return custom_urls + urls

    class Media:
        js = ('js/selection_admin.js',)


my_admin_site.register(CreateDebtorsReportFirstClass, CreateDebtorsReportFirstClassAdmin)


class TypeOfServiceAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'library']
    readonly_fields = ['id', 'report_preview']
    change_form_template = 'kreport/change_form_typeofserviceadmin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['year', 'month', 'library']
        return ['year', 'month', 'library', 'report_preview']

    def report_preview(self, obj):
        year = int(obj.year)
        month = int(obj.month)

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        editions = BookCirculation.objects.filter(
            receive_date__range=(start_date, end_date)
        )

        service_type_count = {}

        for edition in editions:
            service_type = edition.service_type
            if service_type in service_type_count:
                service_type_count[service_type] += 1
            else:
                service_type_count[service_type] = 1

        rows = ""

        for service_type, count in service_type_count.items():
            row = f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{service_type}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{count}</td>
                </tr>
            """
            rows += row

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Тип обслуживания</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Количество</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/type_of_service_report_admin/', typeofservice_report,
                 name='type_of_service_report_admin'),
        ]
        return custom_urls + urls


my_admin_site.register(TypeOfService, TypeOfServiceAdmin)


class BookCirculationReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'year']
    readonly_fields = ['id', 'report_preview_field']
    change_form_template = 'kreport/circulation_report.html'

    form = CirculationForm

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['report_type', 'year', 'reader_id']
        return ['report_type', 'reader_id', 'year', 'report_preview_field']

    def report_preview(self, obj, request):
        table_html = ''
        circulations = BookCirculation.objects.using('belrw-service-db').all()
        user = Reader.objects.using('belrw-user-db').get(user=request.user)

        if user.library is not None:
            circulations = circulations.filter(library=user.library)

        if obj.year is not None:
            circulations = circulations.filter(refund_date__year__lte=obj.year)

        if obj.report_type == 'Date':
            table_rows = ""
            for circulation in circulations:
                edition_element = EditionElement.objects.using('belrw-service-db').filter(
                    book_circulation=circulation).first()
                fund = BaseFundElement.objects.using('belrw-lib-db').filter(pk=edition_element.fund_id).first()
                logger.debug(f'{fund.inventory_number.split("/")[0]}')
                edition_type = ''
                if fund.inventory_number.split('/')[0] == '1':
                    edition_type = 'Книги'
                if fund.inventory_number.split('/')[0] == '2':
                    edition_type = 'НТД и брошюры'
                if fund.inventory_number.split('/')[0] == '3':
                    edition_type = 'Журналы и другие периодические издания'
                if fund.inventory_number.split('/')[0] == '4':
                    edition_type = 'Газеты'
                if fund.inventory_number.split('/')[0] == '5':
                    edition_type = 'Информационные листки'
                if fund.inventory_number.split('/')[0] == '6':
                    edition_type = 'Изменения и дополнения к НТД'
                if fund.inventory_number.split('/')[0] == '8':
                    edition_type = 'Электронный ресурс'

                reader = Reader.objects.using('belrw-user-db').get(pk=circulation.reader_id)
                logger.debug(f'fund: {fund.inventory_number}')
                table_rows += f"""
                                <tr>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.user.last_name} {reader.user.first_name} {reader.middle_name}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{circulation.receive_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{circulation.refund_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_type}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_element.edition}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{fund.inventory_number}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.service_type}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.status}</td>
                                </tr>
                                """

                table_html = f"""
                            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                                <thead>
                                    <tr style="background-color: #f2f2f2;">
                                        <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Дата выдачи</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Вид издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Наименование издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Тип обслуживания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Статус выдачи</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_rows}
                                </tbody>
                            </table>
                            """
        else:
            table_rows = ""
            for circulation in circulations:
                edition_element = EditionElement.objects.using('belrw-service-db').filter(
                    book_circulation=circulation).first()
                fund = BaseFundElement.objects.using('belrw-lib-db').filter(pk=edition_element.fund_id).first()

                edition_type = ''
                if fund.inventory_number.split('/')[0] == '1':
                    edition_type = 'Книги'
                if fund.inventory_number.split('/')[0] == '2':
                    edition_type = 'НТД и брошюры'
                if fund.inventory_number.split('/')[0] == '3':
                    edition_type = 'Журналы и другие периодические издания'
                if fund.inventory_number.split('/')[0] == '4':
                    edition_type = 'Газеты'
                if fund.inventory_number.split('/')[0] == '5':
                    edition_type = 'Информационные листки'
                if fund.inventory_number.split('/')[0] == '6':
                    edition_type = 'Изменения и дополнения к НТД'
                if fund.inventory_number.split('/')[0] == '8':
                    edition_type = 'Электронный ресурс'

                table_rows += f"""
                                                        <tr>
                                                            <td style="padding: 8px; border: 1px solid #ccc;">{circulation.receive_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{circulation.refund_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_type}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_element.edition}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{fund.inventory_number}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.service_type}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.status}</td>
                                                        </tr>
                                                    """

                table_html = f"""
                                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                                            <thead>
                                                <tr style="background-color: #f2f2f2;">
                                                    <th style="padding: 8px; border: 1px solid #ccc;">Дата выдачи</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Вид издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Наименование издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Тип обслуживания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Статус выдачи</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {table_rows}
                                            </tbody>
                                        </table>
                                        """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/circulation_report/', self.admin_site.admin_view(circulation_report),
                 name='circulation_report'),
        ]
        return custom_urls + urls

    class Media:
        js = ('js/circulation.js',)


my_admin_site.register(BookCirculationReport, BookCirculationReportAdmin)


class BookCirculationReportFirstClassAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'year', 'library']
    readonly_fields = ['id', 'report_preview_field']
    change_form_template = 'kreport/circulation_report_admin.html'

    form = CirculationForm

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['report_type', 'library', 'year', 'reader_id']
        return ['report_type', 'reader_id', 'library', 'year', 'report_preview_field']

    def report_preview(self, obj, request):
        table_html = ''
        circulations = BookCirculation.objects.using('belrw-service-db').all()

        if obj.library is not None:
            circulations = circulations.filter(library=obj.library)


        if obj.year is not None:
            circulations = circulations.filter(refund_date__year__lte=obj.year)

        if obj.report_type == 'Date':
            table_rows = ""
            for circulation in circulations:
                edition_element = EditionElement.objects.using('belrw-service-db').filter(
                    book_circulation=circulation).first()
                reader = Reader.objects.using('belrw-user-db').get(pk=circulation.reader_id)
                fund = BaseFundElement.objects.using('belrw-lib-db').filter(pk=edition_element.fund_id).first()

                edition_type = ''
                if fund.inventory_number.split('/')[0] == '1':
                    edition_type = 'Книги'
                if fund.inventory_number.split('/')[0] == '2':
                    edition_type = 'НТД и брошюры'
                if fund.inventory_number.split('/')[0] == '3':
                    edition_type = 'Журналы и другие периодические издания'
                if fund.inventory_number.split('/')[0] == '4':
                    edition_type = 'Газеты'
                if fund.inventory_number.split('/')[0] == '5':
                    edition_type = 'Информационные листки'
                if fund.inventory_number.split('/')[0] == '6':
                    edition_type = 'Изменения и дополнения к НТД'
                if fund.inventory_number.split('/')[0] == '8':
                    edition_type = 'Электронный ресурс'

                table_rows += f"""
                                <tr>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{reader.user.last_name} {reader.user.first_name} {reader.middle_name}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{circulation.receive_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{circulation.refund_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_type}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_element.edition}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{fund.inventory_number}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.service_type}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.status}</td>
                                </tr>
                                """

                table_html = f"""
                            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                                <thead>
                                    <tr style="background-color: #f2f2f2;">
                                        <th style="padding: 8px; border: 1px solid #ccc;">ФИО</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Дата выдачи</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Вид издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Наименование издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Тип обслуживания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Статус выдачи</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_rows}
                                </tbody>
                            </table>
                            """
        else:
            table_rows = ""
            for circulation in circulations:
                edition_element = EditionElement.objects.using('belrw-service-db').filter(
                    book_circulation=circulation).first()

                fund = BaseFundElement.objects.using('belrw-lib-db').filter(pk=edition_element.fund_id).first()

                edition_type = ''
                if fund.inventory_number.split('/')[0] == '1':
                    edition_type = 'Книги'
                if fund.inventory_number.split('/')[0] == '2':
                    edition_type = 'НТД и брошюры'
                if fund.inventory_number.split('/')[0] == '3':
                    edition_type = 'Журналы и другие периодические издания'
                if fund.inventory_number.split('/')[0] == '4':
                    edition_type = 'Газеты'
                if fund.inventory_number.split('/')[0] == '5':
                    edition_type = 'Информационные листки'
                if fund.inventory_number.split('/')[0] == '6':
                    edition_type = 'Изменения и дополнения к НТД'
                if fund.inventory_number.split('/')[0] == '8':
                    edition_type = 'Электронный ресурс'

                table_rows += f"""
                                                        <tr>
                                                            <td style="padding: 8px; border: 1px solid #ccc;">{circulation.receive_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{circulation.refund_date}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_type}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{edition_element.edition}</td>
                                    <td style="padding: 8px; border: 1px solid #ccc;">{fund.inventory_number}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.service_type}</td>
                                     <td style="padding: 8px; border: 1px solid #ccc;">{circulation.status}</td>
                                                        </tr>
                                                    """

                table_html = f"""
                                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                                            <thead>
                                                <tr style="background-color: #f2f2f2;">
                                                    <th style="padding: 8px; border: 1px solid #ccc;">Дата выдачи</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Дата возврата</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Вид издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Наименование издания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Инвентарный номер</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Тип обслуживания</th>
                                        <th style="padding: 8px; border: 1px solid #ccc;">Статус выдачи</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {table_rows}
                                            </tbody>
                                        </table>
                                        """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def report_preview_field(self, obj):
        return self.report_preview(obj, self.request)

    report_preview_field.short_description = "Предварительный просмотр отчета"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.request = request
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/circulation_report_admin/', self.admin_site.admin_view(circulation_report_first_class),
                 name='circulation_report_admin'),
        ]
        return custom_urls + urls

    class Media:
        js = ('js/circulation_admin.js',)


my_admin_site.register(BookCirculationReportFirstClass, BookCirculationReportFirstClassAdmin)


# Отчёт по хранилищу
class StorageReportAdmin(admin.ModelAdmin):
    list_display = ['year', 'month']
    readonly_fields = ['id', 'report_preview']
    change_form_template = 'kreport/change_form_storagereportadmin.html'

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['year', 'month',]
        return ['year', 'month', 'report_preview']

    def report_preview(self, obj):
        year = int(obj.year)
        month = int(obj.month)

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        subtype_dict = dict(BaseEdition.SUBTYPES)

        edition_elements = EditionElement.objects.filter(
            book_circulation__receive_date__gte=start_date,
            book_circulation__receive_date__lt=end_date
        ).order_by('book_circulation__receive_date')

        subtype_count = {}

        for edition_element in edition_elements:
            base_edition = BaseEdition.objects.filter(title=edition_element.edition).first()

            if base_edition:
                edition_subtype = subtype_dict.get(base_edition.edition_subtype, 'Неизвестно')
            else:
                edition_subtype = 'Неизвестно'

            if edition_subtype in subtype_count:
                subtype_count[edition_subtype] += 1
            else:
                subtype_count[edition_subtype] = 1

        rows = ""
        for subtype, count in subtype_count.items():
            row = f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;">{subtype}</td>
                    <td style="padding: 8px; border: 1px solid #ccc;">{count}</td>
                </tr>
            """
            rows += row

        table_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ccc;">Вид</th>
                        <th style="padding: 8px; border: 1px solid #ccc;">Количество</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        """

        return mark_safe(table_html)

    report_preview.short_description = "Предварительный просмотр отчета"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/storage_report_admin/', storage_report_admin,
                 name='storage_report_admin'),
        ]
        return custom_urls + urls


my_admin_site.register(StorageReport, StorageReportAdmin)
