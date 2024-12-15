import logging
from datetime import date, timedelta

from klib.models import BaseFundElement, BaseEdition
from kreport.constans import FIRST_BOOK_TYPE, SECOND_BOOK_TYPE

logger = logging.getLogger('main')

# На начало: кол-во зарегестрированных изданий (статус в фонде), которые есть в фонде (в зависимости от наименования в таблицы(фильтр)) на момент 1 числа (т.е. с начало до конца прошлого месяца)
# На конец: кол-во зарегестрированных изданий (статус в фонде), которые есть в фонде (в зависимости от наименования в таблицы(фильтр)) на момент 30/31/28/29 числа (т.е.на конец текущего месяца + поступления)
# Поступило: кол-во зарегестрированных изданий (т.е ко-во зарегестрированных элементов в фонде в текущем месяце)


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


# Всего документов
def calculate_doc_start_total_document(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    if month == 'ALL_YEAR':
        query = query.filter(
            registration_date__gte=date(year, 1, 1),
            registration_date__lte=date(year, 12, 31)
        )

    return query.count()


def calculate_doc_received_total_document(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_document(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# Принятых на баланс
def calculate_doc_start_accepted_to_balance(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    # Фильтрация в зависимости от типа книги
    if book_type == FIRST_BOOK_TYPE:
        balance_type_filter = 'стоит на балансе'
    elif book_type == SECOND_BOOK_TYPE:
        balance_type_filter = 'не стоит на балансе'  # Пример для другого статуса
    else:
        balance_type_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        library=library
    )

    if balance_type_filter:
        query = query.filter(balance_type=balance_type_filter)

    return query.count()


def calculate_doc_received_accepted_to_balance(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        balance_type_filter = 'стоит на балансе'
    elif book_type == SECOND_BOOK_TYPE:
        balance_type_filter = 'не стоит на балансе'
    else:
        balance_type_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        library=library
    )

    if balance_type_filter:
        query = query.filter(balance_type=balance_type_filter)

    return query.count()


def calculate_doc_end_accepted_to_balance(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        balance_type_filter = 'стоит на балансе'
    elif book_type == SECOND_BOOK_TYPE:
        balance_type_filter = 'не стоит на балансе'
    else:
        balance_type_filter = None

    query_existing = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        library=library
    )

    if balance_type_filter:
        query_existing = query_existing.filter(balance_type=balance_type_filter)
        query_received = query_received.filter(balance_type=balance_type_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# Книги
def calculate_doc_start_books(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_BOOK,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_received_books(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_BOOK,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_books(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_BOOK,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_BOOK,
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# Электронные ресурсы
def calculate_doc_start_electronic_resources(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_E_RESOURCE,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_received_electronic_resources(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_E_RESOURCE,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_electronic_resources(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_E_RESOURCE,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_E_RESOURCE,
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# Брошюры
def calculate_doc_start_brochures(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_BROCHURE,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_received_brochures(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_BROCHURE,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_brochures(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_BROCHURE,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_BROCHURE,
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# Информационные листки
def calculate_doc_start_information_sheets(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_INFORMATION_FLYER,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_received_information_sheets(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_INFORMATION_FLYER,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_information_sheets(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_INFORMATION_FLYER,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_INFORMATION_FLYER,
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# НТД
def calculate_doc_start_ntd(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_received_ntd(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_ntd(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# Журналы
def calculate_doc_start_magazines(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_MAGAZINE,
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_received_magazines(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_MAGAZINE,
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_magazines(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_MAGAZINE,
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_MAGAZINE,
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count


# Газеты
def calculate_doc_start_newspapers(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_NEWSPAPER,
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_received_newspapers(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_NEWSPAPER,
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query = query.filter(publication_status=publication_status_filter)

    return query.count()


def calculate_doc_end_newspapers(year, month, library, book_type):
    first_day, last_day = get_month_date_range(year, month)

    if book_type == FIRST_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF
    elif book_type == SECOND_BOOK_TYPE:
        publication_status_filter = BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF
    else:
        publication_status_filter = None

    query_existing = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_NEWSPAPER,
        registration_date__lte=first_day,
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    query_received = BaseFundElement.objects.filter(
        publication_status=BaseFundElement.SUBTYPE_NEWSPAPER,
        registration_date__range=(first_day, last_day),
        edition__edition_subtype=BaseEdition.SUBTYPE_STD,
        library=library
    )

    if publication_status_filter:
        query_existing = query_existing.filter(publication_status=publication_status_filter)
        query_received = query_received.filter(publication_status=publication_status_filter)

    existing_count = query_existing.count()
    received_count = query_received.count()

    return existing_count + received_count