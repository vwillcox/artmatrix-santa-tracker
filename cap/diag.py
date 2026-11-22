# runs the plugin with the board's own saved settings and reports what its clock and
# its plan are doing. nothing is written to the board's storage
import sys, time
sys.path.append("/")
m = __import__("/remote/santa_tracker")
print("show", m.show, "pretend", repr(m.cfg["pretend"]), "speed", m.speed, "units", m.units)
print("has location", m.location is not None, "home stop", m.places[m.home_stop] if m.home_stop is not None else None)
go = m.takeoff_of(2026)
print("home_after", m.home_after, "types", type(m.pretend_from), type(m.clock()), "pretend_from - home", None if m.pretend_from is None else m.pretend_from - go - m.home_after)
print("spells", [(u - go - m.home_after, r) for u, r in m.spells])
# from 8 seconds before he arrives, on the pretend clock as the settings page sets it
m.pretend_from = go + m.home_after - 8
m.started = time.ticks_ms()
start = time.ticks_ms()
last = None
while time.ticks_diff(time.ticks_ms(), start) < 30000:
    m.update()
    now = m.clock()
    key, scenes, sleeps, since = m.plan(now)
    line = (key, int(since - m.home_after) // 5 * 5, int(m.zoom), m.close, m.local is not None and m.local.ready)
    if line != last:
        last = line
        print(time.ticks_diff(time.ticks_ms(), start) // 1000, "s:", line, "last_from", None if m.last_from is None else m.last_from - m.home_after, "stops", len(m.last_stops), len(m.away_stops))
