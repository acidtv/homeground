var map;
var form;
var feature_layers = [];

function init() {
	map = init_map();
	form = $('.menu form.features');

	// update map with newly selected features
	$('.menu form.features').on('submit', function(event) {
		update_map_by_form();
		event.preventDefault();
	});

	$(map).on('moveend', function(event) {
		update_map_by_form();
	})

	$('.menu form.search').on('submit', function(event) {
		query = $('input[name=q]', event.target).val();
		map_search(query);
		event.preventDefault();
	})
}

function init_map() {
	baselayer = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		maxZoom: 18,
		id: 'mapbox.streets',
		accessToken: 'pk.eyJ1IjoiYWxleC1ydWNvbGEiLCJhIjoiY2pscncyODJnMDk1bDNrbGI3dWtpbmdyNSJ9.Ary5QUiC-HZOizD7N8ping'
	});

	return new L.Map('map', {
		center: new L.LatLng(52.08, 4.33),
		zoom: 12,
		layers: [baselayer]
	});
}

function update_map_by_form() {
	update_map(
		form.serializeArray(),
		map.getBounds()
	);
}

function update_map(filter, bounds) {
	filter.push({name: 'bounds', value: bounds.toBBoxString()});

	$.getJSON(
		'/api/nodes', 
		$.param(filter),
		function(data) {
			clear_map();

			data.forEach(function(polygon) {
				feature_layers.push(L.polygon(polygon, {color: 'red'}).addTo(map));
			});
	})
}

function clear_map() {
	feature_layers.forEach(function(layer) {
		layer.removeFrom(map);
	});
}

function map_search(query) {
	url = 'https://nominatim.openstreetmap.org/search'
	params = $(event.target).serializeArray();
	params.push({name: 'format', value: 'jsonv2'});
	params.push({name: 'limit', value: 1});

	$.getJSON(
		url, 
		$.param(params),
		function(data) {
			console.log(data);
			rawbounds = data[0]['boundingbox'];
			bounds = new L.LatLngBounds(
				new L.LatLng(rawbounds[0], rawbounds[2]),
				new L.LatLng(rawbounds[1], rawbounds[3])
			);
			
			map.flyToBounds(bounds, {maxZoom: 17});
		})
}
