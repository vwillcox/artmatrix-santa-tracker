#!/usr/bin/env python3
"""Cuts the world's coasts, lakes and borders into tiles for the plugin's close-up map.

    uv run --with shapely tools/land.py santa_tracker/land.bin

When Santa is near your house the plugin swaps the globe for a map of your part of
the world, drawn on the board. It can't hold the whole world's coastline at once,
so this cuts it into TILE degree squares, and the board reads the few it needs.

The data is Natural Earth's 1:50m land, lakes and country boundary lines, which are
in the public domain (naturalearthdata.com). They're fetched into tools/data the
first time.

land.bin is: "STL1", TILE as a 16 bit number, 16 bits spare; then for each tile, row
by row from the south-west corner of the world, where its shapes start and how many
bytes they take, as two 32 bit numbers; then the tiles. A tile is shapes one after
another: a byte for the kind (LAND, WATER or BORDER), how many points as a 16 bit
number, then each point as two 16 bit numbers, thousandths of a degree east and
north of the tile's south-west corner. Land and water are closed shapes of no more
than MOST points; a border is a line. Shapes are cut a little way past the tile's
edge so neighbours overlap and no seam shows.
"""
import json
import os
import struct
import sys
import urllib.request

from shapely import STRtree
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon, box, shape

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
TILE = 10
# how far past its edge a tile's shapes run, in degrees
LAP = 0.06
# detail finer than this, in degrees, is smoothed away: the map is 8 pixels a degree
FINE = 0.006
# lakes and islands smaller than this, in square degrees, are left out
SMALLEST_LAKE = 0.05
SMALLEST_ISLAND = 0.002
# the most points one shape may have: bigger ones are cut in two
MOST = 600
LAND, WATER, BORDER = 0, 1, 2


def fetch(name):
    path = os.path.join(HERE, "data", name)
    if not os.path.exists(path):
        print("fetching", name)
        request = urllib.request.Request(SOURCE + name, headers={"User-Agent": "artmatrix-santa-tracker land.py"})
        with urllib.request.urlopen(request) as response, open(path, "wb") as out:
            out.write(response.read())
    with open(path) as f:
        return [shape(feature["geometry"]) for feature in json.load(f)["features"]]


def polygons(thing):
    if isinstance(thing, Polygon):
        return [thing] if not thing.is_empty else []
    if isinstance(thing, MultiPolygon) or hasattr(thing, "geoms"):
        return [part for piece in thing.geoms for part in polygons(piece)]
    return []


def lines(thing):
    if isinstance(thing, LineString):
        return [thing] if not thing.is_empty else []
    if isinstance(thing, MultiLineString) or hasattr(thing, "geoms"):
        return [part for piece in thing.geoms for part in lines(piece)]
    return []


def small_enough(polygon):
    """The polygon as pieces of no more than MOST points, cut in two where need be."""
    if len(polygon.exterior.coords) <= MOST:
        return [polygon]
    west, south, east, north = polygon.bounds
    if east - west > north - south:
        middle = (west + east) / 2
        halves = (box(west - 1, south - 1, middle + LAP / 4, north + 1), box(middle - LAP / 4, south - 1, east + 1, north + 1))
    else:
        middle = (south + north) / 2
        halves = (box(west - 1, south - 1, east + 1, middle + LAP / 4), box(west - 1, middle - LAP / 4, east + 1, north + 1))
    return [piece for half in halves for part in polygons(polygon.intersection(half)) for piece in small_enough(part)]


def packed(kind, coords, west, south):
    points = [(round((x - west) * 1000), round((y - south) * 1000)) for x, y in coords]
    # points the rounding has made the same are no use
    kept = [points[0]]
    for point in points[1:]:
        if point != kept[-1]:
            kept.append(point)
    if kind != BORDER and len(kept) > 1 and kept[0] == kept[-1]:
        kept.pop()
    if len(kept) < (2 if kind == BORDER else 3):
        return b""
    return struct.pack(f"<BH{len(kept) * 2}h", kind, len(kept), *[v for point in kept for v in point])


def main(out):
    land = [p.simplify(FINE) for g in fetch("ne_50m_land.geojson") for p in polygons(g)]
    # smoothing can leave a shape crossing itself: buffer(0) mends it
    land = [p if p.is_valid else p.buffer(0) for p in land]
    land = [p for p in land if p.area >= SMALLEST_ISLAND]
    lakes = [p.simplify(FINE) for g in fetch("ne_50m_lakes.geojson") for p in polygons(g) if p.area >= SMALLEST_LAKE]
    borders = [line.simplify(FINE) for g in fetch("ne_50m_admin_0_boundary_lines_land.geojson") for line in lines(g)]
    trees = [(STRtree(group), group) for group in (land, lakes, borders)]

    tiles = []
    counts = [0, 0, 0]
    most_points = 0
    for south in range(-90, 90, TILE):
        for west in range(-180, 180, TILE):
            area = box(west - LAP, south - LAP, west + TILE + LAP, south + TILE + LAP)
            shapes = [[], [], []]
            (land_tree, land_all), (lake_tree, lake_all), (border_tree, border_all) = trees
            for index in land_tree.query(area):
                for part in polygons(land_all[index].intersection(area)):
                    for piece in small_enough(part):
                        shapes[LAND].append(list(piece.exterior.coords))
                        # an inland sea is a hole in the land: painted back in as water
                        for hole in piece.interiors:
                            if Polygon(hole).area >= SMALLEST_LAKE:
                                shapes[WATER].append(list(hole.coords))
            for index in lake_tree.query(area):
                for part in polygons(lake_all[index].intersection(area)):
                    for piece in small_enough(part):
                        shapes[WATER].append(list(piece.exterior.coords))
            for index in border_tree.query(area):
                for line in lines(border_all[index].intersection(area)):
                    coords = list(line.coords)
                    for start in range(0, len(coords) - 1, MOST - 1):
                        shapes[BORDER].append(coords[start:start + MOST])
            data = b""
            for kind in (LAND, WATER, BORDER):
                for coords in shapes[kind]:
                    piece = packed(kind, coords, west, south)
                    if piece:
                        data += piece
                        counts[kind] += 1
                        most_points = max(most_points, struct.unpack_from("<H", piece, 1)[0])
            tiles.append(data)

    header = struct.pack("<4sHH", b"STL1", TILE, 0)
    start = len(header) + 8 * len(tiles)
    with open(out, "wb") as f:
        f.write(header)
        for data in tiles:
            f.write(struct.pack("<II", start, len(data)))
            start += len(data)
        for data in tiles:
            f.write(data)
    print(f"{out}: {start // 1024} kB, {counts[LAND]} land, {counts[WATER]} water, {counts[BORDER]} borders, "
          f"biggest tile {max(map(len, tiles)) // 1024} kB, most points in a shape {most_points}")


if __name__ == "__main__":
    main(sys.argv[1])
