from housemap import db

class NodeType(db.Model):
    __tablename__ = 'node_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    default_radius = db.Column(db.Float())

class Node(db.Model):
    __tablename__ = 'nodes'

    id = db.Column(db.Integer, primary_key=True)
    osm_id = db.Column(db.BigInteger)
    node_type_id = db.Column(db.Integer, db.ForeignKey('node_types.id'), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

    node_type = db.relationship('NodeType')
