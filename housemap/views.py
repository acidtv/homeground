from sqlalchemy import between
from . import nodetools
from .models import Node, NodeType
from .nodetools import TooFewNodeTypesException
from housemap import app, db
from flask import render_template, jsonify, request, abort
import utm

@app.route("/")
def index():
    return render_template(
        'index.html',
        node_types=db.session.query(NodeType).all()
    )


@app.route("/api/nodes")
def nodes():
    node_types = request.args.getlist('features')

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

    zone_number, zone_letter = bounds[0][2:4]

    # Select nodes. I'm going to assume all nodes within these bounds belong to
    # the same utm zone number/letter for now.
    nodes = db.session.query(Node.x, Node.y, Node.node_type_id, NodeType.default_radius) \
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
        intersections = nodetools.node_intersections(nodes, len(node_types))
    except TooFewNodeTypesException:
        intersections = []

    # Convert back to WGS84.
    wgs84_intersections = nodetools.polygons_to_latlon(intersections, zone_number, zone_letter)

    return jsonify(wgs84_intersections)
