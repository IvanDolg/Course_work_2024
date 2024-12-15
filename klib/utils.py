import logging

from requests import request

from kcatalog.models import Sku
from klib.models import Edition, PeriodicalEdition
from kuser.models import Reader, Worker

logger = logging.getLogger(__name__)

def dict_to_periodic(element_dict: dict):
    elem = PeriodicalEdition()
    elem.id = element_dict['id']
    elem.edition_type = element_dict['type']
    elem.edition_subtype = element_dict['subtype']
    elem.title = element_dict['title']
    elem.note = element_dict['note']
    elem.year = element_dict['year']
    return elem


def is_exist_with_number(sku: Sku, number):
    if sku.edition().edition_type == Edition.TYPE_NON_PERIODICAL:
        logger.debug(False)
        return False
    is_exist = Sku.objects.filter(title_and_statement_of_responsibility__volume_designation=number).exists()
    return is_exist

def get_user_library(user):
    result = Reader.objects.filter(user=user).first()
    if result is None:
        result = Worker.objects.filter(user=user).first()
    return getattr(result, 'library', None)
