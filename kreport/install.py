from django.utils.translation import gettext_lazy as _

from config.settings.base import *

INSTALLED_APPS.append('kreport')
DATABASES['belrw-report-db'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': get_secret('REPORT_DB_HOST'),
        'PORT': get_secret('REPORT_DB_PORT'),
        'NAME': get_secret('REPORT_DB_NAME'),
        'USER': get_secret('REPORT_DB_USER'),
        'PASSWORD': get_secret('REPORT_DB_PASSWORD'),
}
DATABASE_APPS_MAPPING['kreport'] = 'belrw-report-db'

ADMIN_REORDER.append(
    {
        'app': 'kreport',
        'label': _('Report'),
        'models': ('kreport.InventoryBook',),
    }
)
