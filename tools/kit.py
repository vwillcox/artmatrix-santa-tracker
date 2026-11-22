"""The toy box the Santa Tracker's scenes are built from, for Blender 5.

Everything is made of plain shapes: balls, boxes, cones and rings. Things stand on
z = 0, x runs left to right, and the camera looks along +y, so a character faces -y.
The sleigh and the reindeer face -x: Santa flies west, which is left on a map.

scenes.py builds a scene from these and moves the parts itself for each frame, so
nothing here uses Blender's own animation.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

RED = "#d81e2c"
DARK_RED = "#8f1220"
WHITE = "#f4f6ff"
SNOW = "#cfdcf5"
SKIN = "#f2b48c"
PINK = "#f08a80"
BLACK = "#15131a"
GOLD = "#f5b82e"
GREEN = "#1f9a48"
DARK_GREEN = "#0f5a32"
BROWN = "#8a5a34"
DARK_BROWN = "#4f3220"
TAN = "#d9b384"
CREAM = "#f3e6c4"
BLUE = "#2a6fdb"
PURPLE = "#8d4bd6"
ORANGE = "#f07d1e"
WARM = "#ffc861"

PRESENT_COLOURS = ((RED, GOLD), (GREEN, RED), (BLUE, WHITE), (PURPLE, GOLD), (GOLD, RED), (WHITE, RED))


def linear(hex_colour):
    out = []
    for i in (1, 3, 5):
        c = int(hex_colour[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out + [1.0]


_materials = {}


def principled(material):
    return next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def mat(colour, rough=0.65, glow=0.0, metal=0.0, alpha=1.0, own=False):
    """A material in this colour. own=True gives one of its own, to change frame by frame."""
    key = (colour, rough, glow, metal, alpha)
    if not own and key in _materials:
        return _materials[key]
    m = bpy.data.materials.new(colour)
    if not m.node_tree:
        m.use_nodes = True
    shader = principled(m)
    shader.inputs["Base Color"].default_value = linear(colour)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Emission Color"].default_value = linear(colour)
    shader.inputs["Emission Strength"].default_value = glow
    if alpha < 1.0:
        shader.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    if not own:
        _materials[key] = m
    return m


def glow_of(material, strength):
    principled(material).inputs["Emission Strength"].default_value = strength


def as_mat(m):
    return mat(m) if isinstance(m, str) else m


def place(obj, at=(0, 0, 0), size=(1, 1, 1), turn=(0, 0, 0), parent=None):
    obj.location = at
    obj.scale = (size, size, size) if isinstance(size, (int, float)) else size
    obj.rotation_euler = [math.radians(a) for a in turn]
    if parent is not None:
        obj.parent = parent
    return obj


def group(at=(0, 0, 0), parent=None, turn=(0, 0, 0), size=1):
    e = bpy.data.objects.new("group", None)
    bpy.context.scene.collection.objects.link(e)
    return place(e, at, size, turn, parent)


def from_bmesh(bm, material, smooth=True):
    mesh = bpy.data.meshes.new("shape")
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for polygon in mesh.polygons:
            polygon.use_smooth = True
    obj = bpy.data.objects.new("shape", mesh)
    bpy.context.scene.collection.objects.link(obj)
    if material is not None:
        mesh.materials.append(as_mat(material))
    return obj


def ball(material, at=(0, 0, 0), size=1, parent=None, turn=(0, 0, 0)):
    """A ball of radius 1, squashed by size."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=14, radius=1)
    return place(from_bmesh(bm, material), at, size, turn, parent)


def box(material, at=(0, 0, 0), size=(1, 1, 1), parent=None, turn=(0, 0, 0), round=0.06):
    """A box size across, with rounded edges."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    if isinstance(size, (int, float)):
        size = (size, size, size)
    # scaled in the mesh so the rounding keeps its size
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    obj = place(from_bmesh(bm, material, smooth=False), at, 1, turn, parent)
    if round:
        bevel = obj.modifiers.new("round", "BEVEL")
        bevel.width = min(round, min(size) * 0.45)
        bevel.segments = 3
    return obj


def cone(material, at=(0, 0, 0), bottom=1, top=0, tall=1, parent=None, turn=(0, 0, 0), sides=28, size=1):
    """A cone or tube standing on `at`, pointing up z."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=bottom, radius2=top, depth=tall)
    for v in bm.verts:
        v.co.z += tall / 2
    obj = place(from_bmesh(bm, material, smooth=sides > 8), at, size, turn, parent)
    if sides > 8:
        # the caps stay flat
        split = obj.modifiers.new("edges", "EDGE_SPLIT")
        split.split_angle = math.radians(50)
    return obj


def ring(material, at=(0, 0, 0), across=1, thick=0.1, parent=None, turn=(0, 0, 0), size=1):
    bm = bmesh.new()
    steps, around = 32, 10
    rows = []
    for i in range(steps):
        a = 2 * math.pi * i / steps
        row = []
        for j in range(around):
            b = 2 * math.pi * j / around
            r = across + thick * math.cos(b)
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), thick * math.sin(b))))
        rows.append(row)
    for i in range(steps):
        for j in range(around):
            bm.faces.new((rows[i][j], rows[(i + 1) % steps][j], rows[(i + 1) % steps][(j + 1) % around], rows[i][(j + 1) % around]))
    return place(from_bmesh(bm, material), at, size, turn, parent)


def roof(material, at, wide, deep, tall, parent=None, turn=(0, 0, 0)):
    """A ridged roof: its ridge runs along x, its eaves sit at z = at."""
    bm = bmesh.new()
    w, d = wide / 2, deep / 2
    points = [(-w, -d, 0), (w, -d, 0), (w, d, 0), (-w, d, 0), (-w, 0, tall), (w, 0, tall)]
    v = [bm.verts.new(p) for p in points]
    for face in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)):
        bm.faces.new([v[i] for i in face])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = place(from_bmesh(bm, material, smooth=False), at, 1, turn, parent)
    bevel = obj.modifiers.new("round", "BEVEL")
    bevel.width = 0.05
    bevel.segments = 2
    return obj


def limb(material, long, thick, parent, at, end=None, end_size=None):
    """An arm or a leg hanging from a joint at `at`: turn the joint to swing it."""
    joint = group(at, parent)
    cone(material, (0, 0, -long), thick, thick, long, joint)
    ball(material, (0, 0, 0), thick, joint)
    if end is not None:
        ball(end, (0, 0, -long), end_size or thick * 1.25, joint)
    return joint


# ---- people ---------------------------------------------------------------------


def santa(at=(0, 0, 0), parent=None, turn=(0, 0, 0), size=1, legs=True):
    """Santa, about 2.6 tall. Returns his parts, to move."""
    root = group(at, parent, turn, size)
    body = group((0, 0, 0), root)
    ball(RED, (0, 0, 0.98), (0.66, 0.6, 0.7), body)
    ring(BLACK, (0, 0, 0.9), 0.63, 0.085, body, size=(1, 0.92, 1))
    box(GOLD, (0, -0.62, 0.9), (0.24, 0.1, 0.22), body, round=0.03)
    box(BLACK, (0, -0.66, 0.9), (0.12, 0.06, 0.1), body, round=0.02)
    ring(WHITE, (0, 0, 0.46), 0.5, 0.11, body, size=(1, 0.92, 1))
    # the fur down his front
    ball(WHITE, (0, -0.56, 1.25), (0.09, 0.08, 0.26), body)

    head = group((0, 0, 1.78), body)
    ball(SKIN, (0, 0, 0), 0.37, head)
    ball(WHITE, (0, -0.1, -0.25), (0.4, 0.3, 0.36), head)
    ball(WHITE, (-0.2, -0.16, -0.12), 0.2, head)
    ball(WHITE, (0.2, -0.16, -0.12), 0.2, head)
    ball(WHITE, (0, -0.2, -0.46), (0.22, 0.18, 0.22), head)
    ball(WHITE, (-0.11, -0.34, -0.09), (0.13, 0.07, 0.07), head, turn=(0, 20, 0))
    ball(WHITE, (0.11, -0.34, -0.09), (0.13, 0.07, 0.07), head, turn=(0, -20, 0))
    ball(PINK, (0, -0.37, 0.0), 0.085, head)
    ball(PINK, (-0.24, -0.27, 0.0), (0.09, 0.05, 0.07), head)
    ball(PINK, (0.24, -0.27, 0.0), (0.09, 0.05, 0.07), head)
    ball(BLACK, (-0.14, -0.32, 0.1), 0.05, head)
    ball(BLACK, (0.14, -0.32, 0.1), 0.05, head)
    ball(WHITE, (-0.14, -0.31, 0.2), (0.1, 0.04, 0.035), head, turn=(0, 12, 0))
    ball(WHITE, (0.14, -0.31, 0.2), (0.1, 0.04, 0.035), head, turn=(0, -12, 0))
    hat = group((0, 0.02, 0.2), head, turn=(-8, 0, 0))
    ring(WHITE, (0, 0, 0.04), 0.33, 0.1, hat)
    cone(RED, (0, 0, 0.05), 0.34, 0.2, 0.3, hat)
    flop = group((0, 0, 0.33), hat, turn=(0, 38, 0))
    cone(RED, (0, 0, -0.02), 0.2, 0.05, 0.42, flop)
    bobble = ball(WHITE, (0, 0, 0.45), 0.13, flop)

    arms = []
    for side in (-1, 1):
        arm = limb(RED, 0.5, 0.15, body, (side * 0.6, -0.05, 1.42))
        ring(WHITE, (0, 0, -0.5), 0.14, 0.07, arm)
        ball(DARK_GREEN, (0, 0, -0.62), 0.15, arm)
        arm.rotation_euler = (0, math.radians(side * 22), 0)
        arms.append(arm)
    feet = []
    if legs:
        for side in (-1, 1):
            leg = group((side * 0.27, -0.03, 0.42), root)
            cone(RED, (0, 0, -0.3), 0.17, 0.17, 0.3, leg)
            ball(BLACK, (0, -0.1, -0.3), (0.19, 0.28, 0.14), leg)
            feet.append(leg)
    return {"root": root, "body": body, "head": head, "hat": flop, "bobble": bobble, "arms": arms, "feet": feet}


def elf(at=(0, 0, 0), parent=None, turn=(0, 0, 0), size=1, coat=GREEN, trim=RED):
    """An elf, about 1.6 tall."""
    root = group(at, parent, turn, size)
    body = group((0, 0, 0), root)
    cone(coat, (0, 0, 0.32), 0.42, 0.24, 0.62, body)
    ring(trim, (0, 0, 0.36), 0.4, 0.06, body)
    ring(BLACK, (0, 0, 0.62), 0.31, 0.05, body)
    box(GOLD, (0, -0.31, 0.62), (0.13, 0.06, 0.12), body, round=0.02)
    # a collar of points
    for i in range(8):
        a = 2 * math.pi * i / 8
        cone(trim, (0.2 * math.cos(a), 0.2 * math.sin(a), 0.94), 0.1, 0, 0.2, body, turn=(180 + 35 * math.sin(a), -35 * math.cos(a), 0), sides=8)

    head = group((0, 0, 1.18), body)
    ball(SKIN, (0, 0, 0), 0.3, head)
    ball(PINK, (0, -0.3, -0.02), 0.06, head)
    ball(PINK, (-0.19, -0.21, -0.06), (0.07, 0.04, 0.05), head)
    ball(PINK, (0.19, -0.21, -0.06), (0.07, 0.04, 0.05), head)
    ball(BLACK, (-0.11, -0.26, 0.05), 0.045, head)
    ball(BLACK, (0.11, -0.26, 0.05), 0.045, head)
    for side in (-1, 1):
        cone(SKIN, (side * 0.26, 0, -0.02), 0.09, 0, 0.26, head, turn=(0, side * 68, 0), sides=10, size=(1, 0.45, 1))
    hat = group((0, 0, 0.14), head, turn=(-6, 0, 0))
    ring(trim, (0, 0, 0.04), 0.27, 0.07, hat)
    cone(coat, (0, 0, 0.05), 0.28, 0.12, 0.32, hat)
    flop = group((0, 0, 0.36), hat, turn=(0, -30, 0))
    cone(coat, (0, 0, -0.02), 0.12, 0.02, 0.36, flop)
    ball(GOLD, (0, 0, 0.36), 0.08, flop)

    arms = []
    for side in (-1, 1):
        arm = limb(coat, 0.36, 0.1, body, (side * 0.3, -0.02, 0.88), SKIN, 0.11)
        arm.rotation_euler = (0, math.radians(side * 25), 0)
        arms.append(arm)
    feet = []
    for side in (-1, 1):
        leg = group((side * 0.16, -0.02, 0.32), root)
        cone(WHITE, (0, 0, -0.24), 0.09, 0.09, 0.26, leg)
        ball(trim, (0, -0.1, -0.25), (0.12, 0.22, 0.09), leg)
        cone(trim, (0, -0.28, -0.25), 0.06, 0, 0.16, leg, turn=(-50, 0, 0), sides=8)
        feet.append(leg)
    return {"root": root, "body": body, "head": head, "hat": flop, "arms": arms, "feet": feet}


# ---- animals and the sleigh -------------------------------------------------------


def reindeer(at=(0, 0, 0), parent=None, turn=(0, 0, 0), size=1, red_nose=False):
    """A reindeer facing -x, about 2 tall to the antlers. Rudolph's nose has its own material."""
    root = group(at, parent, turn, size)
    body = group((0, 0, 1.0), root)
    ball(BROWN, (0, 0, 0), (0.62, 0.34, 0.36), body)
    ball(TAN, (-0.2, 0, -0.1), (0.4, 0.3, 0.27), body)
    ball(CREAM, (0.62, 0, 0.12), 0.1, body)
    ring(RED, (-0.42, 0, 0.12), 0.27, 0.05, body, turn=(0, 62, 0), size=(1, 1.1, 1))
    ball(GOLD, (-0.58, -0.02, -0.12), 0.07, body)

    neck = group((-0.45, 0, 0.18), body, turn=(0, -32, 0))
    cone(BROWN, (0, 0, 0), 0.2, 0.15, 0.5, neck)
    head = group((0, 0, 0.55), neck, turn=(0, 32, 0))
    ball(BROWN, (0, 0, 0), (0.25, 0.2, 0.2), head)
    ball(TAN, (-0.24, 0, -0.05), (0.19, 0.14, 0.13), head)
    nose_material = mat(RED, 0.3, 4.0, own=True) if red_nose else mat(BLACK, 0.3)
    ball(nose_material, (-0.42, 0, -0.02), 0.085 if red_nose else 0.06, head)
    for side in (-1, 1):
        ball(BLACK, (-0.14, side * 0.17, 0.06), 0.04, head)
        ball(WHITE, (-0.15, side * 0.19, 0.075), 0.015, head)
        cone(BROWN, (0.08, side * 0.16, 0.08), 0.07, 0, 0.2, head, turn=(side * -65, 20, 0), sides=10)
        antler = group((0.04, side * 0.09, 0.15), head, turn=(side * -18, 12, 0))
        cone(CREAM, (0, 0, 0), 0.035, 0.028, 0.42, antler, sides=10)
        cone(CREAM, (0, 0, 0.16), 0.028, 0.012, 0.22, antler, turn=(0, -55, 0), sides=10)
        cone(CREAM, (0, 0, 0.3), 0.026, 0.012, 0.2, antler, turn=(0, 50, 0), sides=10)
        cone(CREAM, (0, 0, 0.4), 0.026, 0.012, 0.16, antler, turn=(0, -40, 0), sides=10)
    legs = []
    for x in (-0.38, 0.4):
        for side in (-1, 1):
            leg = group((x, side * 0.17, -0.15), body)
            cone(BROWN, (0, 0, -0.62), 0.06, 0.1, 0.62, leg, sides=12)
            cone(BLACK, (0, 0, -0.72), 0.08, 0.07, 0.12, leg, sides=12)
            legs.append(leg)
    return {"root": root, "body": body, "neck": neck, "head": head, "legs": legs, "nose": nose_material}


def gallop(deer, phase):
    """Sets a reindeer's legs for this point in its stride, 0 to 1."""
    for i, leg in enumerate(deer["legs"]):
        front = i < 2
        swing = math.sin(2 * math.pi * (phase + (0 if front else 0.5) + (i % 2) * 0.12))
        leg.rotation_euler = (0, math.radians((35 if front else 30) * swing + (10 if front else -10)), 0)
    deer["neck"].rotation_euler = (0, math.radians(-32 + 5 * math.sin(2 * math.pi * phase)), 0)


def present(at=(0, 0, 0), size=0.4, colours=(RED, GOLD), parent=None, turn=(0, 0, 0), shape=(1, 1, 1)):
    """A wrapped present standing on `at`."""
    paper, ribbon = colours
    root = group(at, parent, turn)
    w, d, h = (size * s for s in shape)
    box(paper, (0, 0, h / 2), (w, d, h), root, round=0.03)
    box(ribbon, (0, 0, h / 2), (w * 0.2, d * 1.03, h * 1.03), root, round=0.01)
    box(ribbon, (0, 0, h / 2), (w * 1.03, d * 0.2, h * 1.03), root, round=0.01)
    for side in (-1, 1):
        ball(ribbon, (side * w * 0.14, 0, h + size * 0.06), (size * 0.16, size * 0.08, size * 0.1), root, turn=(0, side * 25, 0))
    return root


def sack(at=(0, 0, 0), parent=None, size=1, colour=DARK_GREEN):
    """Santa's sack, full, with presents poking out of the top."""
    root = group(at, parent, size=size)
    ball(colour, (0, 0, 0.55), (0.62, 0.56, 0.6), root)
    ring(GOLD, (0, 0, 1.0), 0.36, 0.05, root)
    present((-0.16, -0.08, 0.95), 0.34, PRESENT_COLOURS[0], root, turn=(12, -14, 20))
    present((0.18, 0.05, 0.98), 0.3, PRESENT_COLOURS[2], root, turn=(-8, 16, -30))
    present((0.02, -0.2, 1.02), 0.26, PRESENT_COLOURS[4], root, turn=(20, 6, 50))
    return root


def sleigh(at=(0, 0, 0), parent=None, turn=(0, 0, 0), size=1, loaded=True, driver=True):
    """The sleigh, facing -x, about 3 long. Santa rides in it if driver is set."""
    root = group(at, parent, turn, size)
    body = group((0, 0, 0.42), root)
    box(RED, (0.1, 0, 0.3), (2.3, 1.1, 0.6), body, round=0.14)
    box(DARK_RED, (0.1, 0, 0.47), (2.0, 0.86, 0.3), body, round=0.05)
    # the high back and the curled front
    box(RED, (1.15, 0, 0.75), (0.3, 1.1, 1.1), body, round=0.12, turn=(0, 10, 0))
    box(RED, (-1.02, 0, 0.62), (0.28, 1.1, 0.75), body, round=0.12, turn=(0, -22, 0))
    cone(RED, (-1.18, -0.55, 1.0), 0.2, 0.2, 1.1, body, turn=(-90, 0, 0))
    for side in (-1, 1):
        box(GOLD, (0.1, side * 0.56, 0.6), (2.2, 0.05, 0.07), body, round=0.02)
        ring(GOLD, (-1.18, side * 0.56, 1.0), 0.2, 0.035, body, turn=(90, 0, 0))
        ball(GOLD, (0.1, side * 0.57, 0.3), (0.2, 0.03, 0.2), body)
        # runners, with a curl at the front
        box(GOLD, (0.15, side * 0.5, -0.36), (2.5, 0.07, 0.07), body, round=0.03)
        curl = group((-1.1, side * 0.5, -0.06), body)
        for i in range(9):
            a = math.radians(180 + i * 22)
            ball(GOLD, (0.3 * math.cos(a), 0, 0.3 * math.sin(a)), 0.05, curl)
        for x in (-0.6, 0.2, 1.0):
            box(GOLD, (x, side * 0.5, -0.18), (0.06, 0.06, 0.36), body, round=0.02)
    parts = {"root": root, "body": body}
    if driver:
        parts["santa"] = santa((-0.3, 0, 0.5), body, turn=(0, 0, -90), size=0.72, legs=False)
    if loaded:
        parts["sack"] = sack((0.55, 0, 0.42), body, 0.92)
    return parts


def team(parent, count=2, at=(-2.6, 0, 0), gap=1.9, size=0.85):
    """Reindeer in harness ahead of the sleigh, Rudolph in front. Returns them, lead first."""
    deer = []
    for i in range(count):
        x = at[0] - (count - 1 - i) * gap
        deer.append(reindeer((x, at[1], at[2]), parent, size=size, red_nose=(i == 0)))
    # the reins, from the sleigh's front to the lead
    for side in (-1, 1):
        far = at[0] - (count - 1) * gap
        long = -1.25 - far
        cone(DARK_BROWN, (far, side * 0.14, at[2] + 1.05 * size), 0.018, 0.018, long, parent, turn=(0, 90, 0), sides=6)
    return deer


# ---- things ---------------------------------------------------------------------


def tree(at=(0, 0, 0), tall=2.4, parent=None, lights=0, snowy=True, star=False, seed=1):
    """A fir tree. Returns the materials of its lights, to twinkle."""
    root = group(at, parent, size=tall / 2.4)
    cone(DARK_BROWN, (0, 0, 0), 0.14, 0.12, 0.5, root, sides=10)
    tiers = ((0.35, 0.95, 0.95), (0.95, 0.75, 0.85), (1.5, 0.52, 0.75))
    for z, wide, high in tiers:
        cone(DARK_GREEN, (0, 0, z), wide, 0.02, high, root, sides=14)
        if snowy:
            cone(SNOW, (0, 0, z + high * 0.52), wide * 0.5, 0.0, high * 0.5, root, sides=14)
    bulbs = []
    rng = random.Random(seed)
    colours = (RED, GOLD, BLUE, WHITE, ORANGE, PURPLE)
    for i in range(lights):
        z, wide, high = tiers[i % 3]
        up = rng.uniform(0.08, 0.6)
        r = wide * (1 - up) + 0.02
        a = rng.uniform(math.pi * 0.95, math.pi * 2.05)
        m = mat(colours[i % len(colours)], 0.3, 5.0, own=True)
        ball(m, (r * math.cos(a), r * math.sin(a), z + up * high), 0.075, root)
        bulbs.append(m)
    if star:
        m = mat(GOLD, 0.3, 4.0, own=True)
        top = group((0, 0, 2.32), root)
        for i in range(5):
            cone(m, (0, 0, 0), 0.07, 0, 0.24, top, turn=(0, i * 72, 0), sides=4, size=(1, 0.5, 1))
        ball(m, (0, 0, 0), (0.09, 0.05, 0.09), top)
        bulbs.append(m)
    return bulbs


def cabin(at=(0, 0, 0), parent=None, wide=3.2, deep=2.4, tall=1.7, wall="#a8402c", turn=(0, 0, 0), chimney=True):
    """A snowy cabin with lit windows facing -y. Returns the window materials."""
    root = group(at, parent, turn)
    box(wall, (0, 0, tall / 2), (wide, deep, tall), root, round=0.05)
    roof(DARK_BROWN, (0, 0, tall - 0.02), wide + 0.3, deep + 0.4, 1.1, root)
    roof(WHITE, (0, 0, tall + 0.1), wide + 0.42, deep + 0.3, 1.12, root)
    glass = mat(WARM, 0.4, 3.5, own=True)
    for x in (-wide * 0.28, wide * 0.28):
        box(CREAM, (x, -deep / 2 - 0.01, tall * 0.55), (0.72, 0.08, 0.72), root, round=0.02)
        box(glass, (x, -deep / 2 - 0.03, tall * 0.55), (0.58, 0.08, 0.58), root, round=0.01)
        box(CREAM, (x, -deep / 2 - 0.05, tall * 0.55), (0.06, 0.06, 0.58), root, round=0.0)
        box(CREAM, (x, -deep / 2 - 0.05, tall * 0.55), (0.58, 0.06, 0.06), root, round=0.0)
        ball(WHITE, (x, -deep / 2 - 0.08, tall * 0.55 - 0.36), (0.42, 0.1, 0.08), root)
    box(DARK_BROWN, (0, -deep / 2 - 0.02, 0.5), (0.6, 0.08, 1.0), root, round=0.04)
    ball(GOLD, (0.2, -deep / 2 - 0.08, 0.5), 0.045, root)
    ring(GREEN, (0, -deep / 2 - 0.08, 0.72), 0.15, 0.05, root, turn=(90, 0, 0))
    ball(RED, (0, -deep / 2 - 0.12, 0.58), 0.05, root)
    if chimney:
        box("#7a3a30", (wide * 0.3, 0.2, tall + 0.95), (0.5, 0.5, 1.0), root, round=0.03)
        box(WHITE, (wide * 0.3, 0.2, tall + 1.47), (0.62, 0.62, 0.14), root, round=0.06)
    return root, glass


def candy_pole(at=(0, 0, 0), tall=2.6, parent=None):
    """The North Pole itself: striped, with a gold ball on top."""
    root = group(at, parent)
    bands = 9
    for i in range(bands):
        cone(RED if i % 2 else WHITE, (0, 0, i * tall / bands), 0.13, 0.13, tall / bands + 0.005, root, sides=16)
    ball(GOLD, (0, 0, tall + 0.14), 0.2, root)
    box(RED, (0.5, -0.05, tall * 0.7), (0.85, 0.08, 0.34), root, round=0.04)
    box(WHITE, (0.5, -0.1, tall * 0.7), (0.66, 0.04, 0.08), root, round=0.01)
    return root


def snowman(at=(0, 0, 0), parent=None, size=1, turn=(0, 0, 0)):
    root = group(at, parent, turn, size)
    ball(WHITE, (0, 0, 0.4), 0.45, root)
    ball(WHITE, (0, 0, 1.0), 0.33, root)
    head = group((0, 0, 1.48), root)
    ball(WHITE, (0, 0, 0), 0.25, head)
    cone(ORANGE, (0, -0.22, 0), 0.05, 0, 0.26, head, turn=(90, 0, 0), sides=10)
    ball(BLACK, (-0.09, -0.21, 0.08), 0.035, head)
    ball(BLACK, (0.09, -0.21, 0.08), 0.035, head)
    cone(BLACK, (0, 0, 0.18), 0.3, 0.3, 0.04, head)
    cone(BLACK, (0, 0, 0.2), 0.19, 0.19, 0.3, head)
    ring(RED, (0, 0, 1.26), 0.24, 0.07, root)
    box(RED, (0.16, -0.24, 1.08), (0.12, 0.06, 0.36), root, round=0.03, turn=(0, -12, 0))
    for i in range(3):
        ball(BLACK, (0, -0.31 - (0.02 if i == 1 else 0), 0.86 + i * 0.14), 0.035, root)
    return {"root": root, "head": head}


# ---- the world --------------------------------------------------------------------


def ground(colour=SNOW, size=60, at=(0, 0, 0), rough=0.9):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size)
    return place(from_bmesh(bm, mat(colour, rough), smooth=False), at)


def drifts(spots, colour=SNOW):
    """Mounds of snow: (x, y, across, height) each."""
    for x, y, across, height in spots:
        ball(mat(colour, 0.9), (x, y, 0), (across, across * 0.8, height))


def sky(top="#050a24", bottom="#1b3a7a", strength=1.0):
    """A night sky fading from top to bottom of the picture, also the light the scene sits in."""
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    if not world.node_tree:
        world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    background = next(n for n in nodes if n.type == "BACKGROUND")
    coords = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = linear(bottom)
    ramp.color_ramp.elements[1].color = linear(top)
    # the camera sees the window, everything else is lit by a flat middle blue
    path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixRGB")
    mix.inputs[1].default_value = [(a + b) / 2 for a, b in zip(linear(top), linear(bottom))]
    links.new(coords.outputs["Window"], split.inputs[0])
    links.new(split.outputs["Y"], ramp.inputs[0])
    links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(ramp.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], background.inputs["Color"])
    background.inputs["Strength"].default_value = strength
    return world


def stars(count=60, seed=3, box_=((-14, 14), (16, 22), (1, 16)), size=0.05):
    """Stars on the far side of the scene. Returns them with a phase each, to twinkle."""
    rng = random.Random(seed)
    glow = mat(WHITE, 0.5, 6.0)
    out = []
    for _ in range(count):
        at = [rng.uniform(*span) for span in box_]
        s = ball(glow, at, size * rng.uniform(0.6, 1.5))
        out.append((s, rng.random(), s.scale[0]))
    return out


def twinkle(star_list, t, times=2):
    for s, phase, size in star_list:
        k = 0.65 + 0.35 * math.sin(2 * math.pi * (times * t + phase))
        s.scale = (size * k, size * k, size * k)


def moon(at=(4, 20, 9), size=1.6):
    m = mat("#fff3c8", 0.5, 2.2)
    return ball(m, at, size)


def ribbon_material(colour, strength=2.5):
    """Glows in the middle of its height and fades away to nothing above and below."""
    m = bpy.data.materials.new("aurora")
    if not m.node_tree:
        m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    clear = nodes.new("ShaderNodeBsdfTransparent")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = linear(colour)
    emit.inputs["Strength"].default_value = strength
    coords = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.3
    ramp.color_ramp.elements[1].color = (0.75, 0.75, 0.75, 1)
    end = ramp.color_ramp.elements.new(1.0)
    end.color = (0, 0, 0, 1)
    links.new(coords.outputs["UV"], split.inputs[0])
    links.new(split.outputs["Y"], ramp.inputs[0])
    links.new(ramp.outputs[0], mix.inputs[0])
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(emit.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def aurora(at=(0, 21, 6), wide=26, tall=7, colour="#35f0a0", waves=2.5, seed=0, strength=2.5):
    """A curtain of northern lights. Returns (object, rest points) for sway()."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    steps = 48
    low, high = [], []
    for i in range(steps + 1):
        u = i / steps
        x = (u - 0.5) * wide
        y = 1.2 * math.sin(waves * 2 * math.pi * u + seed)
        low.append(bm.verts.new((x, y, 0)))
        high.append(bm.verts.new((x, y, tall)))
    for i in range(steps):
        face = bm.faces.new((low[i], low[i + 1], high[i + 1], high[i]))
        for loop, (u, v) in zip(face.loops, ((i / steps, 0), ((i + 1) / steps, 0), ((i + 1) / steps, 1), (i / steps, 1))):
            loop[uv].uv = (u, v)
    obj = place(from_bmesh(bm, ribbon_material(colour, strength)), at)
    rest = [v.co.copy() for v in obj.data.vertices]
    return obj, rest, (wide, waves, seed)


def sway(curtain, t):
    obj, rest, (wide, waves, seed) = curtain
    for v, r in zip(obj.data.vertices, rest):
        u = r.x / wide + 0.5
        v.co.y = r.y + 0.9 * math.sin(2 * math.pi * (t + 1.5 * u) + seed)
        v.co.z = r.z * (1 + 0.12 * math.sin(2 * math.pi * (t + 3 * u) + seed)) if r.z > 0 else r.z + 0.5 * math.sin(2 * math.pi * (t + 2 * u) + seed)
    obj.data.update()


def snowfall(count=70, seed=5, region=((-6, 6), (-3, 8), (0, 8)), size=0.035):
    """Falling snow that ends each loop where it began. Returns the flakes for fall()."""
    rng = random.Random(seed)
    glow = mat(WHITE, 0.6, 1.5)
    flakes = []
    for _ in range(count):
        at = [rng.uniform(*span) for span in region]
        flake = ball(glow, at, size * rng.uniform(0.7, 1.4))
        flakes.append((flake, at, rng.random(), rng.choice((1, 1, 2))))
    return flakes, region


def fall(snow, t):
    flakes, region = snow
    low, high = region[2]
    for flake, at, phase, speed in flakes:
        z = low + (at[2] - low - speed * t * (high - low)) % (high - low)
        flake.location = (at[0] + 0.25 * math.sin(2 * math.pi * (t * speed + phase)), at[1], z)


def light(kind, at, power, colour="#ffffff", size=1.0, aim=None, shadow=True):
    data = bpy.data.lights.new("light", kind)
    data.energy = power
    data.color = linear(colour)[:3]
    if kind == "AREA":
        data.size = size
    elif kind == "POINT" or kind == "SPOT":
        data.shadow_soft_size = size
    elif kind == "SUN":
        data.angle = math.radians(size)
    data.use_shadow = shadow
    obj = bpy.data.objects.new("light", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at
    if aim is not None:
        look(obj, aim)
    return obj


def look(obj, target):
    direction = Vector(target) - Vector(obj.location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera(at, target, lens=50, ortho=None):
    data = bpy.data.cameras.new("camera")
    if ortho:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    else:
        data.lens = lens
    data.clip_end = 200
    obj = bpy.data.objects.new("camera", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at
    look(obj, target)
    bpy.context.scene.camera = obj
    return obj


# ---- indoors ----------------------------------------------------------------------


def room(wall="#7a4a2c", floor="#5a3520", rug=RED):
    """A cosy room: a back wall at y = 3, a floor and a round rug."""
    sky("#1a0e08", "#2a1810", 0.6)
    ground(floor, rough=0.7)
    box(wall, (0, 3.2, 4), (16, 0.4, 8), round=0)
    # planks and a skirting board
    for x in range(-7, 8, 2):
        box("#6b3f25", (x, 2.98, 4), (0.05, 0.05, 8), round=0)
    box(DARK_BROWN, (0, 2.95, 0.15), (16, 0.12, 0.3), round=0.02)
    if rug:
        cone(rug, (0, -0.6, 0), 2.6, 2.6, 0.03)
        cone(CREAM, (0, -0.6, 0.005), 2.2, 2.2, 0.03)
        cone(rug, (0, -0.6, 0.01), 2.05, 2.05, 0.03)


def window(at=(2.5, 2.95, 2.6), wide=1.5, tall=1.5, glass="#17357f", glow=1.2):
    """A window in the back wall, night outside, snow on the sill."""
    x, y, z = at
    box(CREAM, (x, y, z), (wide + 0.24, 0.1, tall + 0.24), round=0.03)
    box(mat(glass, 0.3, glow), (x, y - 0.03, z), (wide, 0.1, tall), round=0)
    box(CREAM, (x, y - 0.06, z), (0.07, 0.08, tall), round=0)
    box(CREAM, (x, y - 0.06, z), (wide, 0.08, 0.07), round=0)
    ball(WHITE, (x, y - 0.1, z - tall / 2), (wide * 0.56, 0.14, 0.1))
    rng = random.Random(int(x * 10))
    for _ in range(9):
        ball(mat(WHITE, 0.5, 3.0), (x + rng.uniform(-wide, wide) * 0.42, y - 0.09, z + rng.uniform(-tall, tall) * 0.4), 0.03)


def fireplace(at=(-2.6, 2.6, 0)):
    """A stone fireplace against the back wall. Returns its flames and its light, for flicker()."""
    x, y, z = at
    stone = "#8d8a94"
    box(stone, (x, y, 1.1), (2.4, 0.8, 2.2), round=0.08)
    box("#a39fa9", (x, y - 0.05, 2.3), (2.8, 1.0, 0.25), round=0.06)
    box(stone, (x, y + 0.1, 4.6), (1.5, 0.6, 4.6), round=0.06)
    box("#120a08", (x, y - 0.38, 0.75), (1.4, 0.1, 1.3), round=0.1)
    for dx, turn in ((-0.22, 25), (0.2, -20), (0, 90)):
        cone(DARK_BROWN, (x + dx - 0.3, y - 0.5, 0.14), 0.1, 0.1, 0.7, turn=(0, 90, turn), sides=10)
    flames = []
    for i, (dx, tall, colour) in enumerate(((-0.28, 0.6, ORANGE), (0, 0.85, "#ffb020"), (0.27, 0.55, ORANGE), (-0.1, 0.5, "#ffe070"), (0.12, 0.45, "#ffe070"))):
        f = cone(mat(colour, 0.5, 6.0), (x + dx, y - 0.5 - (0.06 if i > 2 else 0), 0.2), 0.2, 0, tall, sides=10)
        flames.append((f, tall, i * 0.23))
    lamp = light("POINT", (x, y - 1.3, 0.9), 500, "#ff9a3c", 0.5)
    return flames, lamp


def flicker(fire, t, power=500):
    flames, lamp = fire
    for f, tall, phase in flames:
        k = 1 + 0.22 * math.sin(2 * math.pi * (4 * t + phase)) + 0.1 * math.sin(2 * math.pi * (7 * t + phase * 3))
        f.scale = (1 - 0.15 * (k - 1), 1, k)
        f.rotation_euler = (0, math.radians(8 * math.sin(2 * math.pi * (3 * t + phase))), 0)
    lamp.data.energy = power * (1 + 0.14 * math.sin(2 * math.pi * 5 * t) + 0.08 * math.sin(2 * math.pi * 9 * t + 1))


def string_lights(start, end, count=12, sag=0.4):
    """Fairy lights hung between two points. Returns their materials."""
    colours = (RED, GOLD, GREEN, BLUE, ORANGE, PURPLE)
    bulbs = []
    for i in range(count):
        u = (i + 0.5) / count
        at = [a + (b - a) * u for a, b in zip(start, end)]
        at[2] -= sag * 4 * u * (1 - u)
        m = mat(colours[i % len(colours)], 0.3, 5.0, own=True)
        ball(m, at, 0.09)
        bulbs.append(m)
    return bulbs


def blink(bulbs, t, times=2, low=1.5, high=7.0):
    for i, m in enumerate(bulbs):
        glow_of(m, low + (high - low) * (0.5 + 0.5 * math.sin(2 * math.pi * (times * t + i * 0.37))))


def pile(at, count=6, seed=1, spread=0.9, size=0.5, parent=None):
    rng = random.Random(seed)
    made = []
    for i in range(count):
        a = rng.uniform(0, 2 * math.pi)
        r = spread * math.sqrt(rng.random())
        s = size * rng.uniform(0.7, 1.2)
        made.append(present((at[0] + r * math.cos(a), at[1] + r * math.sin(a) * 0.6, at[2]), s, PRESENT_COLOURS[(i + seed) % len(PRESENT_COLOURS)],
                            parent, turn=(0, 0, rng.uniform(0, 90)), shape=(rng.uniform(0.8, 1.4), 1, rng.uniform(0.6, 1.1))))
    return made


def sparkles(count, colour=GOLD, glow=8.0, seed=9):
    """Little lights to scatter about. Returns (ball, random, random, random) each."""
    rng = random.Random(seed)
    m = mat(colour, 0.4, glow)
    pale = mat("#fff6d0", 0.4, glow)
    return [(ball(pale if i % 3 == 0 else m, (0, 0, -50), 0.06), rng.random(), rng.random(), rng.random()) for i in range(count)]


def trail(sparks, t, origin, back=(1, 0, 0), long=3.0, spread=0.5, times=3, size=0.07):
    """Streams sparkles away from origin along back: each is born there, drifts, and fades."""
    for s, a, b, c in sparks:
        age = (times * t + a) % 1.0
        s.location = (origin[0] + back[0] * long * age + (b - 0.5) * spread * age,
                      origin[1] + back[1] * long * age + (c - 0.5) * spread,
                      origin[2] + back[2] * long * age + (c - 0.5) * spread * age - 0.4 * age * age)
        k = size * (1 - age) * (0.6 + 0.8 * b)
        s.scale = (k, k, k)


def fence(start, end, posts=6):
    for i in range(posts):
        u = i / (posts - 1)
        x, y = start[0] + (end[0] - start[0]) * u, start[1] + (end[1] - start[1]) * u
        cone(BROWN, (x, y, 0), 0.07, 0.07, 0.9, sides=8)
        ball(WHITE, (x, y, 0.92), (0.1, 0.1, 0.06))
    long = math.hypot(end[0] - start[0], end[1] - start[1])
    angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
    for z in (0.4, 0.72):
        box(BROWN, ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, z), (long, 0.05, 0.09), turn=(0, 0, angle), round=0.02)


def cloud(at, size=1.0, colour="#8fa4d8", parent=None, glow=0.25):
    root = group(at, parent, size=size)
    m = mat(colour, 0.9, glow)
    for x, z, r in ((0, 0, 0.8), (-0.9, -0.1, 0.6), (0.9, -0.05, 0.65), (-0.4, 0.4, 0.55), (0.45, 0.35, 0.6), (-1.6, -0.2, 0.4), (1.6, -0.2, 0.42)):
        ball(m, (x, 0, z), (r, r * 0.7, r * 0.8), root)
    return root
