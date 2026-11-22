#!/usr/bin/env python3
"""Turns Google's Santa Tracker route into the two small files the plugin reads.

    python3 tools/route.py tools/data/google_santa_tracker_android_route.json santa_tracker

The route is from github.com/google/santa-tracker-android (Apache License 2.0,
Copyright 2019 Google LLC): tracker/src/androidTest/res/raw/santa.json. It is cut
down here to each stop's name, place, time and presents, which is a change to it.

route.bin is a record a stop, in order: latitude and longitude in hundredths of a
degree, seconds after take-off that Santa arrives, thousands of presents delivered
by the time he leaves, and 1 if it's a major city, as "<hhIIH". He stays STOP seconds
at each. The major cities are the biggest by the route's own population figures,
taken biggest first and skipping any within APART degrees of one already taken, so
the presents the plugin leaves on them don't pile up on the globe.
route.txt is the stops' names, a line each in the same order: "City, Country".
Take-off is the first and landing the last, both at the North Pole.
"""
import json
import math
import struct
import sys
import unicodedata

RECORD = "<hhIIH"
# the most major cities, and how far apart they must be, in degrees round the world
MAJOR = 60
APART = 9


def apart(a, b):
    """Degrees round the world between two stops."""
    la, lb = math.radians(a["location"]["lat"]), math.radians(b["location"]["lat"])
    d = math.radians(a["location"]["lng"] - b["location"]["lng"])
    return math.degrees(math.acos(max(min(math.sin(la) * math.sin(lb) + math.cos(la) * math.cos(lb) * math.cos(d), 1), -1)))


def major_cities(stops):
    chosen = []
    for index in sorted(range(1, len(stops) - 1), key=lambda i: -stops[i]["population"]):
        if all(apart(stops[index], stops[other]) >= APART for other in chosen):
            chosen.append(index)
            if len(chosen) == MAJOR:
                break
    return set(chosen)


def plain(text):
    """As the plugin's font can draw it: Latin letters, accents kept where the font has them."""
    out = []
    for ch in text:
        if ord(ch) < 0x100:
            out.append(ch)
        else:
            out.append(unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode() or "?")
    return "".join(out)


def main(source, folder):
    with open(source) as f:
        stops = json.load(f)["destinations"]
    takeoff = stops[0]["departure"]
    records, names = [], []
    major = major_cities(stops)
    for i, stop in enumerate(stops):
        arrive = 0 if i == 0 else (stop["arrival"] - takeoff) // 1000
        place = stop["location"]
        records.append(struct.pack(RECORD, round(place["lat"] * 100), round(place["lng"] * 100), arrive, stop["presentsDelivered"] // 1000, 1 if i in major else 0))
        region = stop["region"].split(", ")[-1]
        region = {"United States": "USA", "United Kingdom": "UK"}.get(region, region)
        name = plain(stop["city"]) if i in (0, len(stops) - 1) else plain(f'{stop["city"]}, {region}')
        names.append(name)
    with open(f"{folder}/route.bin", "wb") as f:
        f.write(b"".join(records))
    with open(f"{folder}/route.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(names) + "\n")
    last = (stops[-1]["arrival"] - takeoff) // 1000
    print(f"{len(stops)} stops over {last / 3600:.2f} hours, longest name {max(names, key=len)!r}")
    print("major:", ", ".join(stops[i]["city"] for i in sorted(major)))
    print("non-ascii:", sorted({ch for name in names for ch in name if ord(ch) > 126}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
