from django.urls import path

from kfinder.views import chapter, periodical, non_periodical, extended_search_view, basic_search_view, topic_select, \
    boolean_search_view, new_releases_search

urlpatterns = [
    path('catalog/periodical/<str:id>', periodical, name='periodical'),
    path('catalog/non-periodical/<str:id>', non_periodical, name='non-periodical'),
    path('catalog/search/basic', basic_search_view, name='basic_search'),
    path('catalog/search/extended', extended_search_view, name='extended_search'),
    path('catalog/search/boolean', boolean_search_view, name='boolean_search'),
    path('catalog/search/new', new_releases_search, name='new_releases_search'),
    path('catalog/topic-select/', topic_select, name='topic_select'),
    path('catalog/chapter/', chapter, name='chapter'),
]
