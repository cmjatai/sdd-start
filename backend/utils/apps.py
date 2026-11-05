from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.utils"
    label = "utils"

    def ready(self):
        AppConfig.ready(self)

        from .services import signals
