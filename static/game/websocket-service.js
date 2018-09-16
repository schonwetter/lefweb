angular.module('EquityGame')
.service('WebsocketService', ['$rootScope', function($rootScope) {

	/**
	 * WebsocketService
	 * 
	 * This service enables the use of a websocket connection to a specified 
	 * url. Javascript objects can be sent with the `send` method (the parsing
	 * to json format is done by the service). The reception of data must follow
	 * a precise format: 
	 * All messages received must contain an `action` field  and a `client_data` 
	 * field. The `action` field is used to specify the service callback to be 
	 * called and `client_data` will be passed to the callback as argument.
	 */

	$rootScope.DEBUG = true;

	var self = this;
	// List of callbacks.
	var handlers = {};

	/** 
	 * connect()
	 * Connects to a url using a ReconnectingWebSocket. If the connection is 
	 * lost, it will try to reconnect regularly.
	 * 
	 * @param {String} url - Url to which the websocket will connect.
	 */
	self.connect = function(url) {
		var ws_scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        var ws_path = ws_scheme + '://' + window.location.host + url;

        if ($rootScope.DEBUG) 
        	console.log('[WSService] Connect to ws_path: %s', ws_path);

        self.socket = new ReconnectingWebSocket(ws_path);

		self.socket.onmessage = function(e) {

			if ($rootScope.DEBUG)
				console.log('[WSService] Raw data received: %s', e.data);

			var data = JSON.parse(e.data);
			try {
				$rootScope.$apply(function() {
					handlers[data.action](data.client_data);
				});
			} catch (exc) {
				console.error('[WSService] Error handling: socket.onmessage');
				console.error('[WSService] Data received', data);
				console.error('[WSService] Exception:', exc);
			}

		};

		self.socket.onopen = function() {
			console.log('[WSService] Websocket connected.');
			self.onconnect_callback();
		};

		self.socket.onclose = function() {
			console.log('[WSService] Websocket disconnected.');
		};
	};

	/**
	 * bindCallback()
	 * This method associates an `action` field to a callback function that will
	 * be called when a message with the corresponding `action` is received.
	 * 
	 * @param {string} action - Name of the action.
	 * @param {function} callback - Function to be called.
	 */
	self.bindCallback = function(action, callback) {
		handlers[action] = callback;
	};

	/**
	 * send()
	 * Sends a message through the websocket connection and handles parsing from
	 * javascript object to json string.
	 * 
	 * @param {object} message - Data to be sent.
	 */
	self.send = function(message) {
		if ($rootScope.DEBUG)
			console.log('[WSService] Sending message', message);

		if (self.socket.readyState === WebSocket.OPEN) {
			self.socket.send(JSON.stringify(message));
		} else {
			console.log('[WSService] Unable to send message: ' + 
				'Websocket is not open...');
		}
	};

	self.disconnect = function() {
		self.socket.close();
	}

	// Override this function if you want to specify further action after the 
	// websocket has succesfully connected (e.g. send a message on connect).
	self.onconnect_callback = function() {} 
}]);