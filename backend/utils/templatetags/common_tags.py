import json
import logging
import re
from copy import deepcopy
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template.defaultfilters import stringfilter
from django.utils import formats, timezone
from django.utils.dateparse import parse_datetime as django_parse_datetime
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from num2words import num2words

from backend.utilss import decimal2str

logger = logging.getLogger(__name__)


register = template.Library()


@register.filter("decimal2str")
def decimal2str_filter(value):
    return decimal2str(value)


@register.filter("startswith")
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter("jsonify")
def jsonify(object):
    if isinstance(object, QuerySet):
        return mark_safe(serialize("json", object))
    return mark_safe(json.dumps(object))


@register.filter("to_dict")
def to_dict(object):
    return object.__dict__


@register.filter("islist")
def islist(object):
    return isinstance(object, list)


def get_class(class_string):
    if not hasattr(class_string, "__bases__"):
        class_string = str(class_string)
        dot = class_string.rindex(".")
        mod_name, class_name = class_string[:dot], class_string[dot + 1 :]

        try:
            ct = ContentType.objects.get_by_natural_key(mod_name, class_name.lower())
            if ct:
                return ct.model_class()
            return None
        except:
            if class_name:
                return getattr(__import__(mod_name, {}, {}, [str("")]), class_name)
            return None


@register.simple_tag
def field_verbose_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name


@register.simple_tag
def fieldclass_verbose_name(class_name, field_name):
    cls = get_class(class_name)
    return cls._meta.get_field(field_name).verbose_name


@register.simple_tag
def model_verbose_name(class_name):
    model = get_class(class_name)
    return model._meta.verbose_name


@register.simple_tag
def model_verbose_name_plural(class_name):
    model = get_class(class_name)
    if model:
        return model._meta.verbose_name_plural
    return ""


@register.filter
def meta_model_value(instance, attr):
    try:
        return getattr(instance._meta, attr) if instance else ""
    except:
        return ""


@register.filter
def lookup(d, key):
    return d[key] if key in d else []


@register.filter
def map_field_from_queryset(qs, field):
    return map(lambda obj: getattr(obj, field), qs)


@register.filter
def search_value(request):
    try:
        q = getattr(request, request.method).get("q", "")
        return q
    except Exception as e:
        logger.error(e)

    return ""


@register.filter
def isinst(value, class_str):
    classe = value.__class__.__name__
    return classe == class_str


@register.filter
def age(data, max_age=0):
    if not data:
        return ""
    now = timezone.localtime()
    today = deepcopy(now)
    if not hasattr(data, "tzinfo") or not data.tzinfo:
        data = now.replace(year=data.year, month=data.month, day=data.day)

    idade = relativedelta(today, data)

    if max_age:
        td = today - data
        if td.total_seconds() > max_age * 86400:
            return date_format(data, r"d \d\e M \d\e Y")

    if idade.years or idade.months or idade.days > 2:
        years = "%s %s%s" % (
            idade.years if idade.years else "",
            _("ano") if idade.years else "",
            "s" if idade.years > 1 else "",
        )

        months = "%s%s %s%s" % (
            ", " if idade.years and idade.months else "",
            idade.months if idade.months else "",
            _("mes") if idade.months else "",
            "es" if idade.months > 1 else "",
        )
        days = "%s%s %s%s" % (
            ", " if idade.days and (idade.months or idade.years) else "",
            idade.days if idade.days else "",
            _("dia") if idade.days else "",
            "s" if idade.days > 1 else "",
        )
        return "%s%s%s" % (years.strip(), months.strip(), days.strip())

    days = "%s %s%s" % (
        idade.days if idade.days else "",
        _("dia") if idade.days else "",
        "s" if idade.days > 1 else "",
    )

    hours = "%s%s %s%s" % (
        ", " if idade.hours and idade.days else "",
        idade.hours if idade.hours else "",
        _("hora") if idade.hours else "",
        "s" if idade.hours > 1 else "",
    )

    minutes = "%s%s %s%s" % (
        ", " if idade.minutes and (idade.hours or idade.days) else "",
        idade.minutes if idade.minutes else "",
        _("minuto") if idade.minutes else "",
        "s" if idade.minutes > 1 else "",
    )

    return "%s%s%s" % (days.strip(), hours.strip(), minutes.strip())


@register.filter
def str2intabs(value):
    if not isinstance(value, str):
        return ""
    try:
        v = int(value)
        v = abs(v)
        return v
    except:
        return ""


@register.filter
def url(value):
    if value.startswith("http://") or value.startswith("https://"):
        return True
    return False


@register.filter
def component_frontend(value, prefix="<emf-"):
    if value.startswith(prefix):
        return True
    return False


@register.simple_tag
def settings_key_tag(var_name):
    return getattr(settings, var_name)


@register.filter
def settings_key_filter(var_name):
    return getattr(settings, var_name)


@register.simple_tag(takes_context=True)
def yaml_render(context, template_name, increment_space=0):
    t = template.loader.get_template(template_name)
    r = t.template.render(context)
    if not increment_space:
        return r

    r = r.split("\n")
    r = ["%s%s" % (" " * increment_space, line) for line in r]
    return mark_safe("\n".join(r))


@register.filter(is_safe=True)
@stringfilter
def dont_break_out(value):
    _safe = '<div class="dont-break-out">{}</div>'.format(value)
    _safe = mark_safe(_safe)
    return _safe


@register.filter
def timedelta_filter(data, td):
    if not data:
        data = timezone.now()
    data += timedelta(days=int(td))
    return data


@register.filter
def now_year(obj):
    return timezone.now().year


@register.filter(expects_localtime=True)
def parse_datetime(value):
    return django_parse_datetime(value)


@register.filter
def valor_por_extenso(valor):
    return num2words(valor, to="currency", lang="pt_BR")


@register.filter
def valor_str(valor):
    return formats.number_format(valor, force_grouping=True)


@register.filter
def valor_abs_str(valor):
    return formats.number_format(valor.copy_abs(), force_grouping=True)


@register.filter
def audio_url(value):
    return True if url(value) and value.endswith("mp3") else False


@register.filter
def is_video_url(value):
    video_extensions = ["mp4", "ogg", "webm", "3gp", "ogv"]
    has_ext = any([value.endswith(i) for i in video_extensions])
    return url(value) and has_ext


@register.filter
def youtube_url(value):
    # Test if YouTube video
    # tested on https://pythex.org/
    value = value.lower()
    youtube_pattern = r"^((https?://)?(www\.)?youtube\.com\/watch\?v=)"
    r = re.findall(youtube_pattern, value)

    if r:
        return True

    youtube_p2 = r"^((https?://)?(www\.)?youtu\.be\/)"
    r = re.findall(youtube_p2, value)
    if r:
        return True

    return False


@register.filter
def facebook_url(value):
    value = value.lower()
    facebook_pattern = (
        r"^((https?://)?((www|pt-br)\.)?facebook\.com(\/.+)?\/videos(\/.*)?)"
    )
    r = re.findall(facebook_pattern, value)
    return True if r else False


@register.filter
def youtube_id(value):
    from urllib.parse import parse_qs, urlparse

    u_pars = urlparse(value)
    quer_v = parse_qs(u_pars.query).get("v")
    quer_t = parse_qs(u_pars.query).get("t") or ("0",)
    if quer_v:
        return "{}?start={}".format(quer_v[0], quer_t[0])
    return "{}?start={}".format(u_pars.path[1:], quer_t[0])


@register.filter
def file_extension(value):
    import pathlib

    return pathlib.Path(value).suffix.replace(".", "")


@register.filter
def params_search_to_api(items):
    gd = {k: v for k, v in items if v and k not in ("tipo_listagem",)}
    furl = "&".join(map(lambda kv: f"{kv[0]}={kv[1]}", gd.items()))
    u = furl.replace("_b=", "=")
    u = u.replace("_i=", "=")
    u = u.replace("_is=", "=")
    u = u.replace("autoria", "autores")
    return u


@register.filter
def obfuscate_value(value, key):
    if key in [
        "hash",
        "google_recaptcha_secret_key",
        "password",
        "google_recaptcha_site_key",
        "hash_code",
        "jdata",
    ]:
        return "***************"
    return value


@register.inclusion_tag("eauth/user/avatar.html")
def avatar_user(user_render=None, css_class="avatar"):
    return {"user_render": user_render, "css_class": css_class}


@register.simple_tag(takes_context=True)
def container_css_class(context):
    css_class = context.get("container_css_class", None)
    if css_class:
        return css_class

    view = context.get("view", {})
    crud = getattr(view, "crud", None)
    if crud:
        return crud.container_css_class

    return "container"


@register.simple_tag(takes_context=True)
def view_class_name(context):
    """
    Returns the CSS class for the view.
    """
    view = context.get("view", {})
    vcn = f"{view.__class__.__name__}" if view else "main-content"
    return vcn
