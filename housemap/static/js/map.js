var map;
var form;
var heatmaplayer;

function init() {
	heatmaplayer = init_heatmap();
	map = init_map();
	form = $('.menu form.features');

	// update map with newly selected features
	$('.menu form.features').on('submit', function(event) {
		update_heatmap_by_form();
		event.preventDefault();
	});

	$(map).on('moveend', function(event) {
		update_heatmap_by_form();
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

function init_heatmap() {
	var cfg = {
		// radius should be small ONLY if scaleRadius is true (or small radius is intended)
		// if scaleRadius is false it will be the constant radius used in pixels
		"radius": .003,
		"maxOpacity": .5, 
		// scales the radius based on map zoom
		"scaleRadius": true, 
		// if set to false the heatmap uses the global maximum for colorization
		// if activated: uses the data maximum within the current map boundaries 
		//   (there will always be a red spot with useLocalExtremas true)
		"useLocalExtrema": false,
		// which field name in your data represents the latitude - default "lat"
		latField: "0",
		// which field name in your data represents the longitude - default "lng"
		lngField: "1",
		// which field name in your data represents the data value - default "value"
		valueField: 'count'
	};

	return new HeatmapOverlay(cfg);
}

function update_heatmap_by_form() {
	update_heatmap(
		heatmaplayer, 
		form.serializeArray(),
		map.getBounds()
	);
}

function update_heatmap(heatmaplayer, filter, bounds) {
	filter.push({name: 'bounds', value: bounds.toBBoxString()});

	$.getJSON(
		'/api/nodes', 
		$.param(filter),
		function(data) {
			/*
			heatmaplayer.setData({
				max: 5,
				data: data,
			});

			heatmaplayer.addTo(map);
			*/

			data.forEach(function(polygon) {
				L.polygon(polygon, {color: 'red'}).addTo(map);
			});
	})
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
			
			// hide heatmap while flying
			heatmaplayer.remove();

			map.flyToBounds(bounds, {maxZoom: 17});
			//L.marker([data[0]['lat'], data[0]['lon']]).addTo(map);
		})
}
