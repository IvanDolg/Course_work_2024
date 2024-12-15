import re
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_validity_period(value):
    today = timezone.now().date()
    if value < today:
        raise ValidationError('Срок действия не может быть установлен на прошлую дату.')


def validate_cyrillic_name(value):
    if not re.match(r'^[А-ЯЁ][а-яё]*(?:[-\'\s][А-ЯЁа-яё]+)*$', value):
        raise ValidationError(
            'Поле может содержать только буквы кириллицы, апостроф, дефис и должно начинаться с заглавной буквы.'
        )
    if len(value) > 30:
        raise ValidationError('Длина поля не должна превышать 30 символов.')


def validate_id_number(value):
    if not value.isdigit():
        raise ValidationError('Номер удостоверения может содержать только цифры.')
    if int(value) > 99999:
        raise ValidationError('Номер удостоверения не может превышать 99999.')


def validate_password(value):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,15}$'
    if not re.match(pattern, value):
        raise ValidationError('Пароль должен содержать буквы верхнего и нижнего регистра, цифры и спецсимволы, и быть длиной от 8 до 15 символов.')


def validate_notes(value):
    if value == '':
        return
    pattern = r'^[А-ЯЁа-яё0-9.,;:!?(){}\[\]\'\"—-]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Поле может содержать только буквы кириллицы, цифры и знаки препинания.'
        )
    if len(value) > 1000:
        raise ValidationError('Примечание не должно превышать 1000 символов.')

def validate_custom_email(value):
    if len(value) > 30:
        raise ValidationError('Электронная почта не может быть длиннее 30 символов.')

    email_regex = r'^[A-Za-z0-9]+(?:[A-Za-z0-9._-])*@[A-Za-z0-9]+\.[A-Za-z]{2,}$'
    if not re.match(email_regex, value):
        raise ValidationError('Электронная почта должна быть в формате "user@domain.com".')

    local_part, domain_part = value.rsplit('@', 1)

    if len(local_part) > 64:
        raise ValidationError('Локальная часть электронной почты (до "@") не может быть длиннее 64 символов.')

    if len(domain_part) > 255:
        raise ValidationError('Доменная часть электронной почты (после "@") не может быть длиннее 255 символов.')

    if '..' in local_part:
        raise ValidationError('Локальная часть электронной почты не может содержать последовательные точки.')

    if local_part.startswith('.') or local_part.endswith('.'):
        raise ValidationError('Локальная часть электронной почты не может начинаться или заканчиваться на точку.')

    if '..' in domain_part:
        raise ValidationError('Доменная часть электронной почты не может содержать последовательные точки.')

    if domain_part.startswith('.') or domain_part.endswith('.'):
        raise ValidationError('Доменная часть электронной почты не может начинаться или заканчиваться на точку.')

    domain_regex = r'^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    if not re.match(domain_regex, domain_part):
        raise ValidationError('Доменная часть электронной почты должна содержать только буквы, цифры, точки или дефисы.')

    local_regex = r'^[A-Za-z0-9._%+-]+$'
    if not re.match(local_regex, local_part):
        raise ValidationError('Локальная часть электронной почты может содержать только буквы, цифры, точки, дефисы и символы "_", "%", "+", "-".')

    if not re.match(email_regex, value):
        raise ValidationError('Электронная почта должна быть в формате user@domain.com.')


def validate_phone_number(value):
    phone_number = value.replace(' ', '')

    phone_regex = r'^\+?\d{1,4}-?\d{2,4}-?\d{2,3}-?\d{2,3}-?\d{2,3}$'

    if not re.match(phone_regex, phone_number):
        raise ValidationError('Номер телефона должен быть в формате +375-99-999-99-99.')

    digits_count = sum(c.isdigit() for c in phone_number)
    if digits_count != 12:
        raise ValidationError('Номер телефона должен содержать ровно 12 цифр, включая код страны.')


def validate_city_name(value):
    city_regex = r'^[А-ЯЁ][а-яё0-9-]*([ ][А-ЯЁ][а-яё0-9-]*)*$'
    if not re.match(city_regex, value):
        raise ValidationError(
            'Название города может содержать только буквы кириллицы, цифры 0-9, символ "-", и каждое слово должно начинаться с заглавной буквы.')

    if not (2 <= len(value) <= 30):
        raise ValidationError('Название города должно быть длиной от 2 до 30 символов.')


def validate_street_name(value):
    street_regex = r'^[А-ЯЁ][а-яё0-9-.,]*([ ][А-ЯЁ][а-яё0-9-.,]*)*$'
    if not re.match(street_regex, value):
        raise ValidationError(
            'Название улицы может содержать только буквы кириллицы, цифры 0-9, символы "-", "," и ".", и должно начинаться с заглавной буквы.')

    if not (3 <= len(value) <= 50):
        raise ValidationError('Название улицы должно быть длиной от 3 до 50 символов.')


def validate_house_number(value):
    house_regex = r'^[0-9А-Яа-я]+(/?[0-9А-Яа-я]*)$'
    if not re.match(house_regex, value):
        raise ValidationError(
            'Поле дом/корпус должно содержать только цифры 0-9, буквы кириллицы и символ "/".')

    if not (1 <= len(value) <= 7):
        raise ValidationError('Поле дом/корпус должно быть длиной от 1 до 7 символов.')


def validate_apartment_number(value):
    if not value.isdigit():
        raise ValidationError('Квартира может содержать только цифры 0-9.')

    if not (1 <= len(value) <= 5):
        raise ValidationError('Номер квартиры должен быть длиной от 1 до 5 цифр.')
