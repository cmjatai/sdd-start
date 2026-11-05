from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _

from backend.model_mixins import (
    DateModelMixin,
)


class Teste(models.Model):

    teste = models.CharField(max_length=100, verbose_name=_("Teste"))

    class Meta:
        verbose_name = _("Teste")
        verbose_name_plural = _("Testes's")
        ordering = ("teste",)

    def __str__(self):
        return self.teste


class MetadataManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("content_type")

    def get_metadata(self, content_object):
        """
        Retorna o metadado do objeto passado
        """
        try:
            return self.get(
                content_type=ContentType.objects.get_for_model(content_object),
                object_id=content_object.pk,
            )
        except self.model.DoesNotExist:
            return None

    def set_or_update_metadata(self, content_object, metadata):
        """
        Cria ou atualiza o metadado do objeto passado
        """
        try:
            metadata_instance = self.get(
                content_type=ContentType.objects.get_for_model(content_object),
                object_id=content_object.pk,
            )
            if metadata_instance.metadata is None:
                metadata_instance.metadata = {}
            metadata_instance.metadata.update(metadata)
            metadata_instance.save()
        except self.model.DoesNotExist:
            metadata_instance = self.create(
                content_type=ContentType.objects.get_for_model(content_object),
                object_id=content_object.pk,
                metadata=metadata,
            )
        return metadata_instance


class Metadata(DateModelMixin, models.Model):
    objects = MetadataManager()
    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, default=None, on_delete=models.PROTECT
    )
    object_id = models.PositiveIntegerField(blank=True, null=True, default=None)
    content_object = GenericForeignKey("content_type", "object_id")

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=None,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        verbose_name = _("Metadado")
        verbose_name_plural = _("Metadados")
        unique_together = (("content_type", "object_id"),)
        ordering = ["id"]

    def __str__(self):
        return f"Metadata de {self.content_object}"
