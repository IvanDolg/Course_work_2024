import logging

from django.http import JsonResponse
from .models import BaseEdition

logger = logging.getLogger('main')


def get_edition_subtype(request, editionId):
    if editionId:
        try:
            edition = BaseEdition.objects.get(id=editionId)
            return JsonResponse({'subtype': edition.get_edition_subtype_display()})
        except BaseEdition.DoesNotExist:
            return JsonResponse({'error': 'Издание не найдено'}, status=404)
    return JsonResponse({'error': 'ID издания не указан'}, status=400)

def filter_editions(request):
    edition_subtype = request.GET.get('edition_subtype')
    if edition_subtype:
        editions = BaseEdition.objects.filter(edition_subtype=edition_subtype).values('id', 'title')
        return JsonResponse(list(editions), safe=False)
    return JsonResponse([], safe=False)