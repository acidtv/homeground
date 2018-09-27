from shapely.ops import cascaded_union
from shapely.geometry import Point, MultiPolygon
from itertools import groupby
from functools import reduce
import utm

def node_intersections(nodes, min_count):
    # group by second elemnt, node_type_id
    node_groups = group_nodes(nodes, 2)

    polygon_groups = polygonize_groups(node_groups)
    count, intersections = polygon_intersections(polygon_groups)

    if count < min_count:
        raise TooFewNodeTypesException()

    if not isinstance(intersections, MultiPolygon):
        intersections = MultiPolygon([intersections])

    return intersections


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
    return counting_reduce(lambda a, b: a.intersection(b), polygons, MultiPolygon([]))


def counting_reduce(func, data, initial):
    counting_func = lambda a, b: (1, b) if a[0] == 0 else (a[0]+1, func(a[1], b))
    return reduce(counting_func, data, (0, initial))


def zone_by_latlon(lat, lon):
    zone_number = latlon_to_zone_number(lat, lon)
    zone_letter = latitude_to_zone_letter(lat)

    return zone_number, zone_letter


class TooFewNodeTypesException(Exception):
    pass
