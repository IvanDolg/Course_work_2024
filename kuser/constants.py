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

EDUCATION_STATUS_SECONDARY = 'general-average'
EDUCATION_STATUS_SECONDARY_NAME = 'Общее среднее'
EDUCATION_STATUS_SECONDARY_SPECIAL = 'secondary_special'
EDUCATION_STATUS_SECONDARY_SPECIAL_NAME = 'Средне-специальное'
EDUCATION_STATUS_INCOMPLETE_HIGHER = 'higher'
EDUCATION_STATUS_INCOMPLETE_HIGHER_NAME = 'Высшее'
EDUCATION_STATUS_HIGHER = 'vocational-training'
EDUCATION_STATUS_HIGHER_NAME = 'Профессионально-техническое'

EDUCATION_TYPE = (
    (EDUCATION_STATUS_SECONDARY, EDUCATION_STATUS_SECONDARY_NAME),
    (EDUCATION_STATUS_SECONDARY_SPECIAL, EDUCATION_STATUS_SECONDARY_SPECIAL_NAME),
    (EDUCATION_STATUS_INCOMPLETE_HIGHER, EDUCATION_STATUS_INCOMPLETE_HIGHER_NAME),
    (EDUCATION_STATUS_HIGHER, EDUCATION_STATUS_HIGHER_NAME)
)

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

STATUS_ACTIVE = 'ACTIVE'
STATUS_ACTIVE_NAME = 'действующий'
STATUS_STOPPED = 'STOPPED'
STATUS_STOPPED_NAME = 'приостановлено действие'
STATUS_DEPRIVED = 'DEPRIVED'
STATUS_DEPRIVED_NAME = 'лишен пожизненно'

STATUS = [
    (STATUS_ACTIVE, STATUS_ACTIVE_NAME),
    (STATUS_STOPPED, STATUS_STOPPED_NAME),
    (STATUS_DEPRIVED, STATUS_ACTIVE_NAME)
]

WORK_STATUS_ACTIVE = 'ACTIVE'
WORK_STATUS_ACTIVE_NAME = 'Работает на БелЖД'
WORK_STATUS_DISMISSED = 'DISMISSED'
WORK_STATUS_DISMISSED_NAME = 'Уволен с БелЖД'
WORK_STATUS_ANOTHER = 'ANOTHER'
WORK_STATUS_ANOTHER_NAME = 'Другое'

WORK_TYPE = (
    (WORK_STATUS_ACTIVE, WORK_STATUS_ACTIVE_NAME),
    (WORK_STATUS_DISMISSED, WORK_STATUS_DISMISSED_NAME),
    (WORK_STATUS_ANOTHER, WORK_STATUS_ANOTHER_NAME)
)

STATUS_READER_ONE = 'Исключен'
STATUS_READER_TWO = 'Активен'
READER_STATUSES = (
    (STATUS_READER_ONE.lower(), STATUS_READER_ONE),
    (STATUS_READER_TWO.lower(), STATUS_READER_TWO),
)

ROLE_STATUS_FIRST = 'system_administrator'
ROLE_STATUS_FIRST_NAME = 'Системный администратор'
ROLE_STATUS_SECOND = 'chief_information_administrator'
ROLE_STATUS_SECOND_NAME = 'Главный информационный администратор'
ROLE_STATUS_THIRD = 'information_administrator'
ROLE_STATUS_THIRD_NAME = 'Информационный администратор'
ROLE_STATUS_FOURTH = 'employees_of_tb_bjd'
ROLE_STATUS_FOURTH_NAME = 'Работники ТБ БЖД'

ROLE_TYPE = (
    (ROLE_STATUS_FIRST, ROLE_STATUS_FIRST_NAME),
    (ROLE_STATUS_SECOND, ROLE_STATUS_SECOND_NAME),
    (ROLE_STATUS_THIRD, ROLE_STATUS_THIRD_NAME),
    (ROLE_STATUS_FOURTH, ROLE_STATUS_FOURTH_NAME)
)

WORKER_STATUS_WORKS = 'WORKS'
WORKER_STATUS_WORKS_NAME = 'Работает'
WORKER_STATUS_DISMISSED = 'DISMISSED'
WORKER_STATUS_DISMISSED_NAME = 'Уволен'

STATUS = (
    (WORKER_STATUS_WORKS, WORKER_STATUS_WORKS_NAME),
    (WORKER_STATUS_DISMISSED, WORKER_STATUS_DISMISSED_NAME),
)
