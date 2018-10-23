var map;
var form;
var feature_layers = [];
var last_filter_bounds;
var last_filter;

function init() {
	map = init_map();
	form = $('.menu form.features');

	last_filter_bounds = map.getBounds();
	last_filter = [];

	// update map with newly selected features
	$('.menu form.features').on('submit', function(event) {
		update_map_by_form();
		toggle_menu();
		event.preventDefault();
	});

	$(map).on('moveend', function(event) {
		update_map_by_form();
	});

	$(map).on('movestart', function(event) {
		if ( ! last_filter_bounds.contains(map.getBounds()))
		{
			// expand last filter bounds
			last_filter_bounds = map.getBounds();
		}
	});

	$('.menu form.search').on('submit', function(event) {
		query = $('input[name=q]', event.target).val();
		map_search(query);
		toggle_menu();
		event.preventDefault();
	});

	$('.menu form.features input.feature_check').on('change', function(event) {
		$(event.currentTarget).parents('li').toggleClass('active');
	});

	$('.menu .toggle-menu').on('click', function(event) {
		toggle_menu();
		event.preventDefault();
	})
}

function toggle_menu() {
	$('.menu').toggleClass('show-mobile');
}

function init_map() {
	baselayer = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		maxZoom: 18,
		id: 'mapbox.streets',
		accessToken: 'pk.eyJ1IjoiYWxleC1ydWNvbGEiLCJhIjoiY2pscncyODJnMDk1bDNrbGI3dWtpbmdyNSJ9.Ary5QUiC-HZOizD7N8ping',
	});

	mapdata = $('#map').data();

	map = new L.Map('map', {
		center: new L.LatLng(mapdata['lat'], mapdata['lon']),
		zoom: 15,
		layers: [baselayer],
		zoomControl: false
	});

	L.control.zoom({
		position:'bottomright'
	}).addTo(map);

	return map;
}

function update_map_by_form() {
	bounds = map.getBounds();
	filter = form.serializeArray();

	cmp_last_filter = JSON.stringify(last_filter);
	cmp_filter = JSON.stringify(filter);

	clear_notifications();

	if (cmp_last_filter != cmp_filter)
	{
		// save bounds if filter changed, so we know we have the results for that query within these bounds
		last_filter_bounds = bounds;
		last_filter = filter;
	}
	else if (last_filter_bounds.contains(bounds))
	{
		// same query and new bounds are smaller than last bounds, so don't do a new query
		return;
	}

	update_map(filter, bounds);
}

function update_map(filter, bounds) {
	// copy filter and create query array with bounds
	query = filter.slice();
	query.push({name: 'bounds', value: bounds.toBBoxString()});

	$.getJSON(
		'/api/nodes', 
		$.param(query),
		function(data) {
			clear_map();

			if ('error' in data) {
				notification(data['error']);
				clear_polygons_cache();
			}

			if ('polygons' in data) {
				data['polygons'].forEach(function(polygon) {
					feature_layers.push(L.polygon(polygon, {color: 'red'}).addTo(map));
				});
			}
	})
}

function clear_map() {
	feature_layers.forEach(function(layer) {
		layer.removeFrom(map);
	});
}

function map_search(query) {
	url = 'https://nominatim.openstreetmap.org/search'
	params = [
		{name: 'q', value: query},
		{name: 'format', value: 'jsonv2'},
		{name: 'limit', value: 1},
	];

	$.getJSON(
		url, 
		$.param(params),
		function(data) {
			map.flyTo([data[0]['lat'], data[0]['lon']], 15);
		})
}

function notification(text) {
	$('.notifications').append("<div>" + text + "</div>");

	window.setTimeout(clear_notifications, 10000);
}

function clear_notifications() {
	$('.notifications div').remove();
}

function clear_polygons_cache() {
	last_filter_bounds = map.getBounds();
	last_filter = [];
}
