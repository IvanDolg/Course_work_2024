from datetime import timedelta, datetime

from django.contrib import admin, messages
from django.db import connection
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.apps import apps

import json
from django.http import JsonResponse

from kservice.models import BookCirculation
from kuser.constants import STATUS_READER_ONE, STATUS_READER_TWO, LIBRARY_TYPE, ROLE_STATUS_FIRST, ROLE_STATUS_SECOND, \
    ROLE_STATUS_THIRD, ROLE_STATUS_FOURTH
from kuser.forms import CustomUserCreationForm
from kuser.models import Reader, LibraryCard, Worker, Organization, Position, Department, MyUser, Decision, \
    ReaderFirstClass, Reregistration
from kuser.views import MyAdminSite
from main.models import *
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin
from fcm_django.models import FCMDevice

logger = logging.getLogger('main')

my_admin_site = MyAdminSite(name='myadmin')

my_admin_site.register(User, UserAdmin)
my_admin_site.register(Group, GroupAdmin)
my_admin_site.register(Token, TokenAdmin)
my_admin_site.register(FCMDevice)


class TicketNumberFilter(admin.SimpleListFilter):
    title = 'Номер билета'
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        users = Reader.objects.values_list('user__username', flat=True).distinct()
        return [(user, user) for user in users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__username=self.value())
        return queryset


class FullNameFilter(admin.SimpleListFilter):
    title = 'ФИО'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        readers = Reader.objects.select_related('user').values_list('user__id', 'user__first_name', 'user__last_name',
                                                                    'middle_name').distinct()
        return [
            (user_id, f"{last_name} {first_name} {middle_name or ''}".strip())
            for user_id, first_name, last_name, middle_name in readers
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__id=self.value())
        return queryset


class OrganizationFilter(admin.SimpleListFilter):
    title = 'Организация'
    parameter_name = 'organization'

    def lookups(self, request, model_admin):
        organizations = Reader.objects.select_related('organization').values_list('organization__id',
                                                                                  'organization__name').distinct()
        return [(org_id, org_name) for org_id, org_name in organizations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(organization__id=self.value())
        return queryset


class BirthDateFilter(admin.SimpleListFilter):
    title = _('Дата рождения')
    parameter_name = 'date_of_birth'

    def lookups(self, request, model_admin):
        birth_dates = Reader.objects.values_list('birth_date', flat=True).distinct()
        return [(date, date.strftime('%d-%m-%Y')) for date in birth_dates if date]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(birth_date=self.value())
        return queryset


class RegistrationDateFilter(admin.SimpleListFilter):
    title = _('Дата регистрации')
    parameter_name = 'registration_date'

    def lookups(self, request, model_admin):
        registration_dates = Reader.objects.values_list('registration_date', flat=True).distinct()
        return [(date, date.strftime('%d-%m-%Y')) for date in registration_dates if date]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(registration_date=self.value())
        return queryset


class ReregistrationDateFilter(admin.SimpleListFilter):
    title = _('Дата перерегистрации')
    parameter_name = 'reregistration_dates'

    def lookups(self, request, model_admin):
        dates = Reader.objects.values_list('reregistration_dates', flat=True).distinct()
        unique_dates = set()
        for date_list in dates:
            if date_list:
                unique_dates.update(date_list.split(' '))
        unique_dates = sorted(unique_dates)
        return [(date, date) for date in unique_dates if date]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(reregistration_dates__icontains=self.value())
        return queryset


class LibraryFilter(admin.SimpleListFilter):
    title = 'Библиотека'
    parameter_name = 'library'

    def lookups(self, request, model_admin):
        return LIBRARY_TYPE

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(library=self.value())
        return queryset


@admin.register(MyUser)
class MyUserAdmin(UserAdmin):
    form = CustomUserCreationForm
    search_fields = ('first_name', 'last_name')

    list_display = ('username', 'first_name', 'last_name')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('username',)
    list_filter = ('is_active',)

    def get_user_roles(self, myuser_id):
        query = """
            SELECT g.name
            FROM auth_group g
            JOIN kuser_myuser_groups ug ON g.id = ug.group_id
            WHERE ug.myuser_id = 
        """ + f'{myuser_id}'
        logger.debug(f'query: {query}')
        with connection.cursor() as cursor:
            cursor.execute(query)
            roles = [row[0] for row in cursor.fetchall()]
        logger.debug(f'{roles}')
        return roles

    def get_fieldsets(self, request, obj=None):
        logger.debug(self.get_user_roles(request.user.pk))
        if self.get_user_roles(request.user.pk).__contains__('Системный администратор'):
            return (
                (None, {'fields': ('username', 'email')}),
                ('Персональная информация', {'fields': ('first_name', 'last_name')}),
                ('Даты', {'fields': ('last_login', 'date_joined')}),
            )
        return (
            (None, {'fields': ('username', 'email')}),
            ('Персональная информация', {'fields': ('first_name', 'last_name')}),
            ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
            ('Даты', {'fields': ('date_joined', 'validity_period')}),
        )

    change_form_template = "admin/kuser/mail_change_form.html"

    def has_add_permission(self, request):
        return False

    add_form = CustomUserCreationForm

    # def save_model(self, request, obj, form, change):
    #     if not obj.first_name or not obj.last_name or not obj.email:
    #         raise forms.ValidationError("Поля 'first_name', 'last_name' и 'email' обязательны для заполнения.")
    #     super().save_model(request, obj, form, change)


my_admin_site.register(MyUser, MyUserAdmin)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


my_admin_site.register(Department, DepartmentAdmin)


@admin.register(LibraryCard)
class LibraryCardAdmin(admin.ModelAdmin):
    list_display = ['id', 'number', 'date_from', 'date_to', 'status']
    readonly_fields = ['id']
    fields = ['number', 'date_from', 'date_to', 'status', 'stopped_from', 'stopped_to']


my_admin_site.register(LibraryCard, LibraryCardAdmin)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


my_admin_site.register(Organization, OrganizationAdmin)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


my_admin_site.register(Position, PositionAdmin)


class DecisionAdmin(admin.ModelAdmin):
    list_display = ('notes',)
    fields = ('notes',)
    add_form_template = 'kuser/not_exclude.html'
    change_form_template = 'kuser/not_exclude.html'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        reader_id = request.GET.get('reader_id')
        if reader_id:
            reader = Reader.objects.get(pk=reader_id)
            reader.exclusion = True
            reader.work_type = STATUS_READER_ONE.lower()
            reader.notes = obj.notes
            reader.save()
        obj._redirect_after_save = reverse('admin:kuser_reader_changelist')

    def response_add(self, request, obj, post_url_continue=None):
        if hasattr(obj, '_redirect_after_save'):
            return redirect(obj._redirect_after_save)
        return super().response_add(request, obj, post_url_continue)

    def back_to_reader(self, request):
        reader_id = request.GET.get('reader_id')
        if reader_id:
            reader = get_object_or_404(Reader, pk=reader_id)
            return redirect(reverse('admin:kuser_reader_change', args=[reader.pk]))
        return redirect(reverse('admin:kuser_reader_changelist'))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('back_to_reader/', self.admin_site.admin_view(self.back_to_reader), name='back_to_reader'),
        ]
        return custom_urls + urls


my_admin_site.register(Decision, DecisionAdmin)


class ReregistrationAdmin(admin.ModelAdmin):
    list_display = ('text',)
    fields = ('text',)
    readonly_fields = ('text',)

    add_form_template = 'admin/kuser/reregistration_change_form.html'

    #
    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [
    #         path('redo_exclusion/', self.admin_site.admin_view(self.redo_exclusion),
    #              name='redo_exclusion'),
    #     ]
    #     return custom_urls + urls

    # def redo_exclusion(self, request):
    #     logger.debug(f'entered')
    #     reader = Reader.objects.filter(user=request.user).first()
    #     if reader:
    #         logger.debug(f'{reader}')
    #         reader.exclusion = False
    #         reader.work_type = STATUS_READER_TWO.lower()
    #         current_date = datetime.now()
    #         reader.registration_date = current_date
    #         end_of_year = datetime(current_date.year, 12, 31)
    #         reader.ticket_expiration = end_of_year
    #         reader.email_send = True
    #         reader.save()
    #     return redirect(reverse('admin:index'))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('redo_exclusion/', self.admin_site.admin_view(self.redo_exclusion),
                 name='redo_exclusion'),
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        reader = Reader.objects.filter(user=request.user).first()
        logger.debug(f'redo_exclusion')
        if reader:
            logger.debug(f'{reader}')
            reader.exclusion = False
            reader.work_type = STATUS_READER_TWO.lower()
            current_date = datetime.now().date()
            reader.registration_date = current_date
            end_of_year = datetime(current_date.year, 12, 31)
            reader.ticket_expiration = end_of_year
            reader.email_send = True
            if reader.reregistration_dates is None or len(reader.reregistration_dates) == 0:
                reader.reregistration_dates = f"{current_date}"
            else:
                reader.reregistration_dates = f"{reader.reregistration_dates} {current_date}".strip()
            logger.debug(f'{reader}')
            reader.save()
        obj._redirect_after_save = reverse('admin:index')

    def redo_exclusion(self, request, object_id):
        reader = Reader.objects.filter(user=request.user)
        logger.debug(f'redo_exclusion')
        if reader:
            logger.debug(f'{reader}')
            reader.exclusion = False
            reader.work_type = STATUS_READER_TWO.lower()
            current_date = datetime.now().date()
            reader.registration_date = current_date
            end_of_year = datetime(current_date.year, 12, 31)
            reader.ticket_expiration = end_of_year
            reader.email_send = True
            reader.reregistration_dates = f"{reader.reregistration_dates} {current_date}".strip()
            logger.debug(f'{reader}')
            reader.save()
        obj._redirect_after_save = reverse('admin:index')

    def response_add(self, request, obj, post_url_continue=None):
        if hasattr(obj, '_redirect_after_save'):
            return redirect(obj._redirect_after_save)
        return super().response_add(request, obj, post_url_continue)


my_admin_site.register(Reregistration, ReregistrationAdmin)


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    change_list_template = "admin/myuser_change_list.html"

    def has_add_permission(self, request):
        return False

    list_display = (
        'user', 'full_name', 'birth_date', 'organization', 'position', 'ticket_expiration', 'work_type', 'notes')
    list_filter = [TicketNumberFilter, FullNameFilter, OrganizationFilter, BirthDateFilter, RegistrationDateFilter,
                   ReregistrationDateFilter]
    readonly_fields = ('id', 'get_first_name', 'get_last_name', 'middle_name', 'get_user_email')

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else ''

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else ''

    def get_user_email(self, obj):
        return obj.user.email if obj.user else ''

    get_first_name.short_description = 'Имя'
    get_last_name.short_description = 'Фамилия'
    get_user_email.short_description = 'Почта'

    def get_fieldsets(self, request, obj=None):
        if obj is not None and obj.exclusion == True:
            return [
                ('Основная информация', {
                    'fields': (
                        'work_type', 'registration_date', 'ticket_expiration',
                        'get_last_name', 'get_first_name', 'middle_name', 'birth_date', 'education',
                    )
                }),
                ('Организация и Должность', {
                    'fields': ('organization', 'position', 'department', 'library', 'id_number')
                }),
                ('Контактные данные', {
                    'fields': ('phone', 'get_user_email',)
                }),
                ('Адрес', {
                    'fields': ('city', 'street', 'house', 'apartment',)
                }),
                ('Форма обслуживания', {
                    'fields': ('subscriber', 'reading_room', 'kp', 'mba', 'zdd', 'iri', 'all_services')
                }),
                ('Примечание', {
                    'fields': ('notes',)
                }),
            ]
        return [
            ('Основная информация', {
                'fields': (
                    'work_type', 'registration_date', 'ticket_expiration',
                    'get_last_name', 'get_first_name', 'middle_name', 'birth_date', 'education',
                )
            }),
            ('Организация и Должность', {
                'fields': ('organization', 'position', 'department', 'library', 'id_number')
            }),
            ('Контактные данные', {
                'fields': ('phone', 'get_user_email',)
            }),
            ('Адрес', {
                'fields': ('city', 'street', 'house', 'apartment',)
            }),
            ('Форма обслуживания', {
                'fields': ('subscriber', 'reading_room', 'kp', 'mba', 'zdd', 'iri', 'all_services')
            }),
        ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        reader = Reader.objects.filter(user=request.user).first()
        user_library = getattr(reader, 'library', None)
        if user_library:
            qs = qs.filter(library=user_library)
        return qs

    def save_model(self, request, obj, form, change):
        if obj.all_services:
            obj.subscriber = True
            obj.reading_room = True
            obj.kp = True
            obj.mba = True
            obj.zdd = True
            obj.iri = True

        BookCirculation = apps.get_model('kservice', 'BookCirculation')
        circulations = BookCirculation.objects.using('belrw-service-db').filter(reader_id=obj.pk)
        reader = Reader.objects.get(pk=obj.pk)
        obj.has_unclosed_circulations = False

        if obj.library != reader.library:
            if circulations:
                obj.has_unclosed_circulations = True
                self.message_user(request, 'У пользователя есть незакрытые выдачи', level=messages.WARNING)
            else:
                obj.has_unclosed_circulations = False

        if obj.work_type == STATUS_READER_TWO.lower():
            obj.exclusion = False

        if not obj.has_unclosed_circulations:
            super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        if getattr(obj, 'has_unclosed_circulations', False):
            return redirect(reverse('admin:kuser_reader_change', args=[obj.pk]))

        return super().response_change(request, obj)

    def get_full_name(self, obj):
        return obj.user.__str__()

    get_full_name.short_description = 'ФИО'

    change_form_template = 'kuser/library_change.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/exclusion/', self.admin_site.admin_view(self.exclusion),
                 name='exclusion'),
            path('<path:object_id>/perereg/', self.admin_site.admin_view(self.perereg),
                 name='perereg'),
            path('<path:object_id>/view_circulations/', self.admin_site.admin_view(self.view_circulations),
                 name='view_circulations'),
            path('<path:object_id>/print_data/', self.admin_site.admin_view(self.print_data),
                 name='print_data'),
            path('<path:object_id>/make_circ/', self.admin_site.admin_view(self.make_circ),
                 name='make_circ'),
        ]
        return custom_urls + urls

    def view_circulations(self, request, object_id):
        circulation_url = f"{reverse('admin:kservice_bookcirculation_changelist')}?reader_id={object_id}"
        return redirect(circulation_url)

    def make_circ(self, request, object_id):
        circulation_url = f"{reverse('admin:kservice_bookcirculation_add')}?reader_id={object_id}"
        return redirect(circulation_url)

    def print_data(self, request, object_id):
        return redirect(reverse('download_filled_doc'))

    def exclusion(self, request, object_id):
        BookCirculation = apps.get_model('kservice', 'BookCirculation')
        circulations = BookCirculation.objects.using('belrw-service-db').filter(reader_id=object_id)
        reader = Reader.objects.get(pk=object_id)
        reader.has_unclosed_circulations = False

        if circulations:
            for circulation in circulations:
                if circulation.status != _('Returned'):
                    reader.has_unclosed_circulations = True
                    self.message_user(request, 'У пользователя есть незакрытые выдачи', level=messages.WARNING)
                    break
        else:
            reader.has_unclosed_circulations = False
        if not reader.has_unclosed_circulations:
            return redirect(f"{reverse('admin:kuser_decision_add')}?reader_id={object_id}")
        return redirect(reverse('admin:kuser_reader_change', args=[object_id]))

    def perereg(self, request, object_id):
        obj: Reader = get_object_or_404(Reader, pk=object_id)
        current_date = datetime.now().date()
        obj.registration_date = current_date
        end_of_year = datetime(current_date.year, 12, 31)
        obj.ticket_expiration = end_of_year
        obj.email_send = True
        if obj.reregistration_dates is None or len(obj.reregistration_dates) == 0:
            obj.reregistration_dates = f"{current_date}"
        else:
            obj.reregistration_dates = f"{obj.reregistration_dates} {current_date}".strip()
        obj.save()
        return redirect(reverse('admin:kuser_reader_change', args=[object_id]))

    actions = ['exclude_user']

    class Media:
        js = ('js/change_library.js',)


my_admin_site.register(Reader, ReaderAdmin)


class ReaderFirstClassAdmin(admin.ModelAdmin):
    change_list_template = "admin/myuser_change_list.html"

    def has_add_permission(self, request):
        return False

    list_display = (
        'user', 'full_name', 'birth_date', 'library', 'organization', 'position', 'ticket_expiration', 'work_type',
        'notes')
    list_filter = [TicketNumberFilter, FullNameFilter, OrganizationFilter, BirthDateFilter, LibraryFilter,
                   RegistrationDateFilter, ReregistrationDateFilter]
    readonly_fields = ('id', 'get_first_name', 'get_last_name', 'middle_name')

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else ''

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else ''

    get_first_name.short_description = 'Имя'
    get_last_name.short_description = 'Фамилия'

    def get_fieldsets(self, request, obj=None):
        if obj is not None and obj.exclusion == True:
            return [
                ('Основная информация', {
                    'fields': (
                        'work_type', 'registration_date', 'ticket_expiration',
                        'get_last_name', 'get_first_name', 'middle_name'
                    )
                }),
                ('Организация и Должность', {
                    'fields': ('organization', 'position', 'department', 'library', 'id_number')
                }),
                ('Контактные данные', {
                    'fields': ('phone',)
                }),
                ('Адрес', {
                    'fields': ('city', 'street', 'house', 'apartment',)
                }),
                ('Форма обслуживания', {
                    'fields': ('subscriber', 'reading_room', 'kp', 'mba', 'zdd', 'iri', 'all_services')
                }),
                ('Примечание', {
                    'fields': ('notes',)
                }),
            ]
        return [
            ('Основная информация', {
                'fields': (
                    'work_type', 'registration_date', 'ticket_expiration',
                    'get_last_name', 'get_first_name', 'middle_name'
                )
            }),
            ('Организация и Должность', {
                'fields': ('organization', 'position', 'department', 'library', 'id_number')
            }),
            ('Контактные данные', {
                'fields': ('phone',)
            }),
            ('Адрес', {
                'fields': ('city', 'street', 'house', 'apartment',)
            }),
            ('Форма обслуживания', {
                'fields': ('subscriber', 'reading_room', 'kp', 'mba', 'zdd', 'iri', 'all_services')
            }),
        ]

    def save_model(self, request, obj, form, change):
        if obj.all_services:
            obj.subscriber = True
            obj.reading_room = True
            obj.kp = True
            obj.mba = True
            obj.zdd = True
            obj.iri = True

        BookCirculation = apps.get_model('kservice', 'BookCirculation')
        circulations = BookCirculation.objects.using('belrw-service-db').filter(reader_id=obj.pk)
        reader = Reader.objects.get(pk=obj.pk)
        obj.has_unclosed_circulations = False

        if obj.library != reader.library:
            if circulations:
                obj.has_unclosed_circulations = True
                self.message_user(request, 'У пользователя есть незакрытые выдачи', level=messages.WARNING)
            else:
                obj.has_unclosed_circulations = False

        if obj.work_type == STATUS_READER_TWO.lower():
            obj.exclusion = False

        if not obj.has_unclosed_circulations:
            super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        if getattr(obj, 'has_unclosed_circulations', False):
            return redirect(reverse('admin:kuser_reader_change', args=[obj.pk]))

        return super().response_change(request, obj)

    def get_full_name(self, obj):
        return obj.user.__str__()

    get_full_name.short_description = 'ФИО'

    change_form_template = 'kuser/library_change_admin.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/exclusion_admin/', self.admin_site.admin_view(self.exclusion),
                 name='exclusion_admin'),
            path('<path:object_id>/perereg_admin/', self.admin_site.admin_view(self.perereg),
                 name='perereg_admin'),
            path('<path:object_id>/view_circulations_admin/', self.admin_site.admin_view(self.view_circulations),
                 name='view_circulations_admin'),
            path('<path:object_id>/print_data_admin/', self.admin_site.admin_view(self.print_data),
                 name='print_data_admin'),
            path('<path:object_id>/make_circ_admin/', self.admin_site.admin_view(self.make_circ),
                 name='make_circ_admin'),
        ]
        return custom_urls + urls

    def view_circulations(self, request, object_id):
        circulation_url = f"{reverse('admin:kservice_bookcirculationsfirstclass_changelist')}?reader_id={object_id}"
        return redirect(circulation_url)

    def make_circ(self, request, object_id):
        circulation_url = f"{reverse('admin:kservice_bookcirculationsfirstclass_add')}?reader_id={object_id}"
        return redirect(circulation_url)

    def print_data(self, request, object_id):
        return redirect(reverse('download_filled_doc'))

    def exclusion(self, request, object_id):
        BookCirculation = apps.get_model('kservice', 'BookCirculation')
        circulations = BookCirculation.objects.using('belrw-service-db').filter(reader_id=object_id)
        reader = Reader.objects.get(pk=object_id)
        reader.has_unclosed_circulations = False

        if circulations:
            for circulation in circulations:
                if circulation.status != _('Returned'):
                    reader.has_unclosed_circulations = True
                    self.message_user(request, 'У пользователя есть незакрытые выдачи', level=messages.WARNING)
                    break
        else:
            reader.has_unclosed_circulations = False
        if not reader.has_unclosed_circulations:
            return redirect(f"{reverse('admin:kuser_decision_add')}?reader_id={object_id}")
        return redirect(reverse('admin:kuser_readerfirstclass_change', args=[object_id]))

    def perereg(self, request, object_id):
        obj: Reader = get_object_or_404(Reader, pk=object_id)
        current_date = datetime.now().date()
        obj.registration_date = current_date
        end_of_year = datetime(current_date.year, 12, 31)
        obj.ticket_expiration = end_of_year
        if obj.reregistration_dates is None or len(obj.reregistration_dates) == 0:
            obj.reregistration_dates = f"{current_date}"
        else:
            obj.reregistration_dates = f"{obj.reregistration_dates} {current_date}".strip()
        obj.save()
        obj.save()
        return redirect(reverse('admin:kuser_readerfirstclass_change', args=[object_id]))

    actions = ['exclude_user']


my_admin_site.register(ReaderFirstClass, ReaderFirstClassAdmin)


@admin.register(Worker)
class WorkersAdmin(admin.ModelAdmin):
    change_list_template = "admin/worker_change_list.html"
    list_display = ('full_name', 'library', 'role', 'worker_status')
    list_filter = ('library',)
    search_fields = ['user__first_name', 'middle_name', 'user__last_name']
    actions = ['mark_as_dismissed']

    fieldsets = (
        (None, {
            'fields': ('user', 'position', 'role', 'worker_status', 'validity_period')
        }),
        ('Личные данные', {
            'fields': ('registration_date', 'user_first_name', 'user_last_name', 'middle_name', 'birth_date', 'education', 'id_number', 'phone')
        }),
        ('Услуги', {
            'fields': ('library', 'subscriber', 'reading_room', 'kp', 'mba', 'zdd', 'iri', 'all_services', 'notes', 'exclusion')
        }),
    )

    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = _('Имя')

    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = _('Фамилия')

    readonly_fields = ('user_first_name', 'user_last_name', 'middle_name')

    def save_model(self, request, obj, form, change):
        if obj.all_services:
            obj.subscriber = True
            obj.reading_room = True
            obj.kp = True
            obj.mba = True
            obj.zdd = True
            obj.iri = True

        super().save_model(request, obj, form, change)

        role_to_group = {
            ROLE_STATUS_FIRST: 'Системный администратор',
            ROLE_STATUS_SECOND: 'Главный информационный администратор',
            ROLE_STATUS_THIRD: 'Информационный администратор',
            ROLE_STATUS_FOURTH: 'Работники ТБ БЖД',
        }

        if obj.role in role_to_group:
            group_name = role_to_group[obj.role]
            try:
                group = Group.objects.get(name=group_name)
                obj.user.groups.clear()
                obj.user.groups.add(group)
            except Group.DoesNotExist:
                pass
        obj.user.save()

    def mark_as_dismissed(self, request, queryset):
        updated_count = queryset.update(worker_status=Worker.WORKER_STATUS_DISMISSED)
        self.message_user(request, _('%d worker(s) were successfully marked as dismissed.') % updated_count)

    def has_add_permission(self, request, obj=None):
        return False

    def get_display_name(self, key, choices):
        for choice_key, display_name in choices:
            if choice_key == key:
                return display_name
        return key

    mark_as_dismissed.short_description = _('Mark selected workers as dismissed')

my_admin_site.register(Worker, WorkersAdmin)
