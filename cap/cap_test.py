# the pretend mode, as the settings page would set it: from 15 minutes before the
# visit at ten minutes a second, a picture every so often
import sys, time
sys.path.append("/")
import plugin_config as pc
_real = pc.plugin_config
def forced(name, defaults):
    if name == "santa_tracker":
        return dict(defaults, lat=51.9, lng=0.9, names="Holly, Noel", show="pretend", pretend="2026-12-25T01:02", speed=600)
    return _real(name, defaults)
pc.plugin_config = forced
m = __import__("/remote/santa_tracker")
print("testing", m.testing, "visit", m.visit_local, m.visit_place)
start = time.ticks_ms()
for name, until in (("t1-pretend-globe", 0.8), ("t2-pretend-visit", 4.0), ("t3-pretend-after", 11.5)):
    while time.ticks_diff(time.ticks_ms(), start) < until * 1000:
        m.update()
    with open("/remote/cap/out/" + name + ".raw", "wb") as f:
        f.write(bytes(memoryview(screen)))
    now = m.clock()
    print(name, time.gmtime(int(now))[2:6], m.plan(now)[0])
