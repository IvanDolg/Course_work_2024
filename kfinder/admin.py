from django.contrib import admin

from kfinder.models import Order
from kuser.admin import my_admin_site


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['service_type', 'edition_name', 'count']
    list_filter = ['service_type', 'edition_name', 'count']
    search_fields = ['service_type', 'edition_name']
    fieldsets = (
        ('Описание заказа',
         {
             'fields': (
                 'service_type',
             )
         }),
        ('Список изданий',{
            'fields': (
                'edition_name', 'count',
            )
        }),
    )

my_admin_site.register(Order, OrderAdmin)
