import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack  
from channels.layers import get_channel_layer
from apps.messaging.routing import websocket_urlpatterns 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telemedicine_project.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handles HTTP requests
    "websocket": AuthMiddlewareStack( 
        URLRouter(websocket_urlpatterns)
    ),
})

channel_layer = get_channel_layer() 
