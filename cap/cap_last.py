# his last stops before the house, on the closer map: a picture at each of a few
# moments. the pictures are kept in memory and written to this computer afterwards.
# nothing is written to the board's storage
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
# (seconds before he reaches the house, how long to let it run first)
SHOTS = ((660, 1.5), (618, 0.45), (600, 1.5), (560, 1.5), (470, 1.5), (380, 1.5), (290, 1.5), (200, 2.6), (110, 1.5), (40, 1.5), (8, 1.2),
         (-262, 1.2), (-330, 1.5), (-420, 1.5), (-462, 1.5), (-478, 1.5))
kept = [bytearray(128 * 128 * 4) for _ in SHOTS]
m.clock = lambda: home - 700
t = time.ticks_ms()
while m.getting_ready is not None or m.globe is None:
    m.update()
print("ready in ms", time.ticks_diff(time.ticks_ms(), t), "units", m.units)
print([s[2] for s in m.last_stops], [s[2] for s in m.away_stops])
slowest = 0
for i, (before, wait) in enumerate(SHOTS):
    m.clock = lambda before=before: home - before
    end = time.ticks_add(time.ticks_ms(), int(wait * 1000))
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        a = time.ticks_us(); m.update(); slowest = max(slowest, time.ticks_diff(time.ticks_us(), a))
    kept[i][:] = memoryview(screen)
print("slowest frame ms", slowest / 1000)
for i, picture in enumerate(kept):
    with open("/remote/cap/out/l%02d.raw" % i, "wb") as f:
        f.write(picture)
print("saved", len(kept))
