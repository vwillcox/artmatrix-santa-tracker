"""Renders the Santa Tracker's scenes in Blender.

    blender -b -P tools/scenes.py -- <scene> <folder> [--frames 0,12,24] [--size 512]

Each scene is a function that builds its set from kit.py and returns how many frames
it runs for and a function that poses everything for a point t in the loop, 0 to 1.
Every movement goes round a whole number of times in the loop, so the last frame
runs into the first. Frames are saved as PNGs, for pack.py to shrink and pack.
"""
import math
import os
import random
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
from kit import *  # noqa: E402,F403

TAU = 2 * math.pi


def wave(t, times=1, phase=0.0):
    return math.sin(TAU * (times * t + phase))


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def between(t, start, end):
    """0 before start, 1 after end, eased in between."""
    return ease((t - start) / (end - start))


def degrees(*angles):
    return [math.radians(a) for a in angles]


# ---- the north pole, from outside -------------------------------------------------


def pole():
    sky("#040820", "#16306c")
    ground("#b9c9ee")
    drifts(((-4.5, 3, 3, 0.9), (4.8, 4, 3.5, 1.1), (0, 7, 6, 1.4), (-2.6, -1.6, 1.3, 0.3), (3.4, -1.2, 1.5, 0.3)))
    _, glass = cabin((-0.9, 2.2, 0), wide=3.4, deep=2.4, tall=1.8)
    candy_pole((2.3, 0.3, 0), 2.7)
    bulbs = tree((3.9, 2.2, 0), 3.0, lights=10, star=True, seed=4)
    tree((-3.9, 3.6, 0), 3.6, seed=2)
    tree((-3.0, 4.6, 0), 2.6, seed=2)
    man = snowman((-2.9, -0.3, 0), size=0.8, turn=(0, 0, 20))
    star_list = stars(70)
    moon((-5.0, 20, 11.5), 1.3)
    curtains = [aurora((-2, 21, 5.5), 30, 7, "#2ff5a0", 2.0, 0.0, 2.2), aurora((3, 23, 7.5), 30, 6, "#4aa8ff", 1.5, 2.0, 1.6),
                aurora((0, 22, 8.5), 30, 5, "#c05cff", 1.0, 4.0, 1.0)]
    snow = snowfall(60, region=((-6, 6), (-3, 6), (0, 7)))
    puffs = [ball(mat("#dfe6f5", 0.9), (0, 0, 0), 0.2) for _ in range(5)]

    light("SUN", (0, 0, 10), 1.6, "#9db8ff", 4, aim=(3, 6, 0))
    light("POINT", (-0.9, 0.2, 1.2), 260, WARM, 0.6)
    light("POINT", (3.6, 0.6, 2.2), 60, "#ffd9a0", 0.5)
    camera((0.3, -11.5, 3.3), (0.3, 1.5, 2.2), lens=52)

    def pose(t):
        twinkle(star_list, t)
        for curtain in curtains:
            sway(curtain, t)
        fall(snow, t)
        for i, m in enumerate(bulbs):
            glow_of(m, 3.5 + 3.0 * wave(t, 2, i * 0.37))
        glow_of(glass, 3.4 + 0.5 * wave(t, 3))
        for i, puff in enumerate(puffs):
            p = (t + i / len(puffs)) % 1.0
            size = 0.12 + 0.3 * p if p < 0.8 else (0.36) * (1 - p) / 0.2
            puff.location = (0.12 + 0.5 * p * p + 0.08 * wave(p, 1, i * 0.2), 2.4, 3.45 + 2.3 * p)
            puff.scale = (size, size, size)
        man["head"].rotation_euler = degrees(0, 6 * wave(t), 10 * wave(t))

    return 48, pose


def outdoors(aurora_strength=1.0, star_count=60):
    """The night the outdoor scenes share. Returns a function that moves it on."""
    sky("#040820", "#16306c")
    star_list = stars(star_count)
    curtains = [aurora((-2, 21, 6.5), 30, 6, "#2ff5a0", 2.0, 0.0, 1.5 * aurora_strength),
                aurora((3, 23, 8.5), 30, 5, "#4aa8ff", 1.5, 2.0, 1.1 * aurora_strength)]

    def move(t):
        twinkle(star_list, t)
        for curtain in curtains:
            sway(curtain, t)
    return move


# ---- checking the list ------------------------------------------------------------


def checking():
    room()
    fire = fireplace((-2.9, 2.6, 0))
    window((2.6, 2.95, 2.7))
    bulbs = string_lights((-1.2, 2.9, 4.3), (4.6, 2.9, 4.3), 12, 0.5)
    man = santa((0.5, 0.4, 0), size=1.05)
    # reading glasses
    for side in (-1, 1):
        ring(GOLD, (side * 0.14, -0.37, 0.1), 0.085, 0.014, man["head"], turn=(90, 0, 0))
    helper = elf((-1.5, -1.0, 0), turn=(0, 0, 35), size=0.95)

    # the list: held at his chest, down to the floor and away across the rug
    paper = mat("#f7ecd0", 0.8)
    top = 1.62
    box(paper, (0.5, -0.42, top / 2 + 0.02), (0.95, 0.03, top), round=0)
    box(paper, (0.5, -1.45, 0.05), (0.95, 2.1, 0.03), round=0)
    cone(paper, (0.02, -0.42, top), 0.09, 0.09, 0.96, turn=(0, 90, 0), sides=12)
    cone(paper, (0.02, -2.5, 0.12), 0.12, 0.12, 0.96, turn=(0, 90, 0), sides=12)
    for x in (-0.03, 1.03):
        ball(GOLD, (x, -0.42, top), 0.07)
        ball(GOLD, (x, -2.5, 0.12), 0.08)
    ticks = []
    rows = 8
    for i in range(rows):
        z = top - 0.2 - i * 0.165
        box("#5a4630", (0.6, -0.44, z), (0.5, 0.02, 0.05), round=0)
        tick = ball(mat("#22c55e", 0.4, 2.5), (0.2, -0.45, z), 0.055)
        ticks.append(tick)
    for i in range(6):
        box("#5a4630", (0.6, -0.75 - i * 0.26, 0.07), (0.5, 0.05, 0.02), round=0)
        ball(mat("#22c55e", 0.4, 2.5), (0.2, -0.75 - i * 0.26, 0.07), 0.055)
    # a quill in his right hand
    quill = group((0, 0, -0.62), man["arms"][0])
    cone(WHITE, (0, 0, 0), 0.02, 0.07, 0.5, quill, turn=(-60, 0, 0), sides=6, size=(1, 0.3, 1))

    light("AREA", (2, -5, 5), 700, "#ffe2b8", 5, aim=(0, 0, 1))
    light("POINT", (3.5, -1, 3.5), 150, "#8fb0ff", 1.0)
    camera((0, -9.5, 2.5), (0, 0, 1.55), lens=50)

    def pose(t):
        flicker(fire, t)
        blink(bulbs, t)
        # the ticks go down the list, then he starts again: checking it twice
        done = int(t * (rows + 2))
        for i, tick in enumerate(ticks):
            k = 0.055 if i < done else 0.0001
            tick.scale = (k, k, k)
        reach = (t * (rows + 2)) % 1.0
        dab = math.sin(math.pi * reach)
        man["arms"][0].rotation_euler = degrees(-58 - 12 * dab, -8, 0)
        man["arms"][1].rotation_euler = degrees(-62, 10, 0)
        man["head"].rotation_euler = degrees(10 + 4 * wave(t, 2), 0, 6 * wave(t, 1))
        man["body"].location = (0, 0, 0.02 * wave(t, 2))
        helper["head"].rotation_euler = degrees(-12, 0, 10 * wave(t, 2))
        helper["arms"][1].rotation_euler = degrees(-70 + 15 * wave(t, 4), 30, 0)
        helper["root"].location = (-1.5, -1.0, 0.06 * abs(wave(t, 2)))

    return 48, pose


# ---- the workshop -----------------------------------------------------------------


def workshop():
    room("#6f4428", "#4f2f1c", rug=None)
    window((-3.2, 2.95, 3.0), 1.3, 1.3)
    bulbs = string_lights((-5, 2.9, 4.5), (5, 2.9, 4.5), 16, 0.5)
    # shelves of toys along the back wall
    rng = random.Random(8)
    for z in (2.0, 3.1):
        box(DARK_BROWN, (1.6, 2.75, z), (4.6, 0.5, 0.1), round=0.02)
        for i in range(7):
            x = -0.4 + i * 0.66
            colour = (RED, BLUE, GOLD, GREEN, PURPLE, ORANGE)[rng.randrange(6)]
            kind = rng.randrange(3)
            if kind == 0:
                ball(colour, (x, 2.7, z + 0.27), 0.22)
            elif kind == 1:
                box(colour, (x, 2.7, z + 0.25), (0.36, 0.36, 0.4))
            else:
                cone(colour, (x, 2.7, z + 0.05), 0.2, 0.0, 0.5, sides=12)
    # the bench, with a belt running along it
    box(BROWN, (0, -0.3, 0.95), (9, 1.3, 0.16), round=0.04)
    for x in (-3.4, 0, 3.4):
        box(DARK_BROWN, (x, -0.3, 0.45), (0.2, 1.1, 0.9), round=0.03)
    box("#2b2b36", (0, -0.55, 1.05), (9, 0.6, 0.06), round=0.01)
    gap = 1.5
    moving = []
    for i in range(7):
        if i % 2:
            item = present((0, -0.55, 1.08), 0.42, PRESENT_COLOURS[i % 6])
        else:
            # a toy train engine, not yet wrapped
            item = group((0, -0.55, 1.08))
            box((BLUE, RED, GREEN)[i % 3], (0, 0, 0.2), (0.5, 0.3, 0.26), item, round=0.04)
            box(GOLD, (0.14, 0, 0.42), (0.2, 0.28, 0.22), item, round=0.03)
            cone(BLACK, (-0.14, 0, 0.3), 0.06, 0.08, 0.22, item, sides=10)
            for wx in (-0.15, 0.15):
                cone(BLACK, (wx, -0.16, 0.09), 0.09, 0.09, 0.04, item, turn=(90, 0, 0), sides=12)
        moving.append(item)
    stripes = [box("#55556a", (0, -0.86, 1.06), (0.08, 0.03, 0.05), round=0) for _ in range(12)]

    elves = [elf((-1.7, 0.75, 0), size=1.15), elf((1.5, 0.75, 0), size=1.15, coat=RED, trim=GREEN), elf((4.3, 0.9, 0), size=1.1, coat=BLUE, trim=GOLD)]
    for worker in elves[:2]:
        hammer = group((0, 0, -0.4), worker["arms"][0])
        cone(DARK_BROWN, (0, 0, -0.05), 0.03, 0.03, 0.4, hammer, turn=(-90, 0, 0), sides=8)
        box("#9aa0b0", (0, -0.4, -0.05), (0.26, 0.14, 0.14), hammer, round=0.03)
    hits = sparkles(10, GOLD, 9.0)

    light("AREA", (0, -5, 6), 900, "#ffdcae", 6, aim=(0, 0, 1))
    light("POINT", (-4.5, -1, 3), 200, "#ff9a3c", 1.0)
    light("POINT", (4.5, 0, 3), 160, "#8fb0ff", 1.0)
    camera((0, -9.5, 3.0), (0, 0, 1.75), lens=50)

    def pose(t):
        blink(bulbs, t)
        for i, item in enumerate(moving):
            item.location.x = -5.25 + ((i * gap + t * gap * 2) % (len(moving) * gap))
        for i, stripe in enumerate(stripes):
            stripe.location.x = -4.5 + ((i * 0.75 + t * gap * 2) % 9.0)
        for n, worker in enumerate(elves[:2]):
            swing = (2 * t + n * 0.5) % 1.0
            down = math.sin(math.pi * min(swing / 0.35, 1.0)) if swing < 0.35 else 0
            worker["arms"][0].rotation_euler = degrees(-95 + 60 * (1 - down) * -1 + 60, -10, 0)
            worker["arms"][0].rotation_euler = degrees(-130 + 75 * down, -10, 0)
            worker["arms"][1].rotation_euler = degrees(-50, 15, 0)
            worker["head"].rotation_euler = degrees(8 + 6 * down, 0, 5 * wave(t, 1, n * 0.3))
            worker["root"].location.z = 0.05 * down
            for j, (s, a, b, c) in enumerate(hits[n * 5:n * 5 + 5]):
                age = (swing - 0.17) / 0.4
                k = 0.07 * (1 - age) if 0 <= age < 1 else 0.0001
                x = (-1.7, 1.5)[n] - 0.35
                s.location = (x + (a - 0.5) * 1.3 * age, -0.5 - 0.3 * b * age, 1.5 + 0.9 * age * c - 0.6 * age * age)
                s.scale = (k, k, k)
        carrier = elves[2]
        carrier["root"].location.z = 0.12 * abs(wave(t, 2))
        carrier["arms"][0].rotation_euler = degrees(-170 + 20 * wave(t, 2), -20, 0)
        carrier["arms"][1].rotation_euler = degrees(-170 - 20 * wave(t, 2), 20, 0)
        carrier["head"].rotation_euler = degrees(0, 0, 14 * wave(t, 2))

    return 48, pose


# ---- flying practice --------------------------------------------------------------


def practice():
    sky_move = outdoors(0.8)
    ground("#b9c9ee")
    drifts(((-5, 5, 4, 1.2), (5, 6, 5, 1.5), (0, 9, 7, 1.6), (3.6, -1.6, 1.4, 0.3)))
    tree((5.0, 4.0, 0), 3.4, seed=2)
    tree((-5.3, 4.6, 0), 3.0, seed=3)
    fence((-6, 2.6), (6, 2.6), 9)
    # a barn at the back
    cabin((-2.6, 5.4, 0), wide=3.0, deep=2.2, tall=1.9, wall="#8c2f2a", chimney=False)
    rudolph = reindeer((-0.9, 0.2, 0), size=1.25, red_nose=True)
    learner = reindeer((2.5, 1.2, 0), size=1.1)
    coach = elf((-3.1, -0.6, 0), turn=(0, 0, 60), size=1.05, coat=BLUE, trim=GOLD)
    flag = group((0, 0, -0.4), coach["arms"][0])
    cone(DARK_BROWN, (0, 0, -0.5), 0.02, 0.02, 0.6, flag, sides=6)
    box(mat(GOLD, 0.5, 1.0), (0.16, 0, -0.44), (0.3, 0.02, 0.2), flag, round=0.01)
    dust = sparkles(18, GOLD, 9.0)
    snow = snowfall(40, region=((-6, 6), (-3, 5), (0, 7)))

    light("SUN", (0, 0, 10), 1.8, "#9db8ff", 4, aim=(3, 6, 0))
    light("POINT", (-1.5, -2.5, 2.5), 300, "#ffd9a0", 1.0)
    nose = light("POINT", (-2.2, 0.1, 2.2), 40, "#ff3030", 0.3, shadow=False)
    camera((0, -11.5, 2.9), (0.2, 1.0, 2.0), lens=52)

    def pose(t):
        sky_move(t)
        fall(snow, t)
        # rudolph lifts off, hangs in the air galloping, and comes back down
        up = between(t, 0.08, 0.35) - between(t, 0.7, 0.95)
        height = 1.6 * up + 0.1 * wave(t, 3) * up
        rudolph["root"].location = (-0.9, 0.2, height)
        rudolph["root"].rotation_euler = degrees(0, 8 * up * wave(t, 1, 0.1), 0)
        gallop(rudolph, 3 * t)
        glow_of(rudolph["nose"], 3 + 6 * up + 2 * wave(t, 4))
        nose.location = (-2.2, 0.1, 1.9 + height)
        nose.data.energy = 30 + 90 * up
        trail(dust, t, (-0.7, 0.2, height + 0.25), back=(0.0, 0, -1), long=max(height, 0.01), spread=1.3, times=3, size=0.075 * (0.2 + up))
        # the learner only manages hops
        hop = abs(wave(t, 2, 0.1))
        learner["root"].location = (2.5, 1.2, 0.35 * hop)
        gallop(learner, 2 * t + 0.3)
        learner["head"].rotation_euler = degrees(0, 32 - 14 * up, 0)
        coach["arms"][0].rotation_euler = degrees(-150 + 25 * wave(t, 4), -25, 0)
        coach["arms"][1].rotation_euler = degrees(-120 * up, 25, 0)
        coach["root"].location.z = 0.1 * abs(wave(t, 4)) * up
        coach["head"].rotation_euler = degrees(-20 * up, 0, 0)

    return 48, pose


# ---- loading the sleigh -----------------------------------------------------------


def loading():
    sky_move = outdoors(0.8)
    ground("#b9c9ee")
    drifts(((-5, 6, 4, 1.2), (5, 7, 5, 1.5), (0, 10, 7, 1.6)))
    _, glass = cabin((3.4, 5.2, 0), wide=3.4, deep=2.4, tall=1.9)
    candy_pole((-4.6, 3.4, 0), 2.8)
    tree((-3.0, 5.0, 0), 3.2, seed=2)
    rig = group((-0.6, 0.6, 0))
    sled = sleigh(parent=rig, driver=False, loaded=True, size=1.15)
    deer = reindeer((-4.6, 0.6, 0), size=1.1, red_nose=True)
    cone(DARK_BROWN, (-3.9, 0.45, 1.25), 0.02, 0.02, 2.0, turn=(0, 90, 0), sides=6)
    boss = santa((3.9, -1.3, 0), turn=(0, 0, -35), size=0.95)
    throwers = [elf((2.3, 0.3, 0), turn=(0, 0, -70), size=1.0), elf((3.2, 1.4, 0), turn=(0, 0, -60), size=1.0, coat=RED, trim=GREEN)]
    pile((4.6, 1.2, 0), 7, seed=3, spread=1.1, size=0.6)
    flying = [present((0, 0, 0), 0.42, PRESENT_COLOURS[i]) for i in (0, 2, 3, 4)]
    glints = sparkles(8, GOLD, 9.0)
    snow = snowfall(40, region=((-6, 6), (-3, 5), (0, 7)))

    light("SUN", (0, 0, 10), 1.8, "#9db8ff", 4, aim=(3, 6, 0))
    light("POINT", (0.5, -3, 3), 420, "#ffd9a0", 1.2)
    light("POINT", (3.4, 3.2, 1.3), 200, WARM, 0.6)
    camera((0.9, -12.5, 3.0), (0.9, 1.0, 1.9), lens=50)

    def pose(t):
        sky_move(t)
        fall(snow, t)
        glow_of(glass, 3.4 + 0.5 * wave(t, 3))
        for i, gift in enumerate(flying):
            p = (t * 2 + i / len(flying)) % 1.0
            start = (2.0, 0.3, 1.5) if i % 2 == 0 else (2.9, 1.4, 1.5)
            end = (0.15, 0.6, 1.75)
            fly = min(p / 0.7, 1.0)
            gift.location = (start[0] + (end[0] - start[0]) * fly, start[1] + (end[1] - start[1]) * fly, start[2] + (end[2] - start[2]) * fly + 2.2 * fly * (1 - fly))
            gift.rotation_euler = degrees(360 * fly, 200 * fly, 90 * fly)
            k = 1.0 if p < 0.7 else max(1 - (p - 0.7) / 0.08, 0.001)
            gift.scale = (k, k, k)
        for n, thrower in enumerate(throwers):
            p = (t * 2 + n * 0.25) % 0.5 / 0.5
            fling = math.sin(math.pi * min(p / 0.4, 1.0))
            for arm, side in zip(thrower["arms"], (-1, 1)):
                arm.rotation_euler = degrees(-60 - 100 * fling, side * 12, 0)
            thrower["root"].location.z = 0.1 * fling
        # the sleigh settles a little each time a present lands
        land = (t * 8) % 1.0
        sled["body"].location.z = 0.42 * 1.0 - 0.04 * math.exp(-6 * land) * math.sin(TAU * land * 2)
        for j, (s, a, b, c) in enumerate(glints):
            k = 0.06 * math.exp(-5 * land) * (0.5 + a)
            s.location = (-0.45 + (a - 0.5) * 1.2, 0.2 + (b - 0.5), 2.5 + c * 0.6 + land * 0.5)
            s.scale = (k, k, k)
        boss["head"].rotation_euler = degrees(0, 0, 8 * wave(t, 2))
        boss["arms"][0].rotation_euler = degrees(-25 + 6 * wave(t, 2), -40, 0)
        boss["arms"][1].rotation_euler = degrees(-140 + 14 * wave(t, 4), 20, 0)
        boss["body"].location.z = 0.03 * wave(t, 4)
        deer["head"].rotation_euler = degrees(0, 32 + 10 * wave(t, 1), 0)
        glow_of(deer["nose"], 4 + 2 * wave(t, 2))

    return 48, pose


# ---- off he goes ------------------------------------------------------------------


def takeoff():
    sky_move = outdoors(1.0, 70)
    ground("#b9c9ee")
    drifts(((-5, 6, 4, 1.2), (5, 7, 5, 1.5), (0, 10, 7, 1.6)))
    moon((5.5, 20, 12.5), 1.5)
    _, glass = cabin((4.6, 6.5, 0), wide=3.0, deep=2.2, tall=1.6)
    candy_pole((-5.2, 4.5, 0), 2.6)
    tree((6.6, 4.4, 0), 3.0, lights=8, star=True, seed=4)
    tree((-3.4, 6.2, 0), 3.0, seed=2)
    wavers = [elf((3.2, -1.2, 0), turn=(0, 0, 150), size=0.95), elf((4.4, -0.4, 0), turn=(0, 0, 160), size=0.9, coat=RED, trim=GREEN),
              elf((-4.6, -1.0, 0), turn=(0, 0, -150), size=0.95, coat=BLUE, trim=GOLD)]
    rig = group((0, 0, 0), size=0.72)
    sled = sleigh(parent=rig)
    deer = team(rig, 2)
    dust = sparkles(34, GOLD, 10.0)
    snow = snowfall(40, region=((-7, 7), (-3, 5), (0, 9)))

    light("SUN", (0, 0, 10), 1.8, "#9db8ff", 4, aim=(3, 6, 0))
    key = light("POINT", (0, -3, 3), 300, "#ffe2b8", 1.5)
    camera((0, -13.5, 3.2), (0, 1.0, 3.6), lens=46)

    def pose(t):
        sky_move(t)
        fall(snow, t)
        glow_of(glass, 3.4 + 0.5 * wave(t, 3))
        # along the snow from the right, then up and away to the left
        go = t / 0.8
        x = 10.5 - 20 * go * (0.55 + 0.45 * go)
        climb = between(go, 0.3, 1.0)
        z = 0.02 + 9.5 * climb * climb + (0.08 * abs(wave(t, 5)) if go < 0.3 else 0)
        pitch = 26 * between(go, 0.25, 0.6)
        if t >= 0.8:
            x, z = -30, 20
        rig.location = (x, 0.8, z)
        rig.rotation_euler = degrees(0, pitch + 2 * wave(t, 4), 0)
        for i, d in enumerate(deer):
            gallop(d, 6 * t + i * 0.3)
            d["root"].location.z = 0.12 * abs(wave(t, 6, i * 0.25))
        glow_of(deer[0]["nose"], 6 + 3 * wave(t, 4))
        sled["santa"]["arms"][1].rotation_euler = degrees(0, 150 + 20 * wave(t, 6), 0)
        sled["santa"]["hat"].rotation_euler = degrees(0, 38, -40 + 12 * wave(t, 6))
        key.location = (x, -3, z + 2)
        back = (math.cos(math.radians(pitch)), 0, -math.sin(math.radians(pitch)))
        trail(dust, t, (x + 1.2, 0.8, z + 0.25), back=back, long=5.5 * min(go * 2, 1), spread=0.9, times=4, size=0.09 if t < 0.8 else 0.0001)
        for n, waver in enumerate(wavers):
            waver["arms"][n % 2].rotation_euler = degrees(0, (170 if n % 2 else -170) + 25 * wave(t, 5, n * 0.2), 0)
            waver["root"].location.z = 0.15 * abs(wave(t, 5, n * 0.2))
            waver["head"].rotation_euler = degrees(-25 * climb, 0, 0)

    return 60, pose


# ---- on his way -------------------------------------------------------------------


def flying():
    sky("#03061c", "#132a66")
    star_list = stars(90, box_=((-16, 16), (16, 22), (-6, 16)))
    ball(mat("#fff0b8", 0.6, 0.85), (2.6, 14, 3.4), 3.3)
    # craters, just proud of the moon's face
    for x, z, r in ((1.6, 4.4, 0.55), (3.5, 2.6, 0.7), (3.4, 4.6, 0.35), (1.5, 2.3, 0.4)):
        ball(mat("#d9c684", 0.6, 0.6), (x, 10.9 + 0.35 * abs(x - 2.6) + 0.3 * abs(z - 3.4), z), (r, 0.1, r))
    rig = group((0, 0, 0), size=1.05)
    sled = sleigh(parent=rig)
    deer = team(rig, 2)
    dust = sparkles(30, GOLD, 10.0)
    near = [cloud((0, -1.5, -3.2), 1.6, "#6f86c4"), cloud((0, -1.5, -3.6), 2.0, "#6f86c4"), cloud((0, -1.5, -3.3), 1.4, "#6f86c4")]
    far = [cloud((0, 6, -2.2), 1.5, "#3c4f8f", glow=0.15), cloud((0, 6, 4.9), 1.2, "#3c4f8f", glow=0.15), cloud((0, 6, -1.6), 1.3, "#3c4f8f", glow=0.15)]

    light("SUN", (0, 0, 10), 2.2, "#b8c8ff", 5, aim=(-2, 6, 0))
    light("POINT", (3, -4, 3), 500, "#ffe2b8", 2.0)
    light("POINT", (2.6, 8, 3.4), 500, "#fff0c0", 2.0)
    camera((0, -14, 0.6), (0, 0, 0.6), lens=50)

    def pose(t):
        twinkle(star_list, t)
        bob = 0.22 * wave(t, 2)
        rig.location = (3.1, 0, -0.9 + bob)
        rig.rotation_euler = degrees(0, 5 + 3 * wave(t, 2, 0.2), 0)
        for i, d in enumerate(deer):
            gallop(d, 4 * t + i * 0.3)
            d["root"].location.z = 0.1 * wave(t, 4, i * 0.3)
        glow_of(deer[0]["nose"], 6 + 3 * wave(t, 4))
        sled["santa"]["hat"].rotation_euler = degrees(0, 38, -45 + 14 * wave(t, 4))
        sled["santa"]["arms"][0].rotation_euler = degrees(0, -60 + 8 * wave(t, 4), 0)
        sled["santa"]["arms"][1].rotation_euler = degrees(0, 60 + 8 * wave(t, 4), 0)
        trail(dust, t, (4.8, 0, -0.6 + bob), back=(1, 0, 0.12), long=4.5, spread=0.9, times=3, size=0.085)
        for i, c in enumerate(near):
            c.location.x = -11 + ((i * 7.3 + t * 22) % 22)
        for i, c in enumerate(far):
            c.location.x = -13 + ((i * 8.7 + t * 26) % 26)

    return 48, pose


# ---- on your roof -----------------------------------------------------------------


def rooftop():
    """Your roof on the night, for the two films of his visit. Returns what moves."""
    sky("#03061c", "#14306e")
    star_list = stars(70, box_=((-14, 14), (16, 22), (3, 16)))
    moon((-4.6, 20, 10.3), 1.7)
    ground("#9fb2e2", at=(0, 0, -6))
    # the village below, far off
    lit = []
    for i, (x, y) in enumerate(((-9, 16), (-3.5, 19), (3, 17), (9, 18), (-6.5, 13), (6.5, 13))):
        _, glass = cabin((x, y, -6), wide=3.0, deep=2.2, tall=1.7, wall=("#a8402c", "#3f6ea8", "#8a5a34")[i % 3], chimney=False)
        lit.append(glass)
        tree((x + 2.4, y - 0.5, -6), 3.0, seed=i)
    # this roof: snow to the ridge, a brick chimney
    roof(WHITE, (0, 1.5, -1.2), 22, 7, 2.4)
    roof(DARK_BROWN, (0, 1.5, -1.5), 21.6, 7.6, 2.4)
    for x in (-4.6, -1.5, 3.2):
        ball(WHITE, (x, 1.0, 1.05), (1.6, 0.9, 0.35))
    brick = "#9a4334"
    box(brick, (1.9, 1.3, 1.9), (1.5, 1.3, 2.4), round=0.04)
    for row in range(5):
        box("#7c3428", (1.9, 0.64, 1.0 + row * 0.42), (1.5, 0.02, 0.04), round=0)
    box(WHITE, (1.9, 1.3, 3.16), (1.8, 1.6, 0.22), round=0.1)
    hole = mat(WARM, 0.5, 0.0, own=True)
    box(hole, (1.9, 1.3, 3.2), (1.0, 0.9, 0.2), round=0.02)
    rig = group((-4.3, 1.4, 1.2), size=0.72, turn=(0, 0, 8))
    sleigh(parent=rig, driver=False)
    deer = reindeer((-8.2, 1.9, 1.2), size=0.9, red_nose=True)
    man = santa((0, 0, 0), size=0.95)
    bag = sack((0, 0, 0), size=0.5, colour=DARK_GREEN)
    magic = sparkles(30, GOLD, 10.0)
    glowing = light("POINT", (1.9, 0.8, 3.9), 0, WARM, 0.5, shadow=False)
    snow = snowfall(50, region=((-7, 7), (-2, 6), (0.5, 9)))

    light("SUN", (0, 0, 10), 2.0, "#9db8ff", 4, aim=(-3, 6, 0))
    light("POINT", (0, -4, 4), 380, "#ffe2b8", 1.5)
    camera((0, -12, 3.6), (0, 1.2, 2.7), lens=50)
    return star_list, snow, lit, hole, man, bag, magic, glowing, deer


def visit():
    star_list, snow, lit, hole, man, bag, magic, glowing, deer = rooftop()

    stand = (-0.4, 0.9, 1.2)
    top = (1.9, 1.2, 3.3)

    def pose(t):
        twinkle(star_list, t)
        fall(snow, t)
        for i, glass in enumerate(lit):
            glow_of(glass, 3.2 + 0.6 * wave(t, 2, i * 0.3))
        # a wave, a hop into the chimney, the magic, and back out again
        into = between(t, 0.14, 0.26)
        down = between(t, 0.26, 0.34)
        back_up = between(t, 0.66, 0.74)
        out = between(t, 0.76, 0.9)
        if t < 0.5:
            x = stand[0] + (top[0] - stand[0]) * into
            z = stand[2] + (top[2] - stand[2]) * into + 1.6 * math.sin(math.pi * into) - 2.6 * down
            spin = 0
        else:
            x = top[0] + (stand[0] - top[0]) * out
            z = top[2] - 2.6 * (1 - back_up) + (stand[2] - top[2]) * out + 1.4 * math.sin(math.pi * out)
            spin = 360 * out
        y = stand[1] + (top[1] - stand[1]) * (into if t < 0.5 else 1 - out)
        hidden = 0.34 <= t <= 0.66
        man["root"].location = (x, y, -40 if hidden else z)
        man["root"].rotation_euler = degrees(0, 0, spin)
        hello = 1 - between(t, 0.08, 0.14) if t < 0.5 else between(t, 0.9, 0.96)
        man["arms"][1].rotation_euler = degrees(0, 22 + 130 * hello + 18 * wave(t, 8) * hello, 0)
        man["arms"][0].rotation_euler = degrees(0, -22 - 100 * (into - down if t < 0.5 else 0), 0)
        man["head"].rotation_euler = degrees(0, 0, 8 * wave(t, 4) * hello)
        # the sack goes down with him, and stays
        has_bag = t < 0.5
        bag.location = (x + 0.55, y + 0.2, z + 0.3) if has_bag and not hidden else (0, 0, -40)
        inside = between(t, 0.3, 0.38) - between(t, 0.62, 0.7)
        glow_of(hole, 7 * inside * (0.8 + 0.2 * wave(t, 12)))
        glowing.data.energy = 260 * inside * (0.8 + 0.2 * wave(t, 12))
        for s, a, b, c in magic:
            age = ((t - 0.3) / 0.4 * 3 + a) % 1.0
            k = 0.085 * (1 - age) * (0.5 + b) * inside
            s.location = (top[0] + (b - 0.5) * 2.4 * age, top[1] - 0.6 + (c - 0.5) * 0.6, top[2] + 0.2 + 2.6 * age - 0.8 * age * age)
            s.scale = (max(k, 0.0001),) * 3
        deer["head"].rotation_euler = degrees(0, 32 + 8 * wave(t, 2), 0)
        glow_of(deer["nose"], 5 + 3 * wave(t, 3))

    return 72, pose


def drop():
    """He stands on your roof and tosses the presents down the chimney, one, two, three, four."""
    star_list, snow, lit, hole, man, bag, magic, glowing, deer = rooftop()
    gifts = [present((0, 0, -40), 0.42, PRESENT_COLOURS[i % len(PRESENT_COLOURS)]) for i in (0, 2, 4, 1)]
    stand = (0.15, 0.9, 1.2)
    hand = (stand[0] + 0.75, stand[1] - 0.1, stand[2] + 2.0)
    top = (1.9, 1.2, 3.3)
    man["root"].location = stand
    bag.location = (stand[0] - 1.0, stand[1] + 0.3, stand[2] - 0.05)
    bag.scale = (0.62,) * 3

    def pose(t):
        twinkle(star_list, t)
        fall(snow, t)
        for i, glass in enumerate(lit):
            glow_of(glass, 3.2 + 0.6 * wave(t, 2, i * 0.3))
        # four throws to the film: wind up, toss, and it's down the chimney in a flash
        turn = int(t * 4) % 4
        u = t * 4 % 1.0
        wind = between(u, 0.0, 0.22)
        toss = between(u, 0.22, 0.34)
        flight = min(max((u - 0.26) / 0.44, 0), 1)
        gone = between(u, 0.7, 0.8)
        flash = math.sin(math.pi * min(max((u - 0.68) / 0.32, 0), 1))
        man["root"].location = (stand[0], stand[1], stand[2] + 0.12 * math.sin(math.pi * toss))
        man["root"].rotation_euler = degrees(0, 0, 14 - 10 * wind + 16 * toss)
        man["arms"][1].rotation_euler = degrees(0, 22 + 150 * wind - 60 * toss * (1 - gone) - 150 * gone, 0)
        man["arms"][0].rotation_euler = degrees(0, -22 - 30 * toss * (1 - gone), 0)
        man["head"].rotation_euler = degrees(0, 0, -10 * flight * (1 - gone) + 6 * wave(t, 4))
        for i, gift in enumerate(gifts):
            if i != turn or u >= 0.8:
                gift.location = (0, 0, -40)
                continue
            if flight <= 0:
                # coming up out of the sack in his hand
                gift.location = (hand[0] - 0.9 * (1 - wind), hand[1], hand[2] - 1.5 * (1 - wind))
                gift.rotation_euler = degrees(0, 0, 20)
            else:
                gift.location = (hand[0] + (top[0] - hand[0]) * flight, hand[1] + (top[1] - hand[1]) * flight,
                                 hand[2] + (top[2] - hand[2]) * flight + 1.5 * math.sin(math.pi * flight) - 1.2 * gone)
                gift.rotation_euler = degrees(200 * flight, 360 * flight, 20)
            k = 1 - 0.6 * gone
            gift.scale = (k, k, k)
        glow_of(hole, 1.5 + 8 * flash)
        glowing.data.energy = 60 + 420 * flash
        for s, a, b, c in magic:
            age = min(max((u - 0.7) / 0.3, 0), 1) * (0.6 + 0.4 * a)
            k = 0.085 * (1 - age) * (0.5 + b) * (1 if u > 0.7 else 0)
            s.location = (top[0] + (b - 0.5) * 3.0 * age, top[1] - 0.6 + (c - 0.5) * 0.6, top[2] + 0.2 + (1.2 + 2.2 * a) * age - 0.9 * age * age)
            s.scale = (max(k, 0.0001),) * 3
        deer["head"].rotation_euler = degrees(0, 32 + 8 * wave(t, 2), 0)
        glow_of(deer["nose"], 5 + 3 * wave(t, 3))

    return 72, pose


# ---- christmas morning ------------------------------------------------------------


def morning():
    room("#7a4a2c", "#5a3520")
    fire = fireplace((-2.9, 2.6, 0))
    window((0.2, 2.95, 2.9), 1.4, 1.5, glass="#6f9ff0", glow=1.6)
    # stockings on the mantelpiece
    for i, colour in enumerate((RED, GREEN, RED)):
        x = -3.7 + i * 0.8
        box(colour, (x, 2.05, 1.85), (0.3, 0.14, 0.6), round=0.08)
        ball(colour, (x + 0.12, 2.05, 1.58), (0.26, 0.09, 0.15))
        box(WHITE, (x, 2.03, 2.14), (0.36, 0.18, 0.16), round=0.06)
    bulbs = tree((2.2, 0.9, 0), 5.2, lights=22, snowy=False, star=True, seed=7)
    pile((2.2, -0.9, 0), 9, seed=5, spread=1.7, size=0.62)
    present((-0.6, -1.3, 0), 0.75, PRESENT_COLOURS[1], turn=(0, 0, 20))
    present((-1.5, -0.6, 0), 0.5, PRESENT_COLOURS[3], turn=(0, 0, -15), shape=(1.5, 1, 0.8))
    # a toy train going round the tree
    cars = []
    for i, colour in enumerate((RED, GOLD, BLUE, GREEN)):
        car = group((0, 0, 0))
        box(colour, (0, 0, 0.2), (0.5, 0.3, 0.26), car, round=0.05)
        if i == 0:
            cone(BLACK, (-0.14, 0, 0.3), 0.06, 0.09, 0.26, car, sides=10)
            box(colour, (0.15, 0, 0.42), (0.2, 0.3, 0.22), car, round=0.04)
        else:
            ball((WHITE, RED, GOLD)[i % 3], (0, 0, 0.38), 0.13, car)
        cars.append(car)
    glints = sparkles(16, GOLD, 9.0)
    spots = [(random.Random(i).uniform(-2.2, 4.0), random.Random(i + 50).uniform(-2.0, -0.4), random.Random(i + 90).uniform(0.4, 1.6)) for i in range(16)]

    light("AREA", (0, -5, 5), 600, "#ffe2b8", 5, aim=(0, 0, 1))
    light("POINT", (2.2, -1.5, 2.5), 300, "#ffd9a0", 1.0)
    light("POINT", (0.2, 2, 3), 150, "#9fc0ff", 1.0)
    camera((0, -9.5, 2.6), (0, 0, 1.9), lens=50)

    def pose(t):
        flicker(fire, t, 350)
        blink(bulbs, t, 2, 2.0, 8.0)
        for i, car in enumerate(cars):
            a = TAU * (t - i * 0.055) + 1.2
            car.location = (2.2 + 2.1 * math.cos(a), 0.9 + 1.5 * math.sin(a), 0.02)
            car.rotation_euler = (0, 0, a - math.pi / 2)
        for (s, a, b, c), spot in zip(glints, spots):
            k = 0.08 * max(wave(t, 2, a), 0) ** 2
            s.location = spot
            s.scale = (max(k, 0.0001),) * 3

    return 48, pose


# ---- the globe, and the sleigh that flies over it -----------------------------------

# the plugin's map: GLOBE_FRAMES views a turn of the world apart, seen from GLOBE_TILT
# degrees north. the world is GLOBE_RADIUS of the picture's width across its radius.
# these are repeated in the plugin, which works out where on each picture a place is
GLOBE_FRAMES = 96
GLOBE_TILT = 20
GLOBE_RADIUS = 44 / 128


def globe():
    sky("#000000", "#000000", 0.0)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=1)
    world = from_bmesh(bm, None)
    m = bpy.data.materials.new("earth")
    if not m.node_tree:
        m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    shader = principled(m)
    picture = nodes.new("ShaderNodeTexImage")
    picture.image = bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "earth.png"))
    picture.interpolation = "Closest"
    picture.extension = "REPEAT"
    # longitude and latitude from where the point is on the ball, so the map sits exactly
    coords = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    lon = nodes.new("ShaderNodeMath")
    lon.operation = "ARCTAN2"
    u = nodes.new("ShaderNodeMath")
    u.operation = "MULTIPLY_ADD"
    u.inputs[1].default_value = 1 / TAU
    u.inputs[2].default_value = 0.5
    lat = nodes.new("ShaderNodeMath")
    lat.operation = "ARCSINE"
    v = nodes.new("ShaderNodeMath")
    v.operation = "MULTIPLY_ADD"
    v.inputs[1].default_value = 1 / math.pi
    v.inputs[2].default_value = 0.5
    join = nodes.new("ShaderNodeCombineXYZ")
    links.new(coords.outputs["Object"], split.inputs[0])
    links.new(split.outputs["Y"], lon.inputs[0])
    links.new(split.outputs["X"], lon.inputs[1])
    links.new(lon.outputs[0], u.inputs[0])
    links.new(split.outputs["Z"], lat.inputs[0])
    links.new(lat.outputs[0], v.inputs[0])
    links.new(u.outputs[0], join.inputs["X"])
    links.new(v.outputs[0], join.inputs["Y"])
    links.new(join.outputs[0], picture.inputs["Vector"])
    links.new(picture.outputs["Color"], shader.inputs["Base Color"])
    links.new(picture.outputs["Color"], shader.inputs["Emission Color"])
    shader.inputs["Emission Strength"].default_value = 0.55
    shader.inputs["Roughness"].default_value = 0.6
    world.data.materials.append(m)

    light("SUN", (0, 0, 0), 2.6, "#dfe8ff", 10, aim=(1.2, 2.0, -1.4), shadow=False)
    tilt = math.radians(GLOBE_TILT)
    camera((0, -10 * math.cos(tilt), 10 * math.sin(tilt)), (0, 0, 0), ortho=2 / (2 * GLOBE_RADIUS))

    def pose(t):
        middle = -180 + 360 * t
        world.rotation_euler = (0, 0, math.radians(-90 - middle))

    return GLOBE_FRAMES, pose


def sprite():
    """The sleigh as it is drawn on the globe: side on, four steps of the gallop."""
    sky("#16306c", "#16306c", 1.0)
    rig = group((0, 0, 0))
    sled = sleigh(parent=rig)
    deer = team(rig, 1, at=(-2.7, 0, 0.1), size=1.0)
    light("SUN", (0, 0, 10), 3.0, "#ffffff", 8, aim=(2, 6, 0), shadow=False)
    light("POINT", (0, -6, 2), 900, "#ffe2b8", 3.0, shadow=False)
    camera((-0.95, -12, 1.25), (-0.95, 0, 1.25), ortho=6.4)

    def pose(t):
        gallop(deer[0], t)
        deer[0]["root"].location.z = 0.1 + 0.1 * wave(t)
        sled["santa"]["hat"].rotation_euler = degrees(0, 38, -45 + 14 * wave(t))

    return 4, pose


SCENES = {"globe": globe, "sprite": sprite, "pole": pole, "checking": checking, "workshop": workshop, "practice": practice, "loading": loading,
          "takeoff": takeoff, "flying": flying, "visit": visit, "drop": drop, "morning": morning}


def render(name, folder, frames=None, size=512, clear=False):
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if clear else "RGB"
    scene.render.film_transparent = clear
    scene.eevee.taa_render_samples = 24
    scene.view_settings.view_transform = "Standard"
    try:
        scene.eevee.use_raytracing = False
        scene.eevee.use_fast_gi = True
    except AttributeError:
        pass

    count, pose = SCENES[name]()
    os.makedirs(folder, exist_ok=True)
    for frame in (frames if frames is not None else range(count)):
        pose(frame / count)
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(folder, f"{frame:03d}.png")
        bpy.ops.render.render(write_still=True)
    print(f"{name}: {count} frames")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    name, folder = args[0], args[1]
    frames = None
    size = 512
    if "--frames" in args:
        frames = [int(f) for f in args[args.index("--frames") + 1].split(",")]
    if "--size" in args:
        size = int(args[args.index("--size") + 1])
    render(name, folder, frames, size, clear=name in getattr(kit, "CLEAR", ()) or name.startswith("sprite"))
