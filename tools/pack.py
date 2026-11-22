#!/usr/bin/env python3
"""Shrinks Blender's frames to the panel's 128 x 128 and packs them for the plugin.

    uv run --with pillow --with numpy tools/pack.py clip <frames folder> <out.clip> [--fps 12]
    uv run --with pillow --with numpy tools/pack.py globe <frames folder> <out.clip>
    uv run --with pillow --with numpy tools/pack.py sprite <frames folder> <out.png>

A .clip is: "STC1", the frames a second x100 and the number of frames as two 16 bit
numbers, where each frame starts as 32 bit numbers with one more for the end, then
the frames, each a JPEG. Knowing where each starts lets the plugin show any of them,
which is how the globe turns to wherever Santa is.
"""
import io
import os
import random
import struct
import sys

import numpy as np
from PIL import Image, ImageFilter

SIZE = 128
QUALITY = 84
# where the globe sits on the plugin's picture, and how big. the plugin has the same
GLOBE_AT = (64, 61)
GLOBE_RADIUS = 44
SPRITE_WIDE = 34


def frames(folder):
    return [os.path.join(folder, name) for name in sorted(os.listdir(folder)) if name.endswith(".png")]


def bloom(picture, over=0.72, spread=9, much=0.9):
    """Lets the bright parts spill light, as lit things do."""
    a = np.asarray(picture, dtype=np.float32) / 255
    bright = np.clip(a - over, 0, 1) / (1 - over)
    halo = Image.fromarray((bright * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(spread))
    wide = Image.fromarray((bright * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(spread * 3))
    a = a + much * 0.6 * np.asarray(halo, dtype=np.float32) / 255 + much * 0.5 * np.asarray(wide, dtype=np.float32) / 255
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def write_clip(pictures, out, fps):
    packed = []
    for picture in pictures:
        data = io.BytesIO()
        picture.save(data, "JPEG", quality=QUALITY, subsampling=0, optimize=True)
        packed.append(data.getvalue())
    start = 8 + 4 * (len(packed) + 1)
    with open(out, "wb") as f:
        f.write(struct.pack("<4sHH", b"STC1", round(fps * 100), len(packed)))
        for data in packed:
            f.write(struct.pack("<I", start))
            start += len(data)
        f.write(struct.pack("<I", start))
        for data in packed:
            f.write(data)
    print(f"{out}: {len(packed)} frames, {start // 1024} kB, biggest {max(map(len, packed))} bytes")


def clip(folder, out, fps=12):
    write_clip([bloom(Image.open(path).convert("RGB")).resize((SIZE, SIZE), Image.LANCZOS) for path in frames(folder)], out, fps)


def globe(folder, out):
    """Each view of the world goes on the same starry sky, with a haze of air round it."""
    big = Image.open(frames(folder)[0]).size[0]
    k = big / SIZE
    y, x = np.mgrid[0:big, 0:big].astype(np.float32)
    # the render has the world in the middle: it moves to GLOBE_AT
    shift = (round((GLOBE_AT[0] - SIZE / 2) * k), round((GLOBE_AT[1] - SIZE / 2) * k))
    away = np.hypot(x - GLOBE_AT[0] * k, y - GLOBE_AT[1] * k) / k - GLOBE_RADIUS
    disc = np.clip(0.5 - away * k, 0, 1)[..., None]
    haze = (np.exp(-np.clip(away, 0, None) / 3.5) * 0.75)[..., None] * np.array([70, 140, 255], dtype=np.float32)
    rng = random.Random(24)
    sky = np.zeros((big, big, 3), dtype=np.float32)
    sky += np.array([3, 5, 22], dtype=np.float32)
    for _ in range(70):
        sx, sy = rng.randrange(SIZE), rng.randrange(SIZE)
        level = rng.choice((70, 110, 160, 230))
        sky[int(sy * k):int((sy + 1) * k), int(sx * k):int((sx + 1) * k)] = (level, level, min(level + 25, 255))
    behind = sky + haze
    pictures = []
    for path in frames(folder):
        world = np.roll(np.asarray(Image.open(path).convert("RGB"), dtype=np.float32), (shift[1], shift[0]), axis=(0, 1))
        # brighter towards the rim, as air is
        rim = np.clip(1 + away / GLOBE_RADIUS, 0, 1)[..., None] ** 6 * 0.5 * np.array([70, 140, 255], dtype=np.float32)
        a = (world + rim) * disc + behind * (1 - disc)
        pictures.append(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS))
    write_clip(pictures, out, 12)


def sprite(folder, out, wide=None):
    """The sleigh's frames side by side, cut to their shape and shrunk to SPRITE_WIDE:
    first each step of the gallop heading left, then the same steps heading right."""
    shots = [Image.open(path).convert("RGBA") for path in frames(folder)]
    box = None
    for shot in shots:
        b = shot.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    wide = wide or SPRITE_WIDE
    high = round(wide * (box[3] - box[1]) / (box[2] - box[0]))
    sheet = Image.new("RGBA", (wide * len(shots) * 2, high), (0, 0, 0, 0))
    for i, shot in enumerate(shots):
        small = shot.crop(box).resize((wide, high), Image.LANCZOS)
        # a firmer edge than the shrink leaves, and a little more colour: it's tiny
        r, g, b, a = small.split()
        a = a.point(lambda v: 0 if v < 70 else min(int(v * 1.5), 255))
        small = Image.merge("RGBA", (r, g, b, a))
        sheet.paste(small, (i * wide, 0))
        sheet.paste(small.transpose(Image.FLIP_LEFT_RIGHT), ((len(shots) + i) * wide, 0))
    sheet.save(out)
    print(f"{out}: {len(shots)} frames each way, of {wide} x {high}")


if __name__ == "__main__":
    kind, folder, out = sys.argv[1:4]
    if kind == "clip":
        clip(folder, out, float(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 12)
    elif kind == "globe":
        globe(folder, out)
    else:
        # --wide N makes a smaller one, for the close-up map
        sprite(folder, out, int(sys.argv[sys.argv.index("--wide") + 1]) if "--wide" in sys.argv else None)
