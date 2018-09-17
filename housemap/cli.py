import click
import itertools
from housemap import app, db
from .models import NodeType
from . import osm


@app.cli.command('init-db')
def init_db():
    click.echo('Creating tables')
    db.create_all()

    click.echo('Adding node types')
    add_nodetypes()


def add_nodetypes():
    session = db.session()

    # FIXME use config
    session.add_all([
        NodeType(name='busstop'),
        NodeType(name='shop'),
        NodeType(name='bakery'),
        NodeType(name='pub'),
        NodeType(name='supermarket'),
        NodeType(name='sports-centre'),
        NodeType(name='childcare'),
        NodeType(name='train-station'),
    ])

    session.commit()


@app.cli.command('import-osm')
@click.argument('filename')
def import_osm(filename):
    i = 0
    slice_size = 5

    session = db.session()
    node_types = dict(session.query(NodeType.name, NodeType.id).all())
    nodes = osm.nodes(filename, node_types)

    for slice in iter(lambda: list(itertools.islice(nodes, slice_size)), []):
        session.add_all(slice)
        session.commit()
        click.echo((i * slice_size) + len(slice))
        i = i + 1
