"""
ASGI config for izz project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import izz.routing  # Das erstellen wir im nächsten Schritt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'izz.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Normales HTTP (z.B. für die Admin-Oberfläche)
    "http": django_asgi_app,

    # WebSockets (für unsere Echtzeit-Züge)
    "websocket": AuthMiddlewareStack(
        URLRouter(
            izz.routing.websocket_urlpatterns
        )
    ),
})