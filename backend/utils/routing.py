from django.urls.conf import path

from . import consumers

websocket_urlpatterns = [
    path("ws/sync/", consumers.SyncRefreshConsumer.as_asgi()),
]
