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
    'railway-station': ('railway', 'station'),
    # FIXME park / forest / nature
}


def nodes(filename, node_types):
    catch = ['node', 'way']
    used = ['tag', 'nd']

    # use disk based node lat-lon cache
    with shelve.open('osm-import-cache') as cache:
        with open(filename, 'rb') as file:
            xml_context = etree.iterparse(file, events=('end',))

            for action, elm in xml_context:
                nodes = None
                attrs = dict(elm.items())

                if elm.tag == 'node':
                    # cache node lat/lon because we might need it later if a
                    # <way/> tag refers to its coords
                    cache[attrs['id']] = (attrs['lat'], attrs['lon'])

                if elm.tag in catch:
                    nodes = make_nodes(elm, node_types, cache)

                if (elm.tag in catch) or (elm.tag not in used):
                    # clear some memory, because that might cause probs with
                    # huge import files
                    # only clear when we've encountered something interesting (like a node, way), otherwise
                    # tags within a node will be removed too
                    elm.clear()
                    while elm.getprevious() is not None:
                        del elm.getparent()[0]

                if nodes:
                    for node in nodes:
                        yield node


def make_nodes(elm, available_node_types, cache):
    node_types = get_node_types(elm)

    if not node_types:
        return

    print(dict(elm.items()))
    if not elm.get('lat'):
        coords = get_node_coords(elm, cache)
    else:
        coords = (elm.get('lat'), elm.get('lon'))

    for node_type in node_types:
        yield Node(
            osm_id=elm.get('id'),
            node_type_id=available_node_types[node_type],
            lat=coords[0],
            lon=coords[1]
        )

def get_node_coords(elm, cache):
    lat = mean([float(cache[node.get('ref')][0]) for node in elm.iterchildren('nd')])
    lon = mean([float(cache[node.get('ref')][1]) for node in elm.iterchildren('nd')])

    return (lat, lon)

def get_node_types(node):
    for tag in node.iterchildren('tag'):
        for key, value in type_map.items():
            # check if tag key and value match
            if value == (tag.get('k'), tag.get('v')):
                yield key
            # check if tag key matches if no value is configured
            elif value[1] is None and tag.get('k') == value[0]:
                yield key


# for testing the import code for memory leaks
class InfiniteXML (object):
    def __init__(self):
        self._root = True
        self.i = 0
    def read(self, len=None):
        self.i = self.i + 1
        if self._root:
            self._root=False
            return b"<?xml version='1.0' encoding='US-ASCII'?><records>\n"
        else:
            return b'<node id="%d" lat="50" lon="40">\n\t<ancestor attribute="value">text value</ancestor>\n</node>\n' % self.i

