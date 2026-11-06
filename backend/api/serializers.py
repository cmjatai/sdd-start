from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls.base import reverse
from drf_spectacular.utils import extend_schema_field
from image_cropping.utils import get_backend
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from backend.utils.models import Metadata


class BackendSerializerMixin(serializers.ModelSerializer):
    __str__ = SerializerMethodField()
    metadata = SerializerMethodField()
    link_detail_backend = SerializerMethodField()

    class Meta:
        fields = '__all__'

    def get_link_detail_backend(self, obj) -> str:
        try:
            return reverse(
                f'{self.Meta.model._meta.app_config.name}:{self.Meta.model._meta.model_name}_detail',
                kwargs={'pk': obj.pk},
            )
        except:
            return ''

    def get___str__(self, obj) -> str:
        return str(obj)

    def get_metadata(self, obj) -> dict:
        try:
            if obj._meta.model == 'Metadata':
                return obj.metadata

            metadata = Metadata.objects.get(
                content_type=ContentType.objects.get_for_model(obj._meta.model),
                object_id=obj.id,
            ).metadata
        except:
            metadata = {}
        return metadata
