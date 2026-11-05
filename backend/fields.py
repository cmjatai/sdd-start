import os

from django.conf import settings
from django.db import models
from django.db.models.fields.files import FieldFile
from django.urls import reverse


class CustomFieldFile(FieldFile):
    @property
    def _url(self):
        try:
            self._require_file()
            # if settings.DEBUG:
            #    return self.storage.url(self.name)

            field_name_action = self.field.name.replace("_", "-")
            url = "%s" % reverse(
                "backend.api:%s_%s-%s"
                % (
                    self.instance._meta.app_label,
                    self.instance._meta.model_name,
                    field_name_action,
                ),
                kwargs={"pk": self.instance.pk},
            )
            return url
        except:
            return ""

    @property
    def url(self):
        try:
            url = self._url
            ext = self.name.split(".")[-1]
            if url and url[-1] == "/":
                url = url[:-1]
                url = f"{url}.{ext}"
            return url
        except:
            return ""

    def shorten_file_name(self):
        name = self.name

        if not name:
            return

        nl = name.split("/")

        if len(nl[-1]) < 128:
            return

        name = nl[-1][-20:]

        name = f"f_{name}"

        nl[-1] = name
        new_path = f'{settings.MEDIA_ROOT}/{"/".join(nl)}'

        os.rename(self.path, new_path)

        self.name = "/".join(nl)
        self.instance.save()

    def delete(self, save=True):
        if not self:
            return

        if hasattr(self, "_file"):
            self.close()
            del self.file

        self.storage.delete(self.name)

        self.name = None
        setattr(self.instance, self.field.name, self.name)
        self._committed = False

        if save:
            self.instance.save()


class CustomFileField(models.FileField):
    attr_class = CustomFieldFile
