from flask import Flask, render_template, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import between
from shapely.ops import cascaded_union
from shapely.geometry import Point, MultiPolygon
from itertools import groupby
import utm

app = Flask(__name__)
app.config.from_envvar('HOUSEMAP_SETTINGS')
app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DB_ENGINE']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from .models import Node, NodeType
from . import cli


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

    bounds = (
        # upper left bound lat/lon
        (float(bounds[1]), float(bounds[0])),
        # lower right bound lat/lon
        (float(bounds[3]), float(bounds[2]))
    )

    nodes = db.session.query(Node.lat, Node.lon, Node.node_type_id, NodeType.default_radius) \
        .join(Node.node_type) \
        .filter(
            Node.node_type_id.in_(node_types),
            between(Node.lat, bounds[0][0], bounds[1][0]),
            between(Node.lon, bounds[0][1], bounds[1][1])
        ) \
        .order_by(Node.node_type_id) \
        .all()

    zone_number, zone_letter, cartesian_nodes = cartesianize(nodes, bounds)

    # group by second elemnt, node_type_id
    node_groups = group_nodes(cartesian_nodes, 2)

    polygon_groups = polygonize_groups(node_groups)

    # intersections = calculate_group_intersections(polygon_groups)

    # convert to wgs84
    wgs84_polygon_groups = polygongroups_to_latlon(polygon_groups, zone_number, zone_letter)

    return jsonify(list(wgs84_polygon_groups))


def cartesianize(nodes, bounds):
    zone_number = utm.latlon_to_zone_number(*bounds[0])
    zone_letter = utm.latitude_to_zone_letter(bounds[0][0])

    # FIXME convert to UTM on import?
    cartesian_nodes = [utm.from_latlon(lat, lon)[:2] + (type_id, radius) for lat, lon, type_id, radius in nodes]

    return (zone_number, zone_letter, cartesian_nodes)


def polygongroups_to_latlon(polygon_groups, zone_number, zone_letter):
    for polygons in polygon_groups:
        yield [to_latlon(polygon.exterior.coords, zone_number, zone_letter) for polygon in polygons]


def polygonize_groups(node_groups):
    for group in node_groups:
        yield polygonize(group)


def group_nodes(nodes, groupby_key):
    for key, group in groupby(nodes, key=lambda n: n[groupby_key]):
        yield group


def polygonize(nodes):
    if not nodes:
        return []

    # default radius in meters
    base_radius = 200
    resolution = 8

    seperate_polygons = [Point(lat, lon).buffer(base_radius * radius, resolution) for lat, lon, type_id, radius in nodes]
    polygons = cascaded_union(seperate_polygons)

    if not isinstance(polygons, MultiPolygon):
        polygons = [polygons]

    return polygons


def to_latlon(coords, zone_number, zone_letter):
    return [utm.to_latlon(lat, lon, zone_number, zone_letter) for lat, lon in coords]


def calculate_group_intersections(polygon_groups):
    for id, group in enumerate(polygon_groups):
        for polygon in group:
            for next_group in polygon_groups[id+1:]:
                for next_polygon in next_group:
                    pass
