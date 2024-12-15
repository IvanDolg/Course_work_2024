import logging

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.db import transaction
from datetime import date, timedelta
from django import forms
import datetime
import re
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.forms import Select

from kuser.constants import EDUCATION_TYPE
from kuser.models import Reader, MyUser, AbstractUser, Department, Organization, Position, Worker, library_aliases, \
    OtherNaturalPerson
from kuser.utils import parse_address, generate_username_with_initials, generate_username_without_reader
from kuser.validators import validate_cyrillic_name, validate_id_number, validate_custom_email, validate_phone_number, \
    validate_city_name, validate_street_name, validate_house_number, validate_apartment_number, validate_password, \
    validate_notes, validate_validity_period

logger = logging.getLogger(__name__)

widget_atr = {
    'data-placeholder': 'Select or add an organization',
    'data-allow-clear': 'true',
    'data-minimum-input-length': 1,
}

registration_date = forms.DateField(
    widget=forms.DateInput(attrs={'type': 'date'}),
    required=True,
    label='Дата регистрации',
    initial=datetime.date.today
)


class ReaderCreationForm(forms.ModelForm):
    first_name = forms.CharField( max_length=75, required=True, label='Имя', validators=[validate_cyrillic_name])
    last_name = forms.CharField(max_length=75, required=True, label='Фамилия', validators=[validate_cyrillic_name])
    middle_name = forms.CharField(max_length=75, required=False, label='Отчество', validators=[validate_cyrillic_name])
    id_number = forms.CharField(max_length=5, required=True, label='Номер удостоверения', validators=[validate_id_number])
    email = forms.CharField(max_length=30, required=True, label='Электронная почта', validators=[validate_custom_email])
    phone = forms.CharField(required=True, label='Номер телефона', validators=[validate_phone_number])
    city = forms.CharField(required=True, label='Город', validators=[validate_city_name])
    street = forms.CharField(required=True, label='Улица', validators=[validate_street_name])
    house = forms.CharField(required=True, label='Дом/корпус', validators=[validate_house_number])
    apartment = forms.CharField(required=False, label='Квартира', validators=[validate_apartment_number])
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Дата рождения')

    class Meta:
        model = Reader
        fields = (
            'last_name', 'first_name', 'middle_name',
            'id_number', 'birth_date', 'education',
            'email', 'phone', 'city', 'street',
            'house', 'apartment', 'library',
            'organization', 'department', 'position',
        )
        widgets = {
            'organization': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
            'position': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
            'department': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
            'education': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
            'library': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
        }

    def __init__(self, *args, **kwargs):
        super(ReaderCreationForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['middle_name'].initial = self.instance.user.middle_name
            self.fields['id_number'].initial = self.instance.id_number
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.phone
            self.fields['city'].initial = self.instance.city
            self.fields['street'].initial = self.instance.street
            self.fields['house'].initial = self.instance.house
            self.fields['apartment'].initial = self.instance.apartment
            self.fields['birth_date'].initial = self.instance.birth_date

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = MyUser.objects.filter(email=email).first()
        if user is not None and user.is_active:
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        reader = Reader.objects.filter(id_number=id_number).first()
        if reader is not None and reader.user is not None and reader.user.is_active:
            raise ValidationError('Пользователь с таким номером удостоверения уже существует.')
        return id_number

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date > date.today():
            raise ValidationError('Дата рождения не может быть в будущем.')
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        reader = Reader.objects.filter(phone=phone).first()
        if reader is not None and reader.user is not None and reader.user.is_active:
            raise ValidationError('Пользователь с таким номером телефона уже существует.')
        return phone

    @transaction.atomic
    def save(self, commit=True):
        reader = super(ReaderCreationForm, self).save(commit=False)
        reader.registration_date = date.today()

        email = self.cleaned_data['email']
        user = MyUser.objects.filter(email=email).first()

        if user is None:
            user = MyUser()

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = email
        user.username = generate_username_without_reader(MyUser.objects.aggregate(Max('id'))['id__max'] + 1, reader.library)
        user.is_active = False

        user.save()
        reader.user = user

        tb_bjd_group = Group.objects.get(name='Пользователь работник Белорусской железной дороги')
        user.groups.add(tb_bjd_group)

        if commit:
            reader.save()

        return reader


class ReaderCreationPasswordForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = Reader
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Имя пользователя"
        self.fields['password1'].label = "Новый пароль"
        self.fields['password2'].label = "Подтвердите новый пароль"

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")

        if not password1:
            raise ValidationError("Это поле обязательно для заполнения.")
        if len(password1) < 8:
            raise ValidationError("Пароль должен содержать не менее 8 символов.")
        if len(password1) > 15:
            raise ValidationError("Пароль не может быть длиннее 15 символов.")

        if not re.search(r'[A-ZА-Я]', password1):
            raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву.")

        if not re.search(r'[a-zа-я]', password1):
            raise ValidationError("Пароль должен содержать хотя бы одну строчную букву.")

        if not re.search(r'[0-9]', password1):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру.")

        if not re.search(r'[\W_]', password1):
            raise ValidationError("Пароль должен содержать хотя бы один специальный символ.")

        if not (re.search(r'[A-ZА-Я]', password1) and re.search(r'[a-zа-я]', password1)):
            raise ValidationError("Пароль должен содержать буквы верхнего и нижнего регистра.")

        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Пароли не совпадают.")

        return cleaned_data


class PasswordRecoveryForm(forms.Form):
    email = forms.CharField(
        max_length=30,
        required=True,
        label='Электронная почта',
        validators=[validate_custom_email]
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not MyUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким адресом электронной почты не найден.")
        return email


class PasswordCreationPasswordForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = MyUser
        fields = [
            'username',
            'password1',
            'password2'
        ]

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")

        if not password1:
            raise ValidationError("Это поле обязательно для заполнения.")
        if len(password1) < 8:
            raise ValidationError("Пароль должен содержать не менее 8 символов.")
        if len(password1) > 15:
            raise ValidationError("Пароль не может быть длиннее 15 символов.")
        if not re.search(r'[A-Z]', password1):
            raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву.")
        if not re.search(r'[a-z]', password1):
            raise ValidationError("Пароль должен содержать хотя бы одну строчную букву.")
        if not re.search(r'[0-9]', password1):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру.")
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
        #     raise ValidationError("Пароль должен содержать хотя бы один специальный символ.")

        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(self.cleaned_data["password1"])
        if commit:
            instance.save()
        return instance


class ChangeEmailForm(forms.ModelForm):
    email = forms.CharField(label='Email', widget=forms.EmailInput)
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = MyUser
        fields = [
            'username',
            'email'
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        logger.debug(MyUser.objects.filter(email=email).first())

        if MyUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")

        return email

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.email = self.cleaned_data["email"]
        if commit:
            instance.save()
        return instance


def convert_education_type(request):
    post_data = request.POST.copy()

    education_name = post_data.get('education')

    EDUCATION_NAME_TO_KEY = {value: key for key, value in EDUCATION_TYPE}
    if education_name in EDUCATION_NAME_TO_KEY:
        post_data['education'] = EDUCATION_NAME_TO_KEY[education_name]

    logger.debug(post_data)

    return ProfileForm(post_data)


class ProfileForm(forms.ModelForm):
    username = forms.CharField()
    address = forms.CharField()
    department = forms.CharField()
    organization = forms.CharField()
    position = forms.CharField()

    class Meta:
        model = Reader
        fields = (
            'username', 'education', 'phone', 'birth_date',
            'organization', 'department', 'position', 'address'
        )

    def clean_organization(self):
        organization_name = self.cleaned_data.get('organization')
        if isinstance(organization_name, str):
            organization, created = Organization.objects.get_or_create(name=organization_name)
            return organization
        return organization_name

    def clean_department(self):
        department_name = self.cleaned_data.get('department')
        if isinstance(department_name, str):
            department, created = Department.objects.get_or_create(name=department_name)
            return department
        return department_name

    def clean_position(self):
        position_name = self.cleaned_data.get('position')
        if isinstance(position_name, str):
            position, created = Position.objects.get_or_create(name=position_name)
            return position
        return position_name

    @transaction.atomic
    def save(self, commit=True):
        username = self.cleaned_data['username']
        reader = Reader.objects.filter(user__username=username).first()
        if reader:
            reader.education = self.cleaned_data['education']
            reader.phone = self.cleaned_data['phone']
            reader.birth_date = self.cleaned_data['birth_date']
            reader.organization = self.cleaned_data['organization']
            reader.department = self.cleaned_data['department']
            reader.position = self.cleaned_data['position']
            reader.city, reader.street, reader.house, reader.apartment = parse_address(self.cleaned_data['address'])

            reader.save()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    password1 = forms.CharField(
        label="Password",
        required=False,
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Password confirmation",
        required=False,
        widget=forms.PasswordInput
    )

    class Meta:
        model = MyUser
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.pk is None or self.cleaned_data.get('password1'):
            instance.set_password(self.cleaned_data['password1'])
        else:
            instance.password = MyUser.objects.get(pk=instance.pk).password

        if commit:
            instance.save()

        return instance

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return password2


class WorkerCreationForm(forms.ModelForm):
    registration_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Дата регистрации')
    validity_period = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Срок действия', validators=[validate_validity_period])
    first_name = forms.CharField(max_length=75, required=True, label='Имя', validators=[validate_cyrillic_name])
    last_name = forms.CharField(max_length=75, required=True, label='Фамилия', validators=[validate_cyrillic_name])
    middle_name = forms.CharField(max_length=75, required=False, label='Отчество', validators=[validate_cyrillic_name])
    id_number = forms.CharField(max_length=5, required=True, label='Номер удостоверения', validators=[validate_id_number])
    email = forms.CharField(max_length=30, required=True, label='Электронная почта', validators=[validate_custom_email])
    phone = forms.CharField(required=True, label='Номер телефона', validators=[validate_phone_number])
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Дата рождения')
    subscriber = forms.BooleanField(initial=False, label='Абонемент', required=False)
    reading_room = forms.BooleanField(initial=False, label='Читательский Зал', required=False)
    kp = forms.BooleanField(initial=False, label='КП', required=False)
    mba = forms.BooleanField(initial=False, label='МДА', required=False)
    zdd = forms.BooleanField(initial=False, label='ЭДД', required=False)
    iri = forms.BooleanField(initial=False, label='ИРИ', required=False)
    all_services = forms.BooleanField(initial=False, label='Все', required=False)
    notes = forms.CharField(max_length=100, label='Примечание', required=False, validators=[validate_notes])
    position = forms.CharField(max_length=50, label='Должность')

    class Meta:
        model = Worker
        fields = (
            'registration_date', 'validity_period',
            'last_name', 'first_name', 'middle_name',
            'education', 'position', 'birth_date', 'library', 'role',
            'id_number', 'phone', 'email',
            'subscriber', 'reading_room', 'kp', 'mba', 'zdd', 'iri', 'all_services',
            'notes',
        )
        widgets = {
            'role':  Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
            'education': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
            'library': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
        }

    def __init__(self, *args, **kwargs):
        super(WorkerCreationForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['registration_date'].initial = date.today().strftime('%Y-%m-%d')
            self.fields['validity_period'].initial = date(date.today().year, 12, 31).strftime(
                '%Y-%m-%d')
        else:
            self.fields['registration_date'].initial = self.instance.registration_date.strftime(
                '%Y-%m-%d')
            self.fields['validity_period'].initial = self.instance.validity_period.strftime(
                '%Y-%m-%d')
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['middle_name'].initial = self.instance.middle_name
            self.fields['id_number'].initial = self.instance.id_number
            self.fields['role'].initial = self.instance.role
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.phone
            self.fields['birth_date'].initial = self.instance.birth_date
            self.fields['notes'].initial = self.instance.notes
            self.fields['position'].initial = self.instance.position
            self.fields['subscriber'].initial = self.instance.subscriber
            self.fields['reading_room'].initial = self.instance.reading_room
            self.fields['kp'].initial = self.instance.kp
            self.fields['mba'].initial = self.instance.mba
            self.fields['zdd'].initial = self.instance.zdd
            self.fields['iri'].initial = self.instance.iri
            self.fields['all_services'].initial = self.instance.all_services

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = MyUser.objects.filter(email=email).first()
        if user is not None and user.is_active:
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        reader = Worker.objects.filter(id_number=id_number).first()
        if reader is not None and reader.user is not None and reader.user.is_active:
            raise ValidationError('Пользователь с таким номером удостоверения уже существует.')
        return id_number

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date > date.today():
            raise ValidationError('Дата рождения не может быть в будущем.')
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        reader = Worker.objects.filter(phone=phone).first()
        if reader is not None and reader.user is not None and reader.user.is_active:
            raise ValidationError('Пользователь с таким номером телефона уже существует.')
        return phone

    @transaction.atomic
    def save(self, commit=True):
        worker = super(WorkerCreationForm, self).save(commit=False)
        worker.registration_date = date.today()

        email = self.cleaned_data['email']
        user = MyUser.objects.filter(email=email).first()

        if user is None:
            user = MyUser()

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = email

        # Generate username with initials and library code
        user.username = generate_username_with_initials(
            MyUser.objects.aggregate(Max('id'))['id__max'] + 1,
            self.cleaned_data['first_name'],
            self.cleaned_data['last_name'],
            self.cleaned_data.get('middle_name'),
            worker.library
        )

        user.is_active = False

        if self.cleaned_data.get('all_services'):
            worker.subscriber = True
            worker.reading_room = True
            worker.kp = True
            worker.mba = True
            worker.zdd = True
            worker.iri = True

        user.save()
        worker.user = user

        # Assign the user to a specific group
        tb_bjd_group = Group.objects.get(name='Работники ТБ БЖД')
        user.groups.add(tb_bjd_group)

        if commit:
            worker.save()

        return worker


class OtherNaturalPersonForm(forms.ModelForm):
    registration_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Дата регистрации')
    validity_period = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Срок действия')
    first_name = forms.CharField(max_length=75, required=True, label='Имя', validators=[validate_cyrillic_name])
    last_name = forms.CharField(max_length=75, required=True, label='Фамилия', validators=[validate_cyrillic_name])
    middle_name = forms.CharField(max_length=75, required=False, label='Отчество', validators=[validate_cyrillic_name])
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label='Дата рождения')
    email = forms.CharField(max_length=30, required=True, label='Электронная почта', validators=[validate_custom_email])
    phone = forms.CharField(required=True, label='Номер телефона', validators=[validate_phone_number])
    city = forms.CharField(required=True, label='Город', validators=[validate_city_name])
    street = forms.CharField(required=True, label='Улица', validators=[validate_street_name])
    house = forms.CharField(required=True, label='Дом/корпус', validators=[validate_house_number])
    apartment = forms.CharField(required=False, label='Квартира', validators=[validate_apartment_number])
    subscriber = forms.BooleanField(initial=False, label='Абонемент', required=False)
    reading_room = forms.BooleanField(initial=False, label='Читательский Зал', required=False)
    kp = forms.BooleanField(initial=False, label='КП', required=False)
    mba = forms.BooleanField(initial=False, label='МДА', required=False)
    zdd = forms.BooleanField(initial=False, label='ЭДД', required=False)
    iri = forms.BooleanField(initial=False, label='ИРИ', required=False)
    all_services = forms.BooleanField(initial=False, label='Все', required=False)
    notes = forms.CharField(max_length=100, label='Примечание', required=False, validators=[validate_notes])

    class Meta:
        model = OtherNaturalPerson
        fields = (
            'registration_date', 'validity_period',
            'last_name', 'first_name', 'middle_name',
            'education', 'birth_date',
            'phone', 'email', 'library',
            'city', 'street', 'house', 'apartment',
            'subscriber', 'reading_room', 'kp', 'mba', 'zdd', 'iri', 'all_services',
        )
        widgets = {
            'education': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
            'library': Select(attrs={'class': 'form-control', 'style': 'height: 40px;'}),
        }

    def __init__(self, *args, **kwargs):
        super(OtherNaturalPersonForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['registration_date'].initial = date.today().strftime('%Y-%m-%d')
            self.fields['validity_period'].initial = date(date.today().year, 12, 31).strftime(
                '%Y-%m-%d')
        else:
            self.fields['registration_date'].initial = self.instance.registration_date.strftime(
                '%Y-%m-%d')
            self.fields['validity_period'].initial = self.instance.validity_period.strftime(
                '%Y-%m-%d')
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['middle_name'].initial = self.instance.middle_name
            self.fields['birth_date'].initial = self.instance.birth_date.strftime('%Y-%m-%d')
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.phone
            self.fields['city'].initial = self.instance.city
            self.fields['street'].initial = self.instance.street
            self.fields['house'].initial = self.instance.house
            self.fields['apartment'].initial = self.instance.apartment
            self.fields['subscriber'].initial = self.instance.subscriber
            self.fields['reading_room'].initial = self.instance.reading_room
            self.fields['kp'].initial = self.instance.kp
            self.fields['mba'].initial = self.instance.mba
            self.fields['zdd'].initial = self.instance.zdd
            self.fields['iri'].initial = self.instance.iri
            self.fields['all_services'].initial = self.instance.all_services
            self.fields['notes'].initial = self.instance.notes

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = MyUser.objects.filter(email=email).first()
        if user is not None and user.is_active:
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > date.today():
            raise ValidationError('Дата рождения не может быть в будущем.')
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        reader = Worker.objects.filter(phone=phone).first()
        if reader is not None and reader.user is not None and reader.user.is_active:
            raise ValidationError('Пользователь с таким номером телефона уже существует.')
        return phone

    @transaction.atomic
    def save(self, commit=True):
        other_person = super(OtherNaturalPersonForm, self).save(commit=False)
        other_person.registration_date = self.cleaned_data['registration_date']
        other_person.validity_period = self.cleaned_data['validity_period']

        email = self.cleaned_data['email']
        user = MyUser.objects.filter(email=email).first()

        if user is None:
            user = MyUser()

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.middle_name = self.cleaned_data.get('middle_name', '')
        user.email = email
        user.username = generate_username_without_reader(MyUser.objects.aggregate(Max('id'))['id__max'] + 1,
                                                         other_person.library)
        user.is_active = False

        if self.cleaned_data.get('all_services'):
            other_person.subscriber = True
            other_person.reading_room = True
            other_person.kp = True
            other_person.mba = True
            other_person.zdd = True
            other_person.iri = True

        user.save()
        other_person.user = user

        tb_bjd_group = Group.objects.get(name='Пользователь иное физическое лицо')
        user.groups.add(tb_bjd_group)

        if len(user.username) == 5:
            user.username = f'{user.username}{library_aliases.get(other_person.library)}'
            user.save()

        if commit:
            other_person.save()

        return other_person
