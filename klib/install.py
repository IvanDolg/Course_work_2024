from django.utils.translation import gettext_lazy as _

from config.settings.base import *

INSTALLED_APPS.append('klib')
DATABASES['belrw-lib-db'] = {
    'ENGINE': 'django.db.backends.postgresql',
    'HOST': get_secret('LIB_DB_HOST'),
    'PORT': get_secret('LIB_DB_PORT'),
    'NAME': get_secret('LIB_DB_NAME'),
    'USER': get_secret('LIB_DB_USER'),
    'PASSWORD': get_secret('LIB_DB_PASSWORD'),
}
DATABASE_APPS_MAPPING['klib'] = 'belrw-lib-db'

ADMIN_REORDER.append(
    {
        'app': 'klib',
        'label': _('Lib'),
        'models': (
            'klib.Company',
            'klib.BaseEdition',
            'klib.BaseOrder',
            'klib.BasePeriodicalOrder',
            'klib.BaseArrival',
            'klib.BaseFundElement',
            'klib.PublicationWriteOff',
            'klib.DigitalResource'
        ),
    }
)

