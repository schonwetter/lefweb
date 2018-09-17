from django.db import models
from random import shuffle, choice


class LEFInstance(models.Model):
	"""Represents a LEF instance in the database. It mostly acts as	a reference 
	for the preference orders of each agents present in the instance.

	Attributes:
		solved_by (CharField): Token of player that "wins" the instance.
		solution (CharField): Allocation submitted by the winner. Stored as
			comma separated values in a string.
		time_to_solution (IntegerField): Time taken (in seconds) to solve the 
			instnace.
		size (IntegerField): Size of instance.
	"""

	solved_by = models.CharField(max_length=8, null=True)
	solution = models.CharField(max_length=13, null=True)
	time_to_solution = models.IntegerField(default=0)
	size = models.IntegerField()

	@staticmethod
	def random(N):
		"""Generate a random solvable LEF instance. To ensure the instance
		is solvable, an allocation is chosen randomly and the preference orders
		for each actor is populated in accordance with the allocation.

		Args:
			N (int): Number of actors.

		Returns: 
			(LEFInstance): Database object representing the instance created.
		"""

		# `objects` contains the mapping object_idx -> object_value
		objects = list(range(N))
		shuffle(objects)
		# 1. First we declare the allocation chosen to ensure solvability:
		# For each actor, the index of the allocated object in the preference
		# order is chosen randomly.
		alloc_indices = {a: None for a in range(N)}
		for a in range(N):
			if a == 0 or a == N-1: pool = range(N-1)
			else: pool = range(N-2)
			alloc_indices[a] = choice(pool)

		# 2. Next we populate the preference orders for each actor:
		# The objects prefered to the chosen allocation are chosen among the set
		# of all possible objects restricted to the neighbors allocation.
		def get_neighbors(a):
			"""Returns the neighbors indices of actor `a`."""
			if a == 0: neighbors = [a+1]
			elif a == N-1: neighbors = [a-1]
			else: neighbors = [a-1, a+1]
			return neighbors

		instance = LEFInstance.objects.create(size=N)
		for a in range(N):
			neighbors = get_neighbors(a)
			object_pool_top = [o for o in range(N) 
				if o not in neighbors and o != a]
			shuffle(object_pool_top)

			prefs = list()
			# Populate objects prefered to the allocation.
			for pref_idx in range(alloc_indices[a]):
				prefs.append(objects[object_pool_top.pop()])

			# Set allocation in preference order.
			prefs.append(objects[a])

			# Populate rest of preference order.
			object_pool_bot = object_pool_top + neighbors
			shuffle(object_pool_bot)
			for pref_idx in range(alloc_indices[a]+1, N):
				prefs.append(objects[object_pool_bot.pop()])

			# Create LEFOrder
			LEFOrder.objects.create(instance=instance, 
				index=a, values=','.join(map(str, prefs)))

		return instance

	def check_solution(self, solution):
		"""Checks if a specific allocation is valid for the instance, that is
		no actor feel envy.

		Args:
			solution (dict): Allocation to be checked.

		Returns: (boolean) Validity of the solution.
		"""
		if self.solved_by != None: return 

		values = [p.get_values() for p in 
				self.prefs.all().order_by('index')]

		for a in range(self.size):

			if a == 0: neighbors = [a+1]
			elif a == self.size-1: neighbors = [a-1]
			else: neighbors = [a-1, a+1]

			for n in neighbors:
				neighbor_object_value = values[n][solution[str(n)]]
				neighbor_object_index = values[a].index(neighbor_object_value)

				if neighbor_object_index < solution[str(a)]:
					return False

		return True

	def serialize(self):
		"""Returns a serializable python object that can be sent over a 
		websocket connection.

		Returns: (dict) containing all relevant data.
		"""
		return {
			'size': self.size,
			'values': [p.get_values() for p in 
				self.prefs.all().order_by('index')],
			'solved_by': self.solved_by,
			'solution': list(map(int, self.solution.split(','))) 
				if self.solution else None
		}


class LEFOrder(models.Model):
	"""Defines a preference order for a single actor in an instance. The order 
	is stored as comma separated values in a string.

	Attributes:
		values (CharField): Order of objects.
		instance (ForeignKey): Refering instance.
		index (IntegerField): Index of corresponding actor in instance.
	"""
	values = models.CharField(max_length=13)
	instance = models.ForeignKey(LEFInstance, 
		on_delete=models.CASCADE, 
		related_name='prefs')
	index = models.IntegerField()

	def get_values(self):
		return list(map(int, self.values.split(',')))


class Room(models.Model):
	"""Room identifies a room in which two players can interact with each other.
	It also holds a reference to the instance the players are trying to solve.

	Attributes:
		token (CharField): Used to identify rooms in the webapp.
		current_instance (ForeignKey): Reference to the instance the players are
			currently trying to solve.
	"""
	token = models.CharField(max_length=8)
	current_instance = models.ForeignKey(LEFInstance, 
		on_delete=models.SET_NULL,
		null=True)
	
	def serialize(self):
		"""Returns a serializable python object that can be sent over a 
		websocket connection.

		Returns: (dict) containing all relevant data.
		"""
		return {
			'token': self.token,
			'connected_count': self.connected_players.count()
		}


class Player(models.Model):
	"""Player identifies a player in the database.

	Attributes:
		username (CharField): Username of player.
		token (CharField): Used to identify players in the webapp.
		connected_to (ForeignKey): Reference to the room the player is currently
			connected to.
		is_ready (BooleanField): Status of player. True if the player is in a 
			room and playing. False otherwise.
	"""
	username = models.CharField(max_length=40)
	token = models.CharField(max_length=8)
	connected_to = models.ForeignKey(Room, on_delete=models.SET_NULL, 
		null=True, related_name="connected_players")
	is_ready = models.BooleanField(default=False)

	def serialize(self):
		"""Returns a serializable python object that can be sent over a 
		websocket connection.

		Returns: (dict) containing all relevant data.
		"""
		return {
			'username': self.username,
			'token': self.token,
			'connected_to': self.connected_to.token,
			'is_ready': self.is_ready
		}