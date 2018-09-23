from flask import Flask, render_template, jsonify, request, abort, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import between
from shapely.ops import cascaded_union
from shapely.geometry import Point, MultiPolygon

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
        bounding_box = request.args.get('bounds').split(',')
    except TypeError:
        abort(400)

    nodes = db.session.query(Node.lat, Node.lon, NodeType.default_radius) \
        .join(Node.node_type) \
        .filter(
            Node.node_type_id.in_(node_types),
            between(Node.lat, bounding_box[1], bounding_box[3]),
            between(Node.lon, bounding_box[0], bounding_box[2])
        ) \
        .all()

    polygons = polygonize(nodes)

    return jsonify(polygons)

def polygonize(nodes):
    base_radius = 0.0005
    seperate_polygons = [Point(lat, lon).buffer(base_radius * radius) for lat, lon, radius in nodes]
    polygons = cascaded_union(seperate_polygons)

    if not isinstance(polygons, MultiPolygon):
        polygons = [polygons]

    return [list(polygon.exterior.coords) for polygon in polygons]
