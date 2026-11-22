import sys, time, gc
sys.path.append("/")
import plugin_config as pc
_real = pc.plugin_config
def forced(name, defaults):
    if name == "santa_tracker":
        return dict(defaults, lat=51.9, lng=0.9, names="Holly, Noel", show="live")
    return _real(name, defaults)
pc.plugin_config = forced
t = time.ticks_ms()
m = __import__("/remote/santa_tracker")
print("import ms", time.ticks_diff(time.ticks_ms(), t))
gc.collect(); print("heap free", gc.mem_free())
def at(*d): return time.mktime(d + (0, 0))
SHOTS = (
    ("01-november", at(2026, 11, 22, 9, 0, 0), 0.5),
    ("02-list", at(2026, 12, 1, 9, 0, 0), 1.7),
    ("03-list-name", at(2026, 12, 1, 9, 0, 0), 8.5),
    ("04-workshop", at(2026, 12, 7, 9, 0, 0), 1.7),
    ("05-practice", at(2026, 12, 12, 9, 0, 0), 1.7),
    ("06-loading", at(2026, 12, 19, 9, 0, 0), 5.5),
    ("07-eve", at(2026, 12, 24, 8, 30, 0), 5.5),
    ("08-takeoff", at(2026, 12, 24, 10, 0, 0), 2.2),
    ("09-flight-asia", at(2026, 12, 24, 15, 0, 30), 0.3),
    ("10-flight-presents", at(2026, 12, 24, 19, 21, 0), 4.5),
    ("11-flight-near", at(2026, 12, 25, 0, 58, 0), 0.3),
    ("12-visit", at(2026, 12, 25, 1, 17, 30), 1.2),
    ("13-visit-magic", at(2026, 12, 25, 1, 17, 30), 3.0),
    ("14-flight-after", at(2026, 12, 25, 4, 42, 0), 8.5),
    ("15-morning", at(2026, 12, 25, 12, 0, 0), 1.0),
    ("16-close-europe", at(2026, 12, 24, 23, 31, 0), 5.0),
    ("17-zooming", at(2026, 12, 25, 1, 16, 0), 2.3),
    ("18-close-home", at(2026, 12, 25, 1, 16, 30), 5.0),
    ("19-close-after", at(2026, 12, 25, 1, 31, 0), 5.0),
)
first, last = [int(v) for v in open("/remote/cap/which.txt").read().split()]
for name, when, wait in SHOTS[first:last]:
    m.clock = lambda when=when: when
    m.update()
    end = time.ticks_add(time.ticks_ms(), int(wait * 1000))
    n = 0; spent = 0
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        a = time.ticks_us(); m.update(); spent += time.ticks_diff(time.ticks_us(), a); n += 1
    with open("/remote/cap/out/" + name + ".raw", "wb") as f:
        f.write(bytes(memoryview(screen)))
    print(name, "frame ms", spent // max(n, 1) / 1000)
