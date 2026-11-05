from django.urls.conf import path

from . import consumers

websocket_urlpatterns = [
    path('ws/time-refresh', consumers.TimeRefreshConsumer.as_asgi()),
]
