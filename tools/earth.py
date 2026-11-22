#!/usr/bin/env python3
"""Paints the map the globe wears: the world asleep, with its cities lit.

    uv run --with pillow --with numpy tools/earth.py tools/data/earth.png

Land, lakes and cities are Natural Earth's 1:110m data, which is in the public
domain (naturalearthdata.com). The picture is the whole world, longitude across
and latitude down, 4096 x 2048.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
WIDE, HIGH = 4096, 2048
CITIES = 150


def spot(lon, lat):
    return (lon + 180) / 360 * WIDE, (90 - lat) / 180 * HIGH


def rings(name):
    with open(os.path.join(HERE, "data", name)) as f:
        for feature in json.load(f)["features"]:
            shape = feature["geometry"]
            polygons = shape["coordinates"] if shape["type"] == "MultiPolygon" else [shape["coordinates"]]
            for polygon in polygons:
                yield [spot(lon, lat) for lon, lat in polygon[0]]


def main(out):
    mask = Image.new("L", (WIDE, HIGH), 0)
    draw = ImageDraw.Draw(mask)
    for ring in rings("ne_110m_land.geojson"):
        draw.polygon(ring, fill=255)
    for ring in rings("ne_110m_lakes.geojson"):
        draw.polygon(ring, fill=0)
    land = np.asarray(mask, dtype=np.float32)[..., None] / 255
    # a pale edge to the land, so the coast shows on a small globe
    shore = np.asarray(mask.filter(ImageFilter.GaussianBlur(10)), dtype=np.float32)[..., None] / 255

    lat = np.linspace(90, -90, HIGH, dtype=np.float32)[:, None, None]
    north = np.clip((lat - 56) / 14, 0, 1)
    south = np.clip((-lat - 58) / 6, 0, 1)
    snow = np.maximum(north, south)
    dry = np.exp(-((np.abs(lat) - 23) / 9) ** 2) * 0.35
    green = np.array([38, 150, 84], dtype=np.float32)
    sand = np.array([150, 150, 80], dtype=np.float32)
    white = np.array([226, 236, 255], dtype=np.float32)
    ground = green * (1 - dry) + sand * dry
    ground = ground * (1 - snow) + white * snow
    deep = np.array([8, 26, 92], dtype=np.float32)
    shallow = np.array([24, 70, 160], dtype=np.float32)
    sea = deep + (shallow - deep) * np.clip(shore * 2.2, 0, 1)
    # sea ice round the north pole
    ice = np.clip((lat - 78) / 6, 0, 1)
    sea = sea * (1 - ice) + white * ice
    picture = sea * (1 - land) + ground * land

    with open(os.path.join(HERE, "data", "ne_110m_populated_places_simple.geojson")) as f:
        places = [p["properties"] for p in json.load(f)["features"]]
    places.sort(key=lambda p: -(p.get("pop_max") or 0))
    lights = Image.new("L", (WIDE, HIGH), 0)
    draw = ImageDraw.Draw(lights)
    for place in places[:CITIES]:
        x, y = spot(place["longitude"], place["latitude"])
        r = 7 + min((place.get("pop_max") or 0) / 4e6, 4)
        # wider towards the poles, where the map is stretched
        stretch = 1 / max(np.cos(np.radians(place["latitude"])), 0.3)
        draw.ellipse((x - r * stretch, y - r, x + r * stretch, y + r), fill=255)
    glow = np.asarray(lights.filter(ImageFilter.GaussianBlur(4)), dtype=np.float32)[..., None] / 255
    gold = np.array([255, 214, 110], dtype=np.float32)
    picture = picture * (1 - glow) + gold * glow

    Image.fromarray(np.clip(picture, 0, 255).astype(np.uint8)).save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
