import logging

from datetime import datetime

logger = logging.getLogger(__name__)

def convert_year(elements):
    for element in elements:
        if element['type'] == 'NON_PERIODICAL':
            element['year'] = element['date_of_publication'][:4]
    return elements


def convert_query_params(query):
    result = '&'.join(f'field_{key}={value}' for key, value in query.items() if value)
    return result

def years():
    current_year = datetime.now().year
    years = list(reversed(range(2005, current_year + 1)))
    return years

def months():
    return ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']