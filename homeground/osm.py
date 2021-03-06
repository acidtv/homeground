import shelve
import utm
import os
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
    """
    Yields nodes read from filename

    :param filename:    An Openstreetmap xml export file to read nodes from
    :param node_types:  A dictionary with node types to import where the key is the OSM node name and the value the node_type_id
    :return:            Iterator with nodes
    """

    catch = ['node', 'way']
    used = ['tag', 'nd']
    cachefile = 'osm-import-cache'

    # use disk based node lat-lon cache
    with shelve.open(cachefile) as cache:
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

                if nodes:
                    for node in nodes:
                        yield node

                if (elm.tag in catch) or (elm.tag not in used):
                    # Clear some memory, because that might cause probs with huge import files.
                    # Only clear when we've encountered something interesting (like a node, way), otherwise
                    # tags within a node will be removed too.
                    # Clearing happens after yielding the nodes, because otherwise the node will
                    # be cleared before it has yielded.
                    elm.clear()
                    while elm.getprevious() is not None:
                        del elm.getparent()[0]

    os.remove(cachefile)


def make_nodes(elm, available_node_types, cache):
    """
    Creates Node() objects from an xml element

    An xml element can contain multiple nodes.

    :param elm:                     An xml element
    :param available_node_types:    Node types to look for
    :param cache:                   The shelve node coordinate cache
    :return:                        An iterator with nodes
    """
    node_types = get_node_types(elm)

    if not node_types:
        return

    if not elm.get('lat'):
        try:
            coords = get_node_coords(elm, cache)
        except Exception as e:
            print("Could not get coords: {0}".format(e))
            return
    else:
        coords = (float(elm.get('lat')), float(elm.get('lon')))

    for node_type in node_types:
        node = Node(
            osm_id=elm.get('id'),
            node_type_id=available_node_types[node_type]
        )

        node.x, node.y, node.zone_number, node.zone_letter = utm.from_latlon(*coords)

        yield node


def get_node_coords(elm, cache):
    """
    Get lat/lon coordinates for elm

    :param elm:     An xml element
    :param cache:   The shelve node coordinate cache
    :return:        A lat/lon tuple
    """
    children = list(elm.iterchildren('nd'))

    if not children:
        raise Exception('No referenes to nodes found in elm {0}'.format(elm.tag))

    lat = mean([float(cache[node.get('ref')][0]) for node in children])
    lon = mean([float(cache[node.get('ref')][1]) for node in children])

    return (lat, lon)


def get_node_types(node):
    """
    Yields node types from an xml element

    :param node:    An xml element
    :return:        An iterator with node type names
    """
    for tag in node.iterchildren('tag'):
        for key, value in type_map.items():
            # check if tag key and value match
            if value == (tag.get('k'), tag.get('v')):
                yield key
            # check if tag key matches if no value is configured
            elif value[1] is None and tag.get('k') == value[0]:
                yield key


class InfiniteXML (object):
    """
    Class for testing the import code for memory leaks by providing an
    infinite import-compatible xml stream
    """

    def __init__(self):
        self._root = True
        self.i = 0

    def read(self, len=None):
        self.i = self.i + 1
        if self._root:
            self._root = False
            return b"<?xml version='1.0' encoding='US-ASCII'?><records>\n"
        else:
            return b'<node id="%d" lat="50" lon="40">\n\t<ancestor attribute="value">text value</ancestor>\n</node>\n' % self.i
