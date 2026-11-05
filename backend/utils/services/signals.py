import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def send_signal_for_websocket_time_refresh(sender, inst, **kwargs):
    action = "post_save" if "created" in kwargs else "post_delete"
    created = kwargs.get("created", False)

    if (
        hasattr(inst, "_meta")
        and inst._meta.app_config is not None
        and inst._meta.model_name
        not in (
            "auditlog",
            "metadata",
        )
    ):
        try:
            if not hasattr(inst, "id") or (
                hasattr(inst, "ws_sync") and not inst.ws_sync()
            ):
                return

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                "group_time_refresh_channel",
                {
                    "type": "time_refresh.message",
                    "message": {
                        "action": action,
                        "id": inst.id,
                        "app": inst._meta.app_label,
                        "model": inst._meta.model_name,
                        "created": created,
                    },
                },
            )
        except Exception as e:
            logger.error(
                _(
                    "Erro na comunicação com o backend do redis. "
                    "Certifique se possuir um servidor de redis "
                    "ativo funcionando como configurado em "
                    "CHANNEL_LAYERS"
                )
            )


@receiver([post_save, post_delete], dispatch_uid="timerefresh_post_signal")
def timerefresh_post_signal(sender, instance, **kwargs):
    logger.debug(f"START timerefresh_post_signal {timezone.localtime()}")
    send_signal_for_websocket_time_refresh(sender, instance, **kwargs)
    logger.debug(f"END timerefresh_post_signal {timezone.localtime()}")
