import logging
import transliterate

from kuser.models import Reader, MyUser, AbstractUser

logger = logging.getLogger(__name__)

library_aliases = {
    'Scientific and Technical Library': 'НТБ',
    'Technical Library of the Minsk Branch': 'НОД-1мн',
    'Technical Library of the Baranovichi branch': 'НОД-2брн',
    'Technical Library of the Brest branch': 'НОД-3бр',
    'Technical Library of the Gomel branch': 'НОД-4гмл',
    'Technical Library of the Mogilev branch': 'НОД-5мгл',
    'Technical Library of the Vitebsk Branch': 'НОД-6втб',
    'Orsha Library Point': 'НОД-1орш',
    'Library point Molodechno': 'НОД-1млд',
    'Luninets Library Point': 'НОД-2лун',
    'Library point Volkovysk': 'НОД-2влк',
    'Library point of the Brest Locomotive Depot': 'НОД-3бр2',
    'Zhlobin Library Point': 'НОД-4жлб',
    'Kalinkovichi Library Point': 'НОД-4клн',
    'Osipovichi Library Point': 'НОД-5осп',
    'Polotsk Library Center': 'НОД-6плк'
}

def generate_username(user):
    reader = Reader.objects.filter(user=user).first()

    order_number = str(user.pk).zfill(5)

    if reader and reader.library:
        library_name = reader.library
        library_code = library_aliases.get(library_name, 'default')
    else:
        library_code = 'default'

    base_username = f'{order_number}{library_code}'

    username = base_username
    counter = 1
    while MyUser.objects.filter(username=username).exists():
        username = f'{base_username}_{counter}'
        counter += 1

    return username

def generate_username_with_initials(id, first_name, last_name, middle_name, library):
    order_number = str(id).zfill(5)
    library_code = library_aliases.get(library, 'default') if library else 'default'
    first_name_latin = transliterate.translit(first_name, reversed=True)
    last_name_latin = transliterate.translit(last_name, reversed=True)
    middle_name_latin = transliterate.translit(middle_name, reversed=True) if middle_name else ''

    initials = f"{last_name_latin[:1]}{first_name_latin[:1]}"
    if middle_name_latin:
        initials += middle_name_latin[:1]

    base_username = f"{initials}{library_code}"

    if len(base_username) > 25:
        base_username = base_username[:25]

    username = base_username
    counter = 1

    while MyUser.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        if len(username) > 25:
            username = username[:25]
        counter += 1

    return username


def generate_username_without_reader(id, library):
    order_number = str(id).zfill(5)

    if library:
        library_name = library
        library_code = library_aliases.get(library_name, 'default')
    else:
        library_code = 'default'

    base_username = f'{order_number}{library_code}'

    username = base_username
    counter = 1
    while MyUser.objects.filter(username=username).exists():
        username = f'{base_username}_{counter}'
        counter += 1

    return username


def parse_address(address):
    city, street, house, apartment = address.split(', ')
    return (city.split(' ', 1)[1], street.split(' ', 1)[1], house.split(' ', 1)[1], apartment.split(' ', 1)[1])


def get_education_key(value):
    for key, name in AbstractUser.EDUCATION_TYPE:
        if name == value:
            return key
    return None
