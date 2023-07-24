"""
ASGI config for ainterview project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
import speak_to_chat.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ainterview.settings")
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(speak_to_chat.routing.websocket_urlpatterns)
        ),
    }
)
