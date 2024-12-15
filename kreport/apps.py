from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KReportConfig(AppConfig):
    name = 'kreport'
    verbose_name = _('Report')
    label = 'kreport'