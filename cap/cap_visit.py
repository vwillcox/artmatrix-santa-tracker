# his visit, as it happens: the map, the swoop in to the roof, the presents going
# down the chimney, the swoop out, and off he goes. pictures are kept in memory and
# written to this computer afterwards. nothing is written to the board's storage
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
home = at(2026, 12, 25, 1, 17, 0)
m.clock = lambda: home - 30
end = time.ticks_add(time.ticks_ms(), 3500)
while m.getting_ready is not None or m.globe is None or time.ticks_diff(end, time.ticks_ms()) > 0:
    m.update()
print("zoom", m.zoom)
# seconds after the clock starts running, 3 seconds before he arrives
SHOTS = (2.6, 3.3, 3.55, 3.8, 5.0, 6.2, 7.0, 7.6, 10.5, 13.5, 16.35, 16.6, 16.85, 17.4, 19.5, 24.0)
kept = [bytearray(128 * 128 * 4) for _ in SHOTS]
start = time.ticks_ms()
m.clock = lambda: home - 3 + time.ticks_diff(time.ticks_ms(), start) // 1000
slowest = 0
for i, when in enumerate(SHOTS):
    while time.ticks_diff(time.ticks_ms(), start) < when * 1000:
        a = time.ticks_us(); m.update(); slowest = max(slowest, time.ticks_diff(time.ticks_us(), a))
    kept[i][:] = memoryview(screen)
print("slowest frame ms", slowest / 1000)
for i, picture in enumerate(kept):
    with open("/remote/cap/out/v%02d.raw" % i, "wb") as f:
        f.write(picture)
print("saved", len(kept))
