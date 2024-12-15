from django.urls import path
from django.urls import include

from klib.views import get_edition_subtype, filter_editions

urlpatterns = [
    path('get-edition-subtype-non-periodical-order/<int:editionId>/', get_edition_subtype, name='get_edition_subtype_non_periodical_order'),
    path('api/filter-editions/', filter_editions, name='filter_editions'),
]
