import os
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import ChitChat.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'YourProject.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            ChitChat.routing.websocket_urlpatterns
        )
    ),
})
