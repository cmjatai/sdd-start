import json
import logging
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SyncRefreshConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        from backend.globalrules.map_rules import rules_patterns_public

        super().__init__(*args, **kwargs)

        self.rules_patterns_public = rules_patterns_public

    async def connect(self):
        try:
            self.room_name = "sync_refresh_channel"
            self.room_group_name = "group_%s" % self.room_name
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            logger.error(f"Erro ao conectar no SyncRefreshConsumer: {e}")

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        except Exception as e:
            logger.error(f"Erro ao desconectar do SyncRefreshConsumer: {e}")

    # Receive message from WebSocket
    async def receive(self, text_data):

        jdata = json.loads(text_data)

        try:
            logger.debug(f"Received message: {jdata}")

            type_msg = jdata.get("type", "")

            if type_msg == "ping":
                ping_now = jdata.get("ping_now", "")
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "pong",
                            "message": {
                                "timestamp_server": time.time() * 1000,
                                "ping_now": ping_now,
                            },
                        }
                    )
                )
                return

            if type_msg == "command":
                command = jdata.get("command", "")
                app = jdata.get("app", "")
                model = jdata.get("model", "")
                params = jdata.get("params", {})
                user = self.scope.get("user")

                if not command:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "command_result",
                                "command": command,
                                "error": "Comando não especificado",
                            }
                        )
                    )
                    return

        except Exception as e:
            logger.error(
                f"Erro ao processar mensagem recebida no SyncRefreshConsumer: {e}"
            )
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "command_result",
                        "command": jdata.get("command", ""),
                        "error": str(e),
                    }
                )
            )

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "sync_refresh_message", "message": jdata}
        )

    async def command_result(self, event):
        """Enviar resultado do comando para o cliente"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "command_result",
                    "command": event["command"],
                    "result": event["result"],
                }
            )
        )

    # Receive message from room group
    async def sync_refresh_message(self, event):

        try:
            logger.debug('passou sync_refresh_message')
            message = event["message"]
            logger.debug(f"Mensagem recebida no sync_refresh_message: {message}")
            app = message.get("app")
            model = message.get("model")

            u = self.scope.get("user")

            key = f"{app}:{model}"
            perms_publicas = self.rules_patterns_public.get(key, set())

            perm_detail = f"{app}.detail_{model}"
            perm_view = f"{app}.view_{model}"

            if u.is_anonymous and not perms_publicas:
                detail_perm = False
            elif u.is_anonymous:
                detail_perm = (
                    perm_detail in perms_publicas or perm_view in perms_publicas
                )
            elif not u.is_superuser:
                detail_perm = await database_sync_to_async(u.has_perm)(perm_detail)
                if not detail_perm:
                    detail_perm = await database_sync_to_async(u.has_perm)(perm_view)
            else:
                detail_perm = True

            try:
                if not detail_perm:
                    del message["instance"]
            except KeyError:
                pass

            # Send message to WebSocket
            await self.send(text_data=json.dumps(event))

        except Exception as e:
            logger.error(
                f"Erro ao processar sync_refresh_message no SyncRefreshConsumer: {e}"
            )
            await self.send(text_data=json.dumps({"type": "error", "error": str(e)}))
