from flask import Flask, render_template, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import between
from . import nodetools

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

    return jsonify(list(nodetools.node_intersections(nodes, bounds)))
