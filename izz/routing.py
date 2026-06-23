from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Die Züge verbinden sich mit ws://server/ws/stellwerk/
    re_path(r'ws/stellwerk/$', consumers.StellwerkConsumer.as_asgi()),
]