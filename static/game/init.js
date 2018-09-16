angular.module('EquityGame', ['ngRoute', 'ngCookies'])
.config(function($interpolateProvider) {
	/** 
	 * Replace interpolate symbols so Django templates and AngularJS 
	 * can cohabitate.
	 */
	$interpolateProvider.startSymbol('{[{').endSymbol('}]}');
})
.config(function($routeProvider, $locationProvider) {
	$routeProvider
	.when('/', {
		templateUrl: '/static/partials/menu.html',
		controller: 'MenuController as mCtrl'
	})
	.when('/play/:room_id', {
		templateUrl: '/static/partials/room.html',
		controller: 'GameController as gCtrl'
	})
	.when('/spectate/:room_id', {
		// TODO
	});
});