import inspect

from django.apps import AppConfig
from django.conf import settings


class EAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.eauth'
    label = 'eauth'

    def ready(self):
        AppConfig.ready(self)
        from .services import signals
