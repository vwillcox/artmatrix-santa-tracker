#!/usr/bin/env python3
"""Packs the world's towns into tiles, for Santa's last few stops before your house.

    python3 tools/towns.py santa_tracker/towns.bin

The route has only a handful of stops in each country. In the last minutes before
he reaches you, the plugin has him call at real towns near your house, each closer
than the last, and needs to know what's near wherever that is.

The towns are GeoNames' cities15000: every place of more than 15,000 people, with
capitals. GeoNames' data is under the Creative Commons Attribution 4.0 licence
(geonames.org), so the plugin's README credits it. It's fetched into tools/data the
first time.

towns.bin is: "STT1", TILE as a 16 bit number, 16 bits spare; then for each tile, row
by row from the south-west corner of the world, where its towns start and how many
bytes they take, as two 32 bit numbers; then the tiles. A town is: thousandths of a
degree east and north of the tile's south-west corner as two 16 bit numbers, its
people in hundreds as a 16 bit number (65535 for more), the length of its name as a
byte, and its name in plain letters.
"""
import io
import os
import struct
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = "https://download.geonames.org/export/dump/cities15000.zip"
TILE = 5
LONGEST = 18


def rows():
    path = os.path.join(HERE, "data", "cities15000.zip")
    if not os.path.exists(path):
        print("fetching cities15000.zip")
        request = urllib.request.Request(SOURCE, headers={"User-Agent": "artmatrix-santa-tracker towns.py"})
        with urllib.request.urlopen(request) as response, open(path, "wb") as out:
            out.write(response.read())
    with zipfile.ZipFile(path) as archive:
        with archive.open("cities15000.txt") as f:
            for line in io.TextIOWrapper(f, encoding="utf-8"):
                yield line.rstrip("\n").split("\t")


def main(out):
    columns, lines = 360 // TILE, 180 // TILE
    tiles = [[] for _ in range(columns * lines)]
    count = 0
    for row in rows():
        # asciiname: the plugin's lettering has no accents
        name = "".join(ch for ch in row[2] if 32 <= ord(ch) < 127).strip()
        if not name or len(name) > LONGEST:
            continue
        lat, lon, people = float(row[4]), float(row[5]), int(row[14] or 0)
        column = min(int((lon + 180) // TILE), columns - 1)
        line = min(int((lat + 90) // TILE), lines - 1)
        east = round((lon + 180 - column * TILE) * 1000)
        north = round((lat + 90 - line * TILE) * 1000)
        tiles[line * columns + column].append(
            struct.pack("<hhHB", east, north, min(people // 100, 65535), len(name)) + name.encode())
        count += 1

    header = struct.pack("<4sHH", b"STT1", TILE, 0)
    start = len(header) + 8 * len(tiles)
    packed = [b"".join(tile) for tile in tiles]
    with open(out, "wb") as f:
        f.write(header)
        for data in packed:
            f.write(struct.pack("<II", start, len(data)))
            start += len(data)
        for data in packed:
            f.write(data)
    print(f"{out}: {count} towns, {start // 1024} kB, biggest tile {max(map(len, packed)) // 1024} kB")


if __name__ == "__main__":
    main(sys.argv[1])
