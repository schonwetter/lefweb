from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from .utils import get_new_token
from .models import Player, Room, LEFInstance

import json


class MenuConsumer(JsonWebsocketConsumer):
	"""MenuConsumer handles websocket connection for user in the menu."""

	def connect(self):
		self.accept()

	def disconnect(self, close_code):
		pass

	def receive_json(self, content):
		"""Handles the unique action possible within the menu: `load_context`.
		If the user requesting the context is new (i.e. doesn't have a token), 
		a new Player object is created in the database.

		The context refers to the rooms currently active.
		"""
		player_token = content.get('player_token', None)
		player_results = Player.objects.filter(token=player_token)
		if player_results.count() <= 0:
			player_token = get_new_token()
			Player.objects.create(token=player_token)

		# Send relevant data back to browser
		self.send_json(content={
			'action': 'load_context',
			'client_data': {
				'player_token': player_token,
				'next_room_token': get_new_token(),
				'rooms': [r.serialize() 
					for r in Room.objects.all()]
			}
		})


class RoomConsumer(JsonWebsocketConsumer):
	"""RoomConsumer handles websocket connections for users playing in a room.

	Because JsonWebsocketConsumer is synchronous, all access to database do not 
	need protection against concurrency.
	"""

	def connect(self):
		"""When a user connects to a room, the websocket connection is added 
		to a group specific to the room. All responses can then be broadcasted
		to the players in the room.
		"""
		player_token = self.scope['url_route']['kwargs']['player_token']
		room_token = self.scope['url_route']['kwargs']['room_token']
		self.group_name = 'group-{}'.format(room_token)
		# Join room group channel
		async_to_sync(self.channel_layer.group_add)(
			self.group_name,
			self.channel_name
		)
		# Check room existence in database.
		room_results = Room.objects.filter(token=room_token)
		if room_results.count() <= 0:
			# If room does not exist, create object in database.
			room = Room.objects.create(token=room_token)
		else:
			room = room_results[0]
		
		# Set player status
		player = Player.objects.get(token=player_token)
		player.connected_to = room
		player.save()

		self.accept()

	def disconnect(self, close_code):
		"""This updates the player status and closes the room if no players are
		left.
		"""

		# Leave room group
		async_to_sync(self.channel_layer.group_discard)(
			self.group_name,
			self.channel_name
		)
		
		player_token = self.scope['url_route']['kwargs']['player_token']
		room_token = self.scope['url_route']['kwargs']['room_token']
		# Update player status
		player = Player.objects.get(token=player_token)
		player.connected_to = None
		player.is_ready = False
		player.save()
		# Notify other players
		self.notify_disconnect()
		# If last player to leave the room, delete room.
		room = Room.objects.get(token=room_token)
		players_connected = room.connected_players
		if players_connected.count() <= 0:
			room.delete()

	def receive_json(self, content):
		"""For each request, calls the correct handler (see RoomHandler) and
		sends back the data returned by the handler.

		Args:
			content (dict): data received.
		"""

		# Inject room_token for handlers
		content['csmr_data']['room_token'] = self.scope['url_route']\
			['kwargs']['room_token']
		# Handle request.
		return_data = getattr(RoomHandler, 
			content['action'])(content['csmr_data'])

		callback = return_data.pop('callback', None)
		self.send_return_data(return_data)
		if callback:
			# FIX: No need to send callback data separately as the process is 
			# synchronous and the user receives both messages at the same time..
			callback_data = callback(content['csmr_data'])
			self.send_return_data(callback_data)
		

	def broadcast(self, event):
		"""When a message is of type broadcast, this method is called to send
		data back to the players.

		Args:
			event (dict): event data.
		"""
		self.send_json(event['data'])

	def notify_disconnect(self):
		"""When a user disconnect, a disconnect notification is broadcasted in
		the roomm.
		"""
		async_to_sync(self.channel_layer.group_send)(
			self.group_name,
			{
				'type': 'broadcast',
				'data': {'action': 'notify_disconnect'}
			}
		)

	def send_return_data(self, return_data):
		"""Method used to send data back to the players. If the data contains a
		key `type` with the value "broadcast", the message is broadcasted to all
		players in the room.
		"""
		if return_data.pop('type', None) == 'broadcast':
			async_to_sync(self.channel_layer.group_send)(
				self.group_name,
				{
					'type': 'broadcast',
					'data': return_data
				}
			)
		else:
			self.send_json(return_data)


class RoomHandler:

	@staticmethod
	def load_context(data):
		"""Called when a user connects to a room. The serialized players are 
		sent and if both players are ready, a new instance is created and sent.

		Args:
			data (dict): request data.

		Returns:
			(dict) Data to be sent back to the requesting user.
		"""
		ctx = {}
		# get context
		room = Room.objects.get(token=data['room_token'])
		ctx['players'] = room.connected_players.all()
		# If all players are ready, load instance after loading context.
		if ctx['players'].filter(is_ready=True).count() == 2:
			ctx['callback'] = RoomHandler.load_instance
		# send context
		return {
			'type': 'broadcast',
			'action': 'load_context',
			'client_data': {
				'players': [p.serialize() for p in ctx['players']]
			},
			'callback': ctx.get('callback')
		}

	@staticmethod
	def set_ready(data):
		# Set player ready status
		player = Player.objects.get(token=data['player_token'])
		player.is_ready = True
		player.save()

		return RoomHandler.load_context(data)

	@staticmethod
	def load_instance(data):
		# Called when a room should be sent the instance. If the room does not
		# have an associated instance, a new one is created.
		room = Room.objects.get(token=data['room_token'])
		if not room.current_instance:
			room.current_instance = LEFInstance.random(5)
			room.save()

		return {
		 	'type': 'broadcast',
			'action': 'load_instance',
			'client_data': {
				'instance': room.current_instance.serialize()
			}
		}

	@staticmethod
	def check_solution(data):
		# Handles the evaluation of a solution from a player.
		# If the solution is valid, the correct notification is sent back to
		# both players.
		room = Room.objects.get(token=data['room_token'])
		instance = room.current_instance

		is_solved = instance.check_solution(data['solution'])
		if is_solved:
			instance.solved_by = data['player_token']
			instance.solution = ','.join(map(str, 
				[data['solution'][str(x)] for x in range(instance.size)]
			))
			instance.save()

		return {
			'type': 'broadcast' if is_solved else None,
			'action': 'check_solution',
			'client_data': {
				'is_solved': is_solved,
				'instance': instance.serialize()
			}
		}