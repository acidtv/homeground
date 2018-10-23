from shapely.ops import cascaded_union
from shapely.geometry import Point, MultiPolygon
from itertools import groupby
from functools import reduce
from .util import Itercount
import utm


def node_intersections(nodes, min_layers, type_radius):
    """
    Creates polygons from node intersections by type based on how close
    nodes are together with type_radius

    :param nodes:       An iterable with node records. A record should consist
                        of a (lat, lon, type_id) tuple.
    :param min_layers:  The minimum amount of different node types that should
                        be present in the output. Usually the amount of types
                        you want to see the results for.
    :param type_radius: A dictionary with the radius to use per node type_id. The
                        node_type_id is the dictionary key, the radius in meters the value.
    :return:            An iterable with polygons.
    """

    # group by second element, node_type_id
    node_groups = group_nodes(nodes, 2)

    # turn nodes into polygons with buffer()
    polygon_groups = (polygonize(group, type_radius) for group in node_groups)

    # wrap polygon_groups iterator in counter to count the layers
    polygon_group_counter = Itercount(polygon_groups)

    # merge polygons
    try:
        intersections = reduce(lambda a, b: a.intersection(b), polygon_group_counter)
    except TypeError:
        # reduce() throws a TypeError when the generator was empty
        return []

    if polygon_group_counter.count() < min_layers:
        raise TooFewNodeTypesException()

    if not isinstance(intersections, MultiPolygon):
        intersections = MultiPolygon([intersections])

    # remove polygons smaller than min_area
    min_area = 2000
    filtered = filter(lambda polygon: polygon.area > min_area, intersections)

    return filtered


def group_nodes(nodes, groupby_key):
    """
    A helper to group nodes

    :param nodes:       An iterable with node records. A record should consist
                        of a (lat, lon, type_id) tuple.
    :param groupby_key: The index of the field to group by. See nodes param for possible keys.
    :return:            An iterator where every element is a group of nodes.
    """

    for key, group in groupby(nodes, key=lambda n: n[groupby_key]):
        yield group


def polygonize(nodes, type_radius):
    """
    Make polygons from a list of nodes with a buffer based on type_radius. Overlapping
    polygons are merged together.

    :param nodes:       An iterable with node records. A record should consist
                        of a (lat, lon, type_id) tuple.
    :param type_radius  A dictionary with the radius to use per node type_id. The
                        node_type_id is the dictionary key, the radius in meters the value.
    :return:            A list of polygons.
    """

    if not nodes:
        return []

    # default radius in meters
    resolution = 6

    # this cannot be a generator comprehension, because shapely wants to do a len() on it
    seperate_polygons = [Point(lat, lon).buffer(type_radius[type_id], resolution) for lat, lon, type_id in nodes]

    polygons = cascaded_union(seperate_polygons)

    if not isinstance(polygons, MultiPolygon):
        polygons = MultiPolygon([polygons])

    return polygons


def to_latlon(coords, zone_number, zone_letter):
    """
    Converts a list of utm coordinates to lat/lon.

    :param coords:      A list with (x, y) tuples.
    :param zone_number: The zone number for coordinates.
    :param zone_letter: The zone letter for coordinates.
    :return:            A list with lat/lon coordinates.
    """

    return (utm.to_latlon(x, y, zone_number, zone_letter) for x, y in coords)


def bounds_area(bounds):
    """
    Calculates the area a set of bounds span

    :param bounds:  A list with bounds: ((topleft_x, topleft_y), (bottomright_x, bottomright_y))
    :return:        The area as a float
    """
    return (bounds[1][0] - bounds[0][0]) * (bounds[1][1] - bounds[0][1])


class TooFewNodeTypesException(Exception):
    pass
