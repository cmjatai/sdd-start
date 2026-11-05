import decimal
import hashlib
import logging
import os
import re
from collections import defaultdict
from unicodedata import normalize as unicodedata_normalize

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.core.files.uploadedfile import UploadedFile
from django.db import connection
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_init,
    post_migrate,
    post_save,
    pre_delete,
    pre_init,
    pre_migrate,
    pre_save,
)
from django.forms import BaseForm, ValidationError
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails import source_generators

logger = logging.getLogger(__name__)

YES_NO_CHOICES = [(True, _("Sim")), (False, _("Não"))]

NONE_YES_NO_CHOICES = [(None, _("---------")), (True, _("Sim")), (False, _("Não"))]

DECIMAL_PLACES = {i: (decimal.Decimal(10) ** -i) for i in range(0, 10)}


def quantize(
    value, decimal_places=2, rounding=decimal.ROUND_HALF_DOWN
) -> decimal.Decimal:
    return value.quantize(
        (
            DECIMAL_PLACES[decimal_places]
            if isinstance(decimal_places, int)
            else decimal_places
        ),
        rounding=rounding,
    )


def decimal2str(
    value,
    decimal_places=2,
    rounding=decimal.ROUND_HALF_DOWN,
    force_grouping=True,
    use_l10n=True,
) -> str:
    try:
        value = quantize(
            value, decimal_places=DECIMAL_PLACES[decimal_places], rounding=rounding
        )

        return formats.number_format(
            value,
            decimal_pos=decimal_places,
            use_l10n=use_l10n,
            force_grouping=force_grouping,
        )
    except Exception as e:
        # Log the error
        logger.error(
            f"Erro ao formatar o valor {value} com {decimal_places} casas decimais. "
            f"Valor deve ser um Decimal ou um número válido. Erro: {str(e)}"
        )
        return str(value)


def normalize(txt):
    return unicodedata_normalize("NFKD", txt).encode("ASCII", "ignore").decode("ASCII")


def dict2attr(value):
    class d2a(dict):
        def __init__(self):
            for k, v in value.items():
                setattr(self, k, v)

    class_d2a = d2a()
    class_d2a.update(value)
    return class_d2a


def get_settings_auth_user_model():
    return getattr(settings, "AUTH_USER_MODEL", "auth.User")


def register_all_models_in_admin(module_name):
    appname = module_name.split(".")
    appname = appname[1] if appname[0] == "backend" else appname[0]
    app = apps.get_app_config(appname)

    for model in app.get_models():
        if not admin.site.is_registered(model):
            admin.site.register(model)


def save_in_metadata(obj, mdict=None):
    from django.contrib.contenttypes.models import ContentType

    from backend.utils.models import Metadata

    md = Metadata.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(obj._meta.model),
        object_id=obj.id,
    )[0]

    md.metadata = mdict
    md.save()
    return md


def run_sql(sql):
    result = []
    with connection.cursor() as cursor:
        result = cursor.execute(sql)
        try:
            result = cursor.fetchall()
        except Exception as e:
            pass
    return result


def show_results_filter_set(qr):
    query_params = set(qr.keys())
    if (len(query_params) == 1 and "iframe" in query_params) or len(query_params) == 0:
        return False

    return True


def pil_image(source, exif_orientation=False, **options):
    return source_generators.pil_image(source, exif_orientation, **options)


def clean_text(text, _normalizes=None):
    txt = text
    try:
        normalizes = _normalizes or (
            (r"\n ?\d+ ?/ ?\d+ ?\n", "\n"),
            (r"[ ]{2,}", " "),
            (r" \n", "\n"),
            # ('([^\.]|\S)\n(\S)', r'\1 \2'),
            (r"(\w)\n(.)", r"\1 \2"),
            (r"(,|\.)\n(.)", r"\1 \2"),
            # ('()\n()', r'\1 \2'),
            (r"\n\n", "\n"),
            (r"-\n", "-"),
            (r"^\n", ""),
            ("–", "-"),
            ("•", "*"),
            ("[“”]", '"'),
            # ('', ''),
            # ('', ''),
            # ('', ''),
            # ('', ''),
            # ('', ''),
        )

        for regex, new in normalizes:
            search = re.search(regex, text)
            while search:
                text = re.sub(regex, new, text)
                search = re.search(regex, text)
        return text
    except:
        return txt


def get_mime_type_from_file_extension(filename):
    ext = filename.split(".")[-1]
    if ext == "odt":
        mime = "application/vnd.oasis.opendocument.text"
    else:
        mime = "application/%s" % (ext,)
    return mime


def intervalos_tem_intersecao(a_inicio, a_fim, b_inicio, b_fim):
    maior_inicio = max(a_inicio, b_inicio)
    menor_fim = min(a_fim, b_fim)
    return maior_inicio <= menor_fim


def hash_sha512(arquivo):
    f = open(arquivo, "rb") if isinstance(arquivo, str) else arquivo

    sha512_hash = hashlib.sha512()
    # Read and update hash string value in blocks of 4K
    for byte_block in iter(lambda: f.read(4096), b""):
        sha512_hash.update(byte_block)

    if isinstance(arquivo, str):
        f.close()

    return sha512_hash.hexdigest()


class DisableSignals(object):
    def __init__(self, disabled_signals=None):
        self.stashed_signals = defaultdict(list)
        self.disabled_signals = disabled_signals or [
            pre_init,
            post_init,
            pre_save,
            post_save,
            pre_delete,
            post_delete,
            pre_migrate,
            post_migrate,
            m2m_changed,
        ]

    def __enter__(self):
        for signal in self.disabled_signals:
            self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        keys = list(self.stashed_signals.keys())
        for signal in keys:
            self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]
        signal.sender_receivers_cache.clear()


class TimeExecution(object):
    def __init__(self, print_date=False):
        self.print_date = print_date

    def __enter__(self):
        self.start = timezone.localtime()
        if self.print_date:
            print(self.start)

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = timezone.localtime()
        if self.print_date:
            print(end)
        print("TimeExecution:", end - self.start)


class FileFieldCheckMixin(BaseForm):

    def _check(self):
        cleaned_data = super(FileFieldCheckMixin, self).clean()
        errors = []
        for name, campo in self.fields.items():
            if isinstance(campo, forms.fields.FileField):
                error = self.errors.get(name)
                if error:
                    msgs = [
                        e.replace(
                            "Certifique-se de que o arquivo",
                            "Certifique-se de que o nome do "
                            "arquivo no campo '{}'".format(campo.label),
                        )
                        for e in error
                    ]
                    for msg in msgs:
                        errors.append(msg)

                arquivo = self.cleaned_data.get(name)
                if arquivo and not isinstance(arquivo, UploadedFile):
                    if not os.path.exists(arquivo.path):
                        errors.append(
                            "Arquivo referenciado no campo "
                            " '%s' inexistente! Marque a "
                            "opção Limpar e Salve." % campo.label
                        )
        if errors:
            raise ValidationError(errors)
        return cleaned_data

    def clean(self):
        """Alias for _check()"""
        return self._check()
