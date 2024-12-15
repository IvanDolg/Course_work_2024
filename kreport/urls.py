from django.urls import path

from kreport.views import get_inventory_numbers, generate_summary_book_document

urlpatterns = [
    # Html url
    path('get_inventory_numbers/', get_inventory_numbers, name='get_inventory_numbers'),
    path('generate_summary_book/', generate_summary_book_document, name='generate_summary_book'),
]
