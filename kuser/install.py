from django.utils.translation import gettext_lazy as _

from config.settings.base import *

INSTALLED_APPS.append('kuser')
DATABASES['belrw-user-db'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': get_secret('USER_DB_HOST'),
        'PORT': get_secret('USER_DB_PORT'),
        'NAME': get_secret('USER_DB_NAME'),
        'USER': get_secret('USER_DB_USER'),
        'PASSWORD': get_secret('USER_DB_PASSWORD'),
}
# DATABASE_APPS_MAPPING['kuser'] = 'belrw-user-db'


ADMIN_REORDER.append(
    {
        'app': 'kuser',
        'label': _('Account Users'),
        'models': (
            'kuser.LibraryCard',
            'kuser.Reader',
            'kuser.Worker',
        )
    })

ADMIN_REORDER.append(
    {
        'app': 'kuser',
        'label': _('User App'),
        'models': (
            'kuser.Department',
            'kuser.Organization',
            'kuser.Position',
            'kuser.MyUser',
        )
    })