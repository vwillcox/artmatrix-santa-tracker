# Tries the drawing calls the zoomed map needs, and times them. Draws only into
# pictures in memory and the screen: nothing is written to the board's storage.
import math
import time


def timed(label, job):
    start = time.ticks_us()
    try:
        result = job()
        print(label, "ok", time.ticks_diff(time.ticks_us(), start) / 1000, "ms", result if result is not None else "")
    except Exception as error:
        print(label, "FAILED", repr(error))


big = None


def make():
    global big
    big = image(128, 128)


timed("image(128,128)", make)
big.antialias = image.X2
big.pen = color.rgb(8, 26, 92)
timed("clear", big.clear)

for count in (100, 400, 1000):
    points = [vec2(64 + (50 + 8 * math.sin(i * 0.5)) * math.cos(6.283 * i / count), 64 + (50 + 8 * math.sin(i * 0.5)) * math.sin(6.283 * i / count)) for i in range(count)]
    big.pen = color.rgb(38, 150, 84)
    timed(f"custom polygon {count} points", lambda: big.shape(shape.custom(points)))

big.pen = color.rgb(200, 255, 220, 120)
timed("shape.line", lambda: big.shape(shape.line(10, 10, 100, 60, 1)))
timed("image.line 4 args", lambda: big.line(10, 20, 100, 70))
timed("image.line vec2", lambda: big.line(vec2(10, 30), vec2(100, 80)))

with open("/lib/plugins/santa_tracker/clips/globe.clip", "rb") as f:
    f.seek(8)
    import struct
    a, b = struct.unpack("<II", f.read(8))
    f.seek(a)
    jpeg = f.read(b - a)
other = image(128, 128)
timed("image.load_into", lambda: other.load_into(jpeg))
timed("blit whole", lambda: screen.blit(other, 0, 0))
timed("blit scaled up", lambda: screen.blit(other, rect(40, 30, 48, 48), rect(0, 0, 128, 128)))
timed("blit scaled, fractions", lambda: screen.blit(other, rect(40.5, 30.25, 47.5, 47.5), rect(0, 0, 128, 128)))


def faded():
    screen.alpha = 128
    screen.blit(big, 0, 0)
    screen.alpha = 255


timed("blit at half alpha", faded)
with open("/remote/cap/out/probe.raw", "wb") as f:
    f.write(bytes(memoryview(screen)))
print("triangle", [n for n in dir(shape)])
