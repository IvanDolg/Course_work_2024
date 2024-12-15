from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from config.settings.base import *

class KUserConfig(AppConfig):
    name = 'kuser'
    verbose_name = _('User App')
    label = 'kuser'