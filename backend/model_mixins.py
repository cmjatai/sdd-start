from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.deletion import PROTECT
from django.utils.translation import gettext_lazy as _

from backend.utilss import get_settings_auth_user_model, normalize


class DateModelMixin(models.Model):
    created_at = models.DateTimeField(
        verbose_name=_("Criado em"), editable=False, auto_now_add=True
    )

    modified_at = models.DateTimeField(
        verbose_name=_("Modificado em"), editable=False, auto_now=True
    )

    class Meta:
        abstract = True


class AuditoriaModelMixin(models.Model):
    created_by = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_("Criado Por"),
        related_name="+",
        on_delete=PROTECT,
    )

    modified_by = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_("Modificado Por"),
        related_name="+",
        on_delete=PROTECT,
    )

    class Meta:
        abstract = True


class SearchModelMixin(models.Model):
    """
    Mixin para adicionar um campo de busca em modelos.
    """

    fields_search = []

    search = models.TextField(blank=True, default="")

    class Meta:
        abstract = True

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
        auto_update_search=True,
    ):
        if auto_update_search and hasattr(self, "fields_search"):
            search = ""
            for str_field in self.fields_search:
                if isinstance(str_field, tuple):
                    for field in str_field:
                        try:
                            search += str(getattr(self, field))
                        except Exception as e:
                            pass
                    search += " "
                else:
                    fields = str_field.split("__")
                    if len(fields) == 1:
                        try:
                            search += str(getattr(self, str_field)) + " "
                        except Exception as e:
                            pass
                    else:
                        _self = self
                        for field in fields:
                            _self = getattr(_self, field)
                        search += str(_self) + " "
            self.search = search.strip()
        self.search = normalize(self.search)

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class CleanModelMixin:
    def clean(self):
        super().clean()

        for field_tuple in self._meta.unique_together[:]:
            unique_filter = {}
            unique_fields = []
            null_found = False
            for field_name in field_tuple:
                field_value = getattr(self, field_name)
                if getattr(self, field_name) is None:
                    unique_filter["%s__isnull" % field_name] = True
                    null_found = True
                else:
                    unique_filter["%s" % field_name] = field_value
                    unique_fields.append(field_name)
            if null_found:
                unique_queryset = self.__class__.objects.filter(**unique_filter)
                if self.pk:
                    unique_queryset = unique_queryset.exclude(pk=self.pk)
                if unique_queryset.exists():
                    msg = self.unique_error_message(
                        self.__class__, tuple(unique_fields)
                    )
                    raise ValidationError(msg)

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
        clean=True,
    ):
        if clean:
            self.clean()

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class SaveModelWithFileMixin:
    FIELDFILE_NAME = ("arquivo",)

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
        clean=True,
    ):
        if not self.pk:
            files = {field: getattr(self, field) for field in self.FIELDFILE_NAME}
            for field in self.FIELDFILE_NAME:
                setattr(self, field, None)
            super().save(force_insert, force_update, using, update_fields)
            for field, file in files.items():
                if file:
                    setattr(self, field, file)

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
