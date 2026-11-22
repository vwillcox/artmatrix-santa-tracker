"""Draws the close-up map for a place on this computer, from land.bin, the way the
plugin does on the board: to check the tiles. cap/map_preview.py LAT LON out.png"""
import math, os, struct, sys
from PIL import Image, ImageDraw
lat0, lon0, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
K = 8; S = 4
kx = K * max(math.cos(math.radians(lat0)), 0.25)
d = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "santa_tracker", "land.bin"), "rb").read()
_, TILE, _ = struct.unpack_from("<4sHH", d, 0)
cols = 360 // TILE
im = Image.new("RGB", (128 * S, 128 * S), (8, 26, 92)); dr = ImageDraw.Draw(im)
def xy(lon, lat):
    return (64 + ((lon - lon0 + 540) % 360 - 180) * kx) * S, (64 - (lat - lat0) * K) * S
half_lon = 64 / kx; half_lat = 64 / K
tiles = set()
for row in range(int((max(lat0 - half_lat, -90) + 90) // TILE), int((min(lat0 + half_lat, 89.99) + 90) // TILE) + 1):
    for c in range(math.floor((lon0 - half_lon + 180) / TILE), math.floor((lon0 + half_lon + 180) / TILE) + 1):
        tiles.add((row, c % cols))
n = 0
for kind_wanted in (0, 1, 2):
    for row, col in sorted(tiles):
        start, size = struct.unpack_from("<II", d, 8 + 8 * (row * cols + col))
        at = start
        while at < start + size:
            kind, count = struct.unpack_from("<BH", d, at); pts = struct.unpack_from(f"<{count * 2}h", d, at + 3); at += 3 + count * 4
            if kind != kind_wanted: continue
            n += count
            p = [xy(col * TILE - 180 + pts[i] / 1000, row * TILE - 90 + pts[i + 1] / 1000) for i in range(0, len(pts), 2)]
            if kind == 0: dr.polygon(p, fill=(38, 150, 84))
            elif kind == 1: dr.polygon(p, fill=(8, 26, 92))
            else: dr.line(p, fill=(150, 220, 170), width=S // 2)
print(len(tiles), "tiles,", n, "points")
im.resize((128, 128), Image.LANCZOS).resize((384, 384), Image.NEAREST).save(out)
