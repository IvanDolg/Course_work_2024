import logging
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from kuser.constants import library_aliases, EDUCATION_TYPE, LIBRARY_TYPE, STATUS, STATUS_ACTIVE, WORK_TYPE, \
    WORKER_STATUS_WORKS, ROLE_TYPE, READER_STATUSES, STATUS_READER_TWO, ROLE_STATUS_FIRST, ROLE_STATUS_SECOND, \
    ROLE_STATUS_THIRD, ROLE_STATUS_FOURTH
from kuser.validators import validate_phone_number, validate_id_number
from main.models import DateTimeModel
from django.contrib.auth.models import AbstractUser, Group
from django.urls import reverse

logger = logging.getLogger('main')


class MyUser(AbstractUser):
    first_name = models.CharField(max_length=150, blank=False, verbose_name=_('first name'))
    last_name = models.CharField(max_length=150, blank=False, verbose_name=_('last name'))
    email = models.EmailField(blank=False, verbose_name=_('email address'))
    validity_period = models.DateField(default=timezone.now, null=False, blank=False, verbose_name=_('Validity period'))

    def save(self, *args, **kwargs):
        if isinstance(self.date_joined, datetime.datetime):
            self.validity_period = datetime.date(self.date_joined.year, 12, 31)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username}'

    class Meta:
        app_label = 'kuser'
        verbose_name = _('My user')
        verbose_name_plural = _('My users')

    def to_dict_auth(self):
        return {
            'email': self.email,
            'login': self.username,
            'password': '********',
        }


class Department(DateTimeModel):
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Department'))

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Department')
        verbose_name_plural = _('Department')

    def __str__(self):
        return self.name


class AbstractUser(DateTimeModel):
    registration_date = models.DateField(max_length=10, verbose_name=_('Registration date'))
    middle_name = models.CharField(max_length=150, blank=True, verbose_name=_('Middle name'))
    birth_date = models.DateField(max_length=10, null=True, blank=True, verbose_name=_('Date of birth'))
    education = models.CharField(max_length=30, choices=EDUCATION_TYPE, verbose_name=_('Education'))
    id_number = models.CharField(max_length=50, verbose_name=_('Id number'), validators=[validate_id_number])
    phone = models.CharField(max_length=15, verbose_name=_('Phone'), validators=[validate_phone_number])
    library = models.CharField(max_length=75, choices=LIBRARY_TYPE, verbose_name=_('Library'))
    subscriber = models.BooleanField(default=False, verbose_name=_('Subscriber'))
    reading_room = models.BooleanField(default=False, verbose_name=_('Reading room'))
    kp = models.BooleanField(default=False, verbose_name=_('KP'))
    mba = models.BooleanField(default=False, verbose_name=_('MDA'))
    zdd = models.BooleanField(default=False, verbose_name=_('ZDD'))
    iri = models.BooleanField(default=False, verbose_name=_('IRI'))
    all_services = models.BooleanField(default=False, verbose_name=_('All services'))
    notes = models.TextField(max_length=1000, blank=True, null=True, verbose_name=_('Notes'))
    exclusion = models.BooleanField(verbose_name=_('Exclusion'), default=False)

    def has_permission(self):
        return not self.exclusion

    def clean(self):
        if self.birth_date:
            if self.birth_date > datetime.date.today():
                raise ValidationError({'birth_date': _('Дата рождения не может быть изменена в будущем.')})

            if self.registration_date and self.birth_date > self.registration_date:
                raise ValidationError({'birth_date': _('Дата рождения не может быть позднее даты регистрации.')})

        super().clean()

    class Meta:
        app_label = 'kuser'
        abstract = True


class LibraryCard(DateTimeModel):
    number = models.CharField(null=True, blank=True, max_length=16, verbose_name=_('The number of the library card'),
                              help_text=_('Generated automatically'))
    date_from = models.DateField(null=True, blank=True, verbose_name=_('Date of issue'),
                                 help_text=_('Date of the library card (from)'))
    date_to = models.DateField(null=True, blank=True, verbose_name=_('Validity period'),
                               help_text=_('The validity period of the library card (up to)'))
    status = models.CharField(max_length=16, choices=STATUS, default=STATUS_ACTIVE,
                              verbose_name=_('The status of the library card'))
    stopped_from = models.DateField(null=True, blank=True, verbose_name=_('Date of suspension'),
                                    help_text=_('Date of the beginning of the suspension of the library card (from)'))
    stopped_to = models.DateField(null=True, blank=True, verbose_name=_('The period of suspension'),
                                  help_text=_('The end date of the suspension of the library card (before)'))

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Library card')
        verbose_name_plural = _('Library cards')


class Organization(DateTimeModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Organization'))

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')

    def __str__(self):
        return self.name


class Position(DateTimeModel):
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Position'))

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Position')
        verbose_name_plural = _('Positions')

    def __str__(self):
        position_name = self.name if self.name else _('No Position')
        return f"{position_name}"


class Decision(DateTimeModel):
    notes = models.TextField(max_length=1000, blank=True, null=True, verbose_name=_('Notes'))

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Decision')
        verbose_name_plural = _('Decision')


class Reregistration(DateTimeModel):
    text = models.TextField(max_length=1000, verbose_name=_(''), default='Уважаемый пользователь, для работы с системой вам необходимо '
                                                                         'перерегистрироваться. Нажмите кнопку справа.')

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Reregistration')
        verbose_name_plural = _('Reregistration')


class Reader(AbstractUser):
    user = models.ForeignKey(null=True, blank=False, to=MyUser, related_name='reader', on_delete=models.SET_NULL, verbose_name=_('Account'))
    work_type = models.CharField(max_length=16, default=STATUS_READER_TWO.lower(), choices=READER_STATUSES, verbose_name=_('The status of the place of work'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('City'))
    street = models.CharField(max_length=100, blank=True, verbose_name=_('Street'))
    house = models.CharField(max_length=50, blank=True, verbose_name=_('House'))
    apartment = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Apartment'))
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name=_('Department'))
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name=_('Organization'))
    position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name=_('Position'), related_name='readers_position')
    ticket_expiration = models.DateField(verbose_name=_('Expiration date'), null=True)
    email_send = models.BooleanField(verbose_name=_('Is expired'), default=True)
    reregistration_dates = models.CharField(verbose_name=_('Registration dates'), max_length=1000, blank=True, null=True)

    def full_name(self):
        return (f'{self.user.last_name if self.user else ""} '
                f'{self.user.first_name if self.user else ""} ' 
                f'{self.middle_name}')

    full_name.short_description = 'ФИО'

    def save(self, *args, **kwargs):
        if self.registration_date:
            if isinstance(self.registration_date, (datetime.date, datetime.datetime)):
                self.ticket_expiration = datetime.date(self.registration_date.year, 12, 31)

        if not self.ticket_expiration:
            current_date = datetime.now()
            self.ticket_expiration = datetime(current_date.year, 12, 31)

        if self.all_services:
            self.subscriber = True
            self.reading_room = True
            self.kp = True
            self.mba = True
            self.zdd = True
            self.iri = True

        if self.user and len(self.user.username) == 5:
            self.user.username = f'{self.user.username}{library_aliases.get(self.library)}'
            self.user.save()

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        user: MyUser = MyUser.objects.get(pk=self.user.pk)
        user.is_active = False
        user.save()
        super(Reader, self).delete(using, keep_parents)

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Reader')
        verbose_name_plural = _('Readers')

    def __str__(self):
        return f'{self.user.username if self.user else ""} {self.full_name()}'

    def to_dict_info(self):
        return {
            'education': self.get_education_display(),
            'birth_date': self.birth_date,
            'phone': self.phone,
            'organization': self.organization.name,
            'department': self.department.name,
            'position': self.position.name,
            'address': f'г. {self.city}, ул. {self.street}, д. {self.house}, кв. {self.apartment}'
        }

    def to_dict_auth(self):
        return {
            'email': self.user.email,
            'login': self.user.username,
            'password': '********',
        }

    def get_absolute_url(self):
        return reverse('admin:app_label_reader_change', args=[self.pk])


class ReaderFirstClass(Reader):
    class Meta:
        app_label = 'kuser'
        verbose_name = _('Reader')
        verbose_name_plural = _('Readers')
        proxy = True


class Worker(AbstractUser):
    worker_status = models.CharField(max_length=100, choices=STATUS, default=WORKER_STATUS_WORKS, verbose_name=_('Worker status'))
    validity_period = models.DateField(max_length=10, null=True, blank=True, verbose_name=_('Validity period'))
    user = models.ForeignKey(null=True, blank=False, to=MyUser, related_name='worker', on_delete=models.SET_NULL, verbose_name=_('Account'))
    position = models.CharField(max_length=100, verbose_name=_('Position'))
    role = models.CharField(max_length=100, choices=ROLE_TYPE, verbose_name=_('Role'))

    def full_name(self):
        return f'{self.user.last_name} {self.user.first_name} {self.middle_name}' if self.user else ''
    full_name.short_description = _('Full Name')

    def clean(self):
        super().clean()
        # Check that at least one service is selected
        if not (
                self.subscriber or self.reading_room or self.kp or self.mba or self.zdd or self.iri or self.all_services):
            raise ValidationError(
                _('Должна быть выбрана хотя бы одна услуга (Абонентская, Читальный зал, КП, МДА, ЭДД, ИРИ или Все услуги).'))


    def save(self, *args, **kwargs):
        if self.all_services:
            self.subscriber = True
            self.reading_room = True
            self.kp = True
            self.mba = True
            self.zdd = True
            self.iri = True
        super(Worker, self).save(*args, **kwargs)

        if len(self.user.username) == 5:
            self.user.username = f'{self.user.username}{library_aliases.get(self.library)}'
            self.user.save()

        role_to_group = {
            ROLE_STATUS_FIRST: 'Системный администратор',
            ROLE_STATUS_SECOND: 'Главный информационный администратор',
            ROLE_STATUS_THIRD: 'Информационный администратор',
            ROLE_STATUS_FOURTH: 'Работники ТБ БЖД',
        }

        if self.role in role_to_group:
            group_name = role_to_group[self.role]
            try:
                group = Group.objects.get(name=group_name)
                self.user.groups.clear()
                self.user.groups.add(group)
            except Group.DoesNotExist:
                pass

        self.user.save()

    def __str__(self):
        return f'{self.user.username if self.user else ""} {self.full_name()}'

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Worker')
        verbose_name_plural = _('Workers')

    def to_dict_info(self):
        return {
            'education': self.get_education_display(),
            'birth_date': self.birth_date,
            'phone': self.phone,
            'position': self.position,
        }

    def to_dict_auth(self):
        return {
            'email': self.user.email,
            'login': self.user.username,
            'password': '********',
        }


class OtherNaturalPerson(AbstractUser):
    user = models.ForeignKey(null=True, blank=False, to=MyUser, related_name='other_natural_person', on_delete=models.SET_NULL,
                             verbose_name=_('Account'))
    validity_period = models.DateField(max_length=10, null=True, blank=True, verbose_name=_('Validity period'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('City'))
    street = models.CharField(max_length=100, blank=True, verbose_name=_('Street'))
    house = models.CharField(max_length=50, blank=True, verbose_name=_('House'))
    apartment = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Apartment'))

    class Meta:
        app_label = 'kuser'
        verbose_name = _('Other natural person')
        verbose_name_plural = _('Other natural person')

    def to_dict_info(self):
        return {
            'education': self.get_education_display(),
            'birth_date': self.birth_date,
            'phone': self.phone,
            'address': f'г. {self.city}, ул. {self.street}, д. {self.house}, кв. {self.apartment}'
        }

    def to_dict_auth(self):
        return {
            'email': self.user.email,
            'login': self.user.username,
            'password': '********',
        }