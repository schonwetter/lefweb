# from channels.routing import route
# from game.consumers import ws_connect, ws_disconnect
from . import consumers
from django.conf.urls import url

websocket_urlpatterns = [
	url(r"^menu/", consumers.MenuConsumer),
	url(r"^room/(?P<room_token>[^/]+)/(?P<player_token>[^/]+)/$", 
		consumers.RoomConsumer)
]
