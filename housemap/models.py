from housemap import db


class NodeType(db.Model):
    __tablename__ = 'node_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    default_radius = db.Column(db.Integer())


class Node(db.Model):
    __tablename__ = 'nodes'

    id = db.Column(db.Integer, primary_key=True)
    osm_id = db.Column(db.BigInteger)
    node_type_id = db.Column(db.Integer, db.ForeignKey('node_types.id'), nullable=False)
    x = db.Column(db.Float())
    y = db.Column(db.Float())
    zone_number = db.Column(db.Integer)
    zone_letter = db.Column(db.String(length=1))

    node_type = db.relationship('NodeType')
