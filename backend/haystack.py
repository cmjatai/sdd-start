import logging

from celery_haystack.signals import CelerySignalProcessor
from django.conf import settings
from django.db.models.base import Model
from haystack.constants import DEFAULT_ALIAS
from haystack.routers import DefaultRouter

logger = logging.getLogger(__name__)

DEFAULT_ALIAS = settings.SOLR_COLLECTIONS.split(",")[0]
BACKENDARQ_ALIAS = settings.SOLR_COLLECTIONS.split(",")[1]

if not BACKENDARQ_ALIAS or not DEFAULT_ALIAS or BACKENDARQ_ALIAS == DEFAULT_ALIAS:
    raise ValueError(
        "SOLR_COLLECTIONS must contain at least two distinct collections separated by a comma and defined in settings.SOLR_COLLECTIONS."
    )

MODELS_SOLR_DEFAULT = ()

MODELS_SOLR_BACKENDARQ = ()


class CelerySignalProcessor(CelerySignalProcessor):
    def enqueue_save(self, sender, instance, **kwargs):
        if sender not in (MODELS_SOLR_BACKENDARQ + MODELS_SOLR_DEFAULT):
            return

        action = "update"

        return self.enqueue(action, instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue("delete", instance, sender, **kwargs)


class DefaultRouter(DefaultRouter):
    def for_write(self, **hints):
        return self.for_rw(**hints)

    def for_read(self, **hints):
        return self.for_rw(**hints)

    def for_rw(self, **hints):
        # logger.debug(hints)
        if not hints:
            return DEFAULT_ALIAS

        if "instance" in hints:
            m = hints["instance"]._meta.model
            if m in MODELS_SOLR_BACKENDARQ:
                return BACKENDARQ_ALIAS
            elif m not in MODELS_SOLR_DEFAULT:
                return None
        elif "index" in hints:
            m = hints["index"].model
            if m in MODELS_SOLR_BACKENDARQ:
                return BACKENDARQ_ALIAS
            elif m not in MODELS_SOLR_DEFAULT:
                return None
        elif "models" in hints:
            m = hints["models"]
            if m and not isinstance(m, Model):
                m = m[0]
            if m in MODELS_SOLR_BACKENDARQ:
                return BACKENDARQ_ALIAS
            elif m not in MODELS_SOLR_DEFAULT:
                return None
        return DEFAULT_ALIAS
