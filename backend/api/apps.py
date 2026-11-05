import inspect

from django.apps import AppConfig
from django.conf import settings


class ApiConfig(AppConfig):
    name = 'backend.api'
    label = 'api'
