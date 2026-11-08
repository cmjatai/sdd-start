import inspect
import json
import logging

from django.conf import settings
from django.core import serializers
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from backend.eauth.models import AuditLog

logger = logging.getLogger(__name__)


def auditlog_signal_function(sender, **kwargs):
    try:
        app_name = sender._meta.app_config.name[:10]
        if app_name not in ('backend',):
            return
    except:
        # não é necessário usar logger, aqui é usada apenas para
        # eliminar um o if complexo
        return

    instance = kwargs.get('instance')
    if instance._meta.model in (
        AuditLog,  # Causa recursividade
    ):
        return

    u = None
    stack = ''
    for i in inspect.stack():
        stack = str(i)
        if i.function == 'migrate':
            return
        r = i.frame.f_locals.get('request', None)
        try:
            if r.user._meta.label == settings.AUTH_USER_MODEL:
                u = r.user
                if u.is_anonymous:
                    return
                break
        except:
            # não é necessário usar logger, aqui é usada apenas para
            # eliminar um o if complexo
            pass

    try:
        # logger.info('\n'.join(stack))

        operation = kwargs.get('created', 'D')
        if operation != 'D':
            operation = 'C' if operation else 'U'

        al = AuditLog()
        al.user = u
        al.email = u.email if u else ''
        al.operation = operation
        al.obj = json.loads(serializers.serialize('json', (instance,)))
        al.content_object = instance if operation != 'D' else None
        al.obj_id = instance.id
        al.model_name = instance._meta.model_name
        al.app_name = instance._meta.app_label

        al.obj[0]['stack'] = stack

        al.save()

    except Exception as e:
        logger.error('Error saving auditing log object')
        logger.error(e)


@receiver([post_save, post_delete], dispatch_uid='auditlog_post_signal')
def auditlog_post_signal(sender, **kwargs):
    logger.debug(f'START auditlog_post_signal {timezone.localtime()}')
    auditlog_signal_function(sender, **kwargs)
    logger.debug(f'END auditlog_post_signal {timezone.localtime()}')
