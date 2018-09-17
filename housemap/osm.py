import shelve
from statistics import mean
from .models import Node
from lxml import etree

type_map = {
    'busstop': ('bus', 'yes'),
    'shop': ('shop', None),
    'bakery': ('shop', 'bakery'),
    'pub': ('amenity', 'pub'),
    'supermarket': ('shop', 'supermarket'),
    'sports-centre': ('leisure', 'sports_centre'),
    'childcare': ('amenity', 'childcare'),
    'train-station': ('railway', 'station'),
    # FIXME park / forest / nature
}


def nodes(filename, node_types):
    catch = ['node', 'way']

    # use disk based node lat-lon cache
    with shelve.open('osm-import-cache') as cache:
        with open(filename, 'rb') as file:
            xml_context = etree.iterparse(file, events=('end',))

            for action, elm in xml_context:
                node = None
                attrs = dict(elm.items())

                if elm.tag == 'node':
                    # cache node lat/lon because we might need it later if a
                    # <way/> tag refers to its coords
                    cache[attrs['id']] = (attrs['lat'], attrs['lon'])

                if elm.tag in catch:
                    node = make_node(elm, node_types, cache)

                    # clear some memory, because that might cause probs with
                    # huge import files
                    #elm.clear()
                    while elm.getprevious() is not None:
                        del elm.getparent()[0]

                if node:
                    yield node


def make_node(elm, node_types, cache):
    node_type = get_node_type(elm)

    print(elm.tag)
    if not node_type:
        return
    print(node_type)

    if not elm.get('lat'):
        if not hasattr(elm, 'node'):
            # we need refs to other nodes to get coords
            return

        coords = get_node_coords(elm, cache)
    else:
        coords = (elm.get('lat'), elm.get('lon'))

    print(coords)
    return Node(
        osm_id=elm.get('id'),
        node_type_id=node_types[node_type],
        lat=coords[0],
        lon=coords[1]
    )

def get_node_coords(elm, cache):
    if not 'node' in elm:
        return

    lat = mean([cache[node.get('id')]['lat'] for node in elm.iterchildren('node')])
    lon = mean([cache[node.get('id')]['lon'] for node in elm.iterchildren('node')])

    return (lat, lon)

def get_node_type(node):
    for tag in node.iterchildren('tag'):
        print(tag.items())
        for key, value in type_map.items():
            # check if tag key and value match
            print(value)
            if value == (tag.get('k'), tag.get('v')):
                return key
            # check if tag key matches if no value is configured
            elif value[1] is None and tag.get('k') == value[0]:
                return key
