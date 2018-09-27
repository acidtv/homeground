from shapely.ops import cascaded_union
from shapely.geometry import Point, MultiPolygon
from itertools import groupby
from functools import reduce
import utm

def node_intersections(nodes, bounds):
    zone_number, zone_letter, cartesian_nodes = cartesianize(nodes, bounds)

    # group by second elemnt, node_type_id
    node_groups = group_nodes(cartesian_nodes, 2)

    polygon_groups = polygonize_groups(node_groups)

    # calculating intersections does not work with an iterator :(
    intersections = polygon_intersections(polygon_groups)

    if not isinstance(intersections, MultiPolygon):
        intersections = MultiPolygon([intersections])

    # convert to wgs84
    wgs84_intersections = polygons_to_latlon(intersections, zone_number, zone_letter)

    return wgs84_intersections

def cartesianize(nodes, bounds):
    zone_number = utm.latlon_to_zone_number(*bounds[0])
    zone_letter = utm.latitude_to_zone_letter(bounds[0][0])

    # FIXME convert to UTM on import?
    cartesian_nodes = [utm.from_latlon(lat, lon)[:2] + (type_id, radius) for lat, lon, type_id, radius in nodes]

    return (zone_number, zone_letter, cartesian_nodes)


def polygongroups_to_latlon(polygon_groups, zone_number, zone_letter):
    for polygons in polygon_groups:
        yield polygons_to_latlon(polygons, zone_number, zone_letter)


def polygons_to_latlon(polygons, zone_number, zone_letter):
    return [to_latlon(polygon.exterior.coords, zone_number, zone_letter) for polygon in polygons]


def polygonize_groups(node_groups):
    for group in node_groups:
        yield polygonize(group)


def group_nodes(nodes, groupby_key):
    for key, group in groupby(nodes, key=lambda n: n[groupby_key]):
        yield group


def polygonize(nodes):
    if not nodes:
        return []

    # default radius in meters
    base_radius = 200
    resolution = 8

    seperate_polygons = [Point(lat, lon).buffer(base_radius * radius, resolution) for lat, lon, type_id, radius in nodes]
    polygons = cascaded_union(seperate_polygons)

    if not isinstance(polygons, MultiPolygon):
        polygons = MultiPolygon([polygons])

    return polygons


def to_latlon(coords, zone_number, zone_letter):
    return [utm.to_latlon(lat, lon, zone_number, zone_letter) for lat, lon in coords]


def polygon_intersections(polygons):
    return reduce(lambda a, b: a.intersection(b), polygons)
