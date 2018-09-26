from flask import Flask, render_template, jsonify, request, abort, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import between
from shapely.ops import cascaded_union
from shapely.geometry import Point, MultiPolygon
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

    nodes = db.session.query(Node.lat, Node.lon, NodeType.default_radius) \
        .join(Node.node_type) \
        .filter(
            Node.node_type_id.in_(node_types),
            between(Node.lat, bounds[0][0], bounds[1][0]),
            between(Node.lon, bounds[0][1], bounds[1][1])
        ) \
        .all()

    polygons = polygonize(nodes, bounds)

    return jsonify(polygons)


def polygonize(nodes, bounds):
    if not nodes:
        return []

    # default radius in meters
    base_radius = 100

    zone_number = utm.latlon_to_zone_number(*bounds[0])
    zone_letter = utm.latitude_to_zone_letter(bounds[0][0])

    # FIXME convert to UTM on import?
    cartesian_nodes = [utm.from_latlon(lat, lon)[:2] + (radius,) for lat, lon, radius in nodes]

    seperate_polygons = [Point(lat, lon).buffer(base_radius * radius) for lat, lon, radius in cartesian_nodes]
    polygons = cascaded_union(seperate_polygons)

    if not isinstance(polygons, MultiPolygon):
        polygons = [polygons]

    polygons_coords = [to_latlon(polygon.exterior.coords, zone_number, zone_letter) for polygon in polygons]

    return polygons_coords


def to_latlon(coords, zone_number, zone_letter):
    return [utm.to_latlon(lat, lon, zone_number, zone_letter) for lat, lon in coords]
