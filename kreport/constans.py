from django.utils.translation import gettext_lazy as _
from datetime import datetime

# InventoryBook constans
BOOKS = 'BOOKS'
BOOKS_NAME = _('Книги')
BROCHURES = 'BROCHURES'
BROCHURES_NAME = _('Брошюры')
NTD = 'NTD'
NTD_NAME = _('НТД')
INFORMATION_SHEETS = 'INFORMATION_SHEETS'
INFORMATION_SHEETS_NAME = _('Информационные листы')
CHANGES_AND_ADDITIONS_TO_THE_NTD = 'CHANGES_AND_ADDITIONS_TO_THE_NTD'
CHANGES_AND_ADDITIONS_TO_THE_NTD_NAME = _('Изменения и дополнения к НТД')
ELECTRONIC_RESOURCES = 'ELECTRONIC_RESOURCES'
ELECTRONIC_RESOURCES_NAME = _('Электронные ресурсы')

TEMPLATE_TYPE_CHOICES = [
    (BOOKS, BOOKS_NAME),
    (BROCHURES, BROCHURES_NAME),
    (NTD, NTD_NAME),
    (INFORMATION_SHEETS, INFORMATION_SHEETS_NAME),
    (CHANGES_AND_ADDITIONS_TO_THE_NTD, CHANGES_AND_ADDITIONS_TO_THE_NTD_NAME),
    (ELECTRONIC_RESOURCES, ELECTRONIC_RESOURCES_NAME),
]

# SummaryBook constans
FIRST_BOOK_TYPE = 'ADMISSION_TO_THE_FUND'
FIRST_BOOK_TYPE_NAME = _('Поступление в фонд')
SECOND_BOOK_TYPE = 'RETIREMENT_FROM_THE_FOUND'
SECOND_BOOK_TYPE_NAME = _('Выбытие из фонда')
THEAD_BOOK_TYPE = 'RESULTS_OF_THE_FOUND_MOVEMENT'
THEAD_BOOK_TYPE_NAME = _('Итоги движения фонда')

BOOK_TYPE_CHOICES = [
    (FIRST_BOOK_TYPE, FIRST_BOOK_TYPE_NAME),
    (SECOND_BOOK_TYPE, SECOND_BOOK_TYPE_NAME),
    (THEAD_BOOK_TYPE, THEAD_BOOK_TYPE_NAME),
]

LIBRARY_FIRST = 'Scientific and Technical Library'
LIBRARY_FIRST_NAME = 'Научно-техническая библиотека'
LIBRARY_SECOND = 'Technical Library of the Minsk Branch'
LIBRARY_SECOND_NAME = 'Техническая библиотека Минского отделения'
LIBRARY_THIRD = 'Technical Library of the Baranovichi branch'
LIBRARY_THIRD_NAME = 'Техническая библиотека Барановичского отделения'
LIBRARY_FOURTH = 'Technical Library of the Brest branch'
LIBRARY_FOURTH_NAME = 'Техническая библиотека Брестского отделения'
LIBRARY_FIFTH = 'Technical Library of the Gomel branch'
LIBRARY_FIFTH_NAME = 'Техническая библиотека Гомельского отделения'
LIBRARY_SIXTH = 'Technical Library of the Mogilev branch'
LIBRARY_SIXTH_NAME = 'Техническая библиотека Могилевского отделения'
LIBRARY_SEVENTH = 'Technical Library of the Vitebsk Branch'
LIBRARY_SEVENTH_NAME = 'Техническая библиотека Витебского отделения'
LIBRARY_EIGHTH = 'Orsha Library Point'
LIBRARY_EIGHTH_NAME = 'Библиотечный пункт Орша'
LIBRARY_NINTH = 'Library point Molodechno'
LIBRARY_NINTH_NAME = 'Библиотечный пункт Молодечно'
LIBRARY_TENTH = 'Luninets Library Point'
LIBRARY_TENTH_NAME = 'Библиотечный пункт Лунинец'
LIBRARY_ELEVENTH = 'Library point Volkovysk'
LIBRARY_ELEVENTH_NAME = 'Библиотечный пункт Волковыск'
LIBRARY_TWELFTH = 'Library point of the Brest Locomotive Depot'
LIBRARY_TWELFTH_NAME = 'Библиотечный пункт Локомотивного депо Брест'
LIBRARY_THIRTEEN = 'Zhlobin Library Point'
LIBRARY_THIRTEEN_NAME = 'Библиотечный пункт Жлобин'
LIBRARY_FOURTEENTH = 'Kalinkovichi Library Point'
LIBRARY_FOURTEENTH_NAME = 'Библиотечный пункт Калинковичи'
LIBRARY_FIFTEENTH = 'Osipovichi Library Point'
LIBRARY_FIFTEENTH_NAME = 'Библиотечный пункт Осиповичи'
LIBRARY_SIXTEENTH = 'Polotsk Library Center'
LIBRARY_SIXTEENTH_NAME = 'Библиотечный пункт Полоцк'

LIBRARY_TYPE = (
    (LIBRARY_FIRST, LIBRARY_FIRST_NAME),
    (LIBRARY_SECOND, LIBRARY_SECOND_NAME),
    (LIBRARY_THIRD, LIBRARY_THIRD_NAME),
    (LIBRARY_FOURTH, LIBRARY_FOURTH_NAME),
    (LIBRARY_FIFTH, LIBRARY_FIFTH_NAME),
    (LIBRARY_SIXTH, LIBRARY_SIXTH_NAME),
    (LIBRARY_SEVENTH, LIBRARY_SEVENTH_NAME),
    (LIBRARY_EIGHTH, LIBRARY_EIGHTH_NAME),
    (LIBRARY_NINTH, LIBRARY_NINTH_NAME),
    (LIBRARY_TENTH, LIBRARY_TENTH_NAME),
    (LIBRARY_ELEVENTH, LIBRARY_ELEVENTH_NAME),
    (LIBRARY_TWELFTH, LIBRARY_TWELFTH_NAME),
    (LIBRARY_THIRTEEN, LIBRARY_THIRTEEN_NAME),
    (LIBRARY_FOURTEENTH, LIBRARY_FOURTEENTH_NAME),
    (LIBRARY_FIFTEENTH, LIBRARY_FIFTEENTH_NAME),
    (LIBRARY_SIXTEENTH, LIBRARY_SIXTEENTH_NAME)
)

JANUARY = '01'
JANUARY_NAME = _('Январь')
FEBRUARY = '02'
FEBRUARY_NAME = _('Февраль')
MARCH = '03'
MARCH_NAME = _('Март')
APRIL = '04'
APRIL_NAME = _('Апрель')
MAY = '05'
MAY_NAME = _('Май')
JUNE = '06'
JUNE_NAME = _('Июнь')
JULY = '07'
JULY_NAME = _('Июль')
AUGUST = '08'
AUGUST_NAME = _('Август')
SEPTEMBER = '09'
SEPTEMBER_NAME = _('Сентябрь')
OCTOBER = '10'
OCTOBER_NAME = _('Октябрь')
NOVEMBER = '11'
NOVEMBER_NAME = _('Ноябрь')
DECEMBER = '12'
DECEMBER_NAME = _('Декабрь')
ALL_YEAR = 'ALL_YEAR'
ALL_YEAR_NAME = _('Весь год')

MONTH_CHOICES = [
    (JANUARY, JANUARY_NAME),
    (FEBRUARY, FEBRUARY_NAME),
    (MARCH, MARCH_NAME),
    (APRIL, APRIL_NAME),
    (MAY, MAY_NAME),
    (JUNE, JUNE_NAME),
    (JULY, JULY_NAME),
    (AUGUST, AUGUST_NAME),
    (SEPTEMBER, SEPTEMBER_NAME),
    (OCTOBER, OCTOBER_NAME),
    (NOVEMBER, NOVEMBER_NAME),
    (DECEMBER, DECEMBER_NAME),
    (ALL_YEAR, ALL_YEAR_NAME),
]
CURRENT_YEAR = datetime.now().year

# YEAR_CHOICES с целыми числами
YEAR_CHOICES_N = [(year, str(year)) for year in range(2005, CURRENT_YEAR + 1)]

# MONTH_CHOICES с целыми числами
MONTH_CHOICES_N = [
    (1, JANUARY_NAME),
    (2, FEBRUARY_NAME),
    (3, MARCH_NAME),
    (4, APRIL_NAME),
    (5, MAY_NAME),
    (6, JUNE_NAME),
    (7, JULY_NAME),
    (8, AUGUST_NAME),
    (9, SEPTEMBER_NAME),
    (10, OCTOBER_NAME),
    (11, NOVEMBER_NAME),
    (12, DECEMBER_NAME),
]

YEAR_CHOICES = [(str(year), str(year)) for year in range(2005, CURRENT_YEAR + 1)]

REPORT_TYPE_CHOICES = [
    ('Registered', 'Количество зарегистрированных читателей'),
    ('Reregistred', 'Количество перерегистрированных читателей'),
]

DEBT_REPORT_TYPE_CHOICES = [
    ('Date', 'По дате'),
    ('User', 'По пользователю'),
]

CIRC_REPORT_TYPE_CHOICES = [
    ('Date', 'Год'),
    ('User', 'Отдельный пользователь'),
]


FIRST_REPORT_TYPE = 'ISSUED_LITERATURE'
FIRST_REPORT_TYPE_NAME = _('Выдано')
SECOND_REPORT_TYPE = 'RETURNED_LITERATURE'
SECOND_REPORT_TYPE_NAME = _('Возвращено')

REPORT_CHOICES = [
    (FIRST_REPORT_TYPE, FIRST_REPORT_TYPE_NAME),
    (SECOND_REPORT_TYPE, SECOND_REPORT_TYPE_NAME),
]