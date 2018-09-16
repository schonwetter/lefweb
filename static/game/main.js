angular.module('EquityGame')
.controller('MenuController', ['$rootScope', '$scope', '$cookies', 
	'WebsocketService', function($rootScope, $scope, $cookies, ws) {

	/**
	 * MenuController is in charge of the main menu's functionalities. It 
	 * requests basic data from the app such as the player's identity and which 
	 * rooms are currently active.
	 *
	 *
	 * Initialization: 
	 * First we need register the `onconnect` callback. When the controller 
	 * starts, it connects to a websocket on the url "/menu/" and requests the
	 * context of the application.
	 */
	ws.onconnect_callback = function() {
		//By sending the player token, the application is able to identify the 
		// user and create a player if needed.
		ws.send({player_token: $cookies.get('player_token')});
	}
	// Register callback in response to request.
	ws.bindCallback('load_context', function(data) {
		$rootScope.player_token = data.player_token;
		$cookies.put('player_token', data.player_token);
		$rootScope.next_room_token = data.next_room_token;
		$rootScope.rooms = data.rooms;
	});
	// Connect to the websocket service.
	ws.connect('/menu/');
	// When the user leaves the page, the websocket must be disconnected.
	$scope.$on('$routeChangeStart', function(e, n, p) {
		console.log('About to leave the page: disconnecting websocket.');
		ws.disconnect();
	});
}])
.controller('GameController', ['$rootScope', '$scope', '$routeParams', '$cookies', 
	'WebsocketService', function($rootScope, $scope, $routeParams, $cookies, ws) {

	/**
	 * The GameController handles all the game functionnalities past the main 
	 * menu. 
	 */

	let self = this;
	// `selected` contains the currently selected indices for each actor.
	self.selected = {};
	// `envy` contains the actors subject to envy in regards to the current 
	// selection.
	self.envy = {};
	// Current status of the controller.
	self.status = "loading";
	// The player token is used to identify the player within the websocket 
	// service.
	let player_token = $cookies.get('player_token');
	if (!player_token) {
		// TODO: Redirect to menu
	}

	// Similar to the MenuController, an `onconnect` callback is registered
	// to request context data on connection
	ws.onconnect_callback = function() {
		ws.send({'action': 'load_context', 'csmr_data': {}});
	}
	// Connection to websocket. We use the url paramters `room_id` and 
	// `player_token` to identify the connection.
	ws.connect('/room/'+$routeParams.room_id+'/'+player_token+'/');
	// When the user leaves the page, the websocket must be disconnected.
	$scope.$on('$routeChangeStart', function(e, n, p) {
		console.log('About to leave the page: disconnecting websocket.');
		ws.disconnect();
	});
	
	/***************************************************************************
	 * Callbacks
	 * 
	 * The GameController mainly consists of "actions" (acted when a user 
	 * interacts with the interface) and of callbacks reacting to the websocket
	 * responses.
	 **/

	/**
	 * load_context
	 * Received when the server responds to the initial request for context.
	 * Loads player information (user and adversary).
	 */
	ws.bindCallback('load_context', function(data) {
		for (let idx in data.players) {
			let player = data.players[idx];
			if (player.token === player_token) {
				self.player = player;
			} else {
				self.adversary = player;
			}
		}
	});

	/**
	 * load_instance
	 * When both players are ready, the server sends the instance to be solved 
	 * via the `load_instance` event. The GameController can then change status
	 * and the game starts.
	 */
	ws.bindCallback('load_instance', function(data) {
		self.instance = data.instance;
		if (self.instance.solved_by) {
			self.status = 'solved';
			self.selected = self.instance.solution;
		} else {
			self.status = 'playing';
		}
	});

	/**
	 * notify_diconnect
	 * If a player leaves the game page and the room has the "playing" status, 
	 * then the remaining player is notified and the game is paused while 
	 * waiting for an opponent.
	 */
	ws.bindCallback('notify_disconnect', function() {
		if (self.status === 'playing') {
			self.status = 'loading';
		}
	});

	/**
	 * check_solution
	 * Response to the `check_solution` action. If the solution is valid, this
	 * triggers the "solved" state in the room.
	 */
	ws.bindCallback('check_solution', function(data) {
		if (data.is_solved) {
			self.status = 'solved';
			self.instance = data.instance;
			self.selected = data.instance.solution;

		}
	});
	
	/***************************************************************************
	 * Actions
	 * 
	 * All possible user actions are registered in the scope and called when the 
	 * user interacts with the interface.
	 **/

	/**
	 * setReady()
	 * Sets the "ready" status of the current user.
	 */
	$scope.setReady = function() {
		if (self.player.is_ready) return;
		ws.send({'action': 'set_ready', 'csmr_data': 
			{'player_token': player_token}});
	}

	/**
	 * select()
	 * Selects an object for an actor. It also sets the envy status for all 
	 * actors in the instance and checks if the selection is valid. If the 
	 * selection is complete (i.e. all actors have an object allocated) and no 
	 * actors are envious, the current  selection is sent to the server for 
	 * evaluation (see the `check_solution` callback).
	 * 
	 * @param {int} i - index of actor in instance.
	 * @param {int} j - index of object for actor `i`.
	 */
	$scope.select = function(i, j) {
		if (self.instance.solved_by) return;

		self.number_of_select = {};
		self.n_envious = 0;
		self.selected[i] = j;

		for (var a = 0; a < self.instance.size; a++) {
			// Check if an object has been selected more than once. 
			if (self.selected[a] ===  undefined) continue;

			let selected_object_value = self.instance.values[a][self.selected[a]];
			if (self.number_of_select[selected_object_value]) {
				self.number_of_select[selected_object_value] += 1;
			} else {
				self.number_of_select[selected_object_value] = 1;
			}

			// Check envy status for all actors.
			self.envy[a] = $scope.check_actor_envy(a);
			if (self.envy[a]) self.n_envious += 1;
		}

		// If solution is valid and complete, send to server.
		if (Object.keys(self.number_of_select).length == self.instance.size &&
			self.n_envious === 0) {
			ws.send({
				'action': 'check_solution',
				'csmr_data': {
					'solution': self.selected,
					'player_token': player_token
				}
			})
		}
	}

	/**
	 * check_actor_envy()
	 * Checks if an actor is experiencing envy with the current selection.
	 *
	 * @param {int} a - index of actor in instance.
	 */
	$scope.check_actor_envy = function(a) {
		var vals = self.instance.values;

		if (a === 0) var neighbors = [a+1];
		else if (a === self.instance.size-1) var neighbors = [a-1];
		else var neighbors = [a+1, a-1];

		for (var idx in neighbors) {
			let neighbor = neighbors[idx];
			if (self.selected[a] !== undefined 
				&& self.selected[neighbor] !== undefined) {
				// Both agent have an item allocated.
				let neighbor_object_value = vals[neighbor][self.selected[neighbor]];
				let neighbor_object_index = vals[a].indexOf(neighbor_object_value);

				if (neighbor_object_index < self.selected[a]) {
					return true;
				}
			}
		}

		return false;
	}

	/***************************************************************************
	 * Style
	 */

	// Colors used in the interface. One color per object.
	let colors = {
		0: '#406E8E', // blue
		1: '#F4AC45', // yellow
		2: '#E15554', // red, alt: #A63A50
		3: '#3BB273', // green, alt: #779c79
		4: '#9983ec', // purple
		5: '#30B8F6', // clear blue
		6: '#988383'
	};

	/**
	 * get_obj_style()
	 * Returns the object background colorto be used in the interface. If the 
	 * game is under play, each object displays its associated color. However,
	 * if the game has ended and a solution has been found, only the object 
	 * selected in the solution are to be displayed in their true color.
	 * 
	 * @param {int} i - index of actor.
	 * @param {int} j - index of object.
	 * @param {int} obj - object value.
	 */
	$scope.get_obj_style = function (i, j, obj) {
		let background_color;
		if (self.status === 'solved') {
			if (self.selected[i] === j) background_color = colors[obj];
			else background_color = '#614b63';
		} else {
			background_color = colors[obj];
		}

		return {background: background_color}
	}

}]);