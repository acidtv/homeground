from sqlalchemy import between
from . import nodetools
from .models import Node, NodeType
from .nodetools import TooFewNodeTypesException
from housemap import app, db
from flask import render_template, jsonify, request, abort
import utm


@app.route("/")
def index():
    ranges = [
        [50, '50m'],
        [100, '100m'],
        [150, '150m'],
        [200, '200m'],
        [250, '250m'],
        [300, '300m'],
        [400, '400m'],
        [500, '500m'],
        [600, '600m'],
        [750, '750m'],
        [1000, '1km'],
        [1250, '1.25km'],
        [1500, '1.5km'],
        [2000, '2km'],
    ]

    return render_template(
        'index.html',
        node_types=db.session.query(NodeType).all(),
        ranges=ranges
    )


@app.route("/api/nodes")
def nodes():
    max_viewport_area = 15000 * 15000 # 15km * 15km
    node_types = request.args.getlist('features')
    radius = dict([map(int, value.split(',')) for value in request.args.getlist('radius')])

    try:
        bounds = request.args.get('bounds').split(',')
    except TypeError:
        abort(400)

    # Convert bounds to utm
    bounds = (
        # upper left bound lat/lon
        utm.from_latlon(float(bounds[1]), float(bounds[0])),
        # lower right bound lat/lon
        utm.from_latlon(float(bounds[3]), float(bounds[2]))
    )

    if nodetools.bounds_area(bounds) > max_viewport_area:
        return jsonify({'error': 'Zoom in to view the results'})

    zone_number, zone_letter = bounds[0][2:4]

    # Select nodes. I'm going to assume all nodes within these bounds belong to
    # the same utm zone number/letter for now.
    nodes = db.session.query(Node.x, Node.y, Node.node_type_id) \
        .join(Node.node_type) \
        .filter(
            Node.node_type_id.in_(node_types),
            between(Node.x, bounds[0][0], bounds[1][0]),
            between(Node.y, bounds[0][1], bounds[1][1]),
            Node.zone_number == zone_number,
            Node.zone_letter == zone_letter
        ) \
        .order_by(Node.node_type_id) \
        .all()

    try:
        intersections = nodetools.node_intersections(nodes, min_layers=len(node_types), type_radius=radius)
    except TooFewNodeTypesException:
        intersections = []

    # Convert back to WGS84.
    latlon_intersections = nodetools.polygons_to_latlon(intersections, zone_number, zone_letter)

    data = {
        'polygons': latlon_intersections
    }

    return jsonify(data)
