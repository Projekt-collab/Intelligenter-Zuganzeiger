"""
ASGI config for izz project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'izz.settings')

# 1. Zuerst die Django-ASGI-App initialisieren.
# Dadurch lädt Django intern alle Apps, Modelle und die Registry!
django_asgi_app = get_asgi_application()

# 2. ERST JETZT dürfen wir Dateien importieren, die auf Modelle zugreifen!
import izz.routing

application = ProtocolTypeRouter({
    # Normales HTTP
    "http": django_asgi_app,

    # WebSockets
    "websocket": AuthMiddlewareStack(
        URLRouter(
            izz.routing.websocket_urlpatterns
        )
    ),
})