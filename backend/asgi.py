import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.handlers.asgi import ASGIHandler

from backend.utils import routing as backend_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

application = ProtocolTypeRouter(
    {
        'http': ASGIHandler(),
        'websocket': AuthMiddlewareStack(
            URLRouter(backend_routing.websocket_urlpatterns)
        ),
        # Just HTTP for now. (We can add other protocols later.)
    }
)
