# the zoom in to the map and back out, a picture every 150 ms. the pictures are kept
# in memory and written to this computer afterwards, so saving them doesn't hold the
# zoom up. nothing is written to the board's storage
import sys, time
sys.path.append("/")
import plugin_config as pc
_real = pc.plugin_config
def forced(name, defaults):
    if name == "santa_tracker":
        return dict(defaults, lat=51.9, lng=0.9, names="Holly, Noel", show="live")
    return _real(name, defaults)
pc.plugin_config = forced
m = __import__("/remote/santa_tracker")
def at(*d): return time.mktime(d + (0, 0))
EACH = 7
kept = [bytearray(128 * 128 * 4) for _ in range(EACH * 2)]
far = at(2026, 12, 25, 1, 5, 0)
near = at(2026, 12, 25, 1, 16, 30)
# on the globe until the map has been drawn
m.clock = lambda: far
while not m.local is not None and m.local.ready:
    m.update()
print("map drawn, zoom", m.zoom)
n = 0
for when in (near, far):
    m.clock = lambda when=when: when
    start = time.ticks_ms()
    for i in range(EACH):
        while time.ticks_diff(time.ticks_ms(), start) < 80 + i * 150:
            m.update()
        m.update()
        kept[n][:] = memoryview(screen)
        n += 1
    end = time.ticks_add(time.ticks_ms(), 600)
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        m.update()
    print("zoom now", m.zoom, "close", m.close)
for i, picture in enumerate(kept):
    with open("/remote/cap/out/z%02d.raw" % i, "wb") as f:
        f.write(picture)
print("saved", n)
