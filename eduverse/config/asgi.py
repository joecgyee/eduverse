import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# get_asgi_application() must be called before importing anything that
# touches models, to ensure Django's app registry is populated first.
django_asgi_app = get_asgi_application()

import apps.chat.routing  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(apps.chat.routing.websocket_urlpatterns)
    ),
})