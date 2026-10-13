"""Level definitions (data) -> levels/level_N.json + assets/kits/level_N.glb + docs/levels/level_N.png.
Authoring helpers place orbs/enemies in clusters; nothing per-level lives in game code."""
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.geometry import Point
from meshkit import Part, bake, write_json, ROOT, lathe, place, export_glb, ico, extrude
from palette import LEVELS, BASE
from terrain import Rail, terrain_mesh, gap_shape, wall_mesh, debug_map, floor_h, FLOOR_COLS

SHIP_R = 2.0
MIN_GAP = 10 * SHIP_R


# ---------- authoring helpers (cross-section x right, y up, relative to rail) ----------
def orb_line(s0, s1, n, x0, x1, y0=0, y1=0, bend=0.0):
    out = []
    for i in range(n):
        f = i / max(n - 1, 1)
        out.append({"s": s0 + (s1 - s0) * f, "x": x0 + (x1 - x0) * f + bend * math.sin(math.pi * f), "y": y0 + (y1 - y0) * f})
    return out


def orb_ring(s, cx, cy, n=5, r=5.0):
    return [{"s": s + i * 3.0, "x": cx + r * math.cos(2 * math.pi * i / n), "y": cy + r * math.sin(2 * math.pi * i / n)} for i in range(n)]


def group(kind, s, n, cx, cy, spread=9.0, seed=0):
    """Odd-sized clusters with varied heights/depths; never a grid."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a = (i - (n - 1) / 2)
        out.append({"type": kind, "s": s + rng.uniform(-6, 10) + abs(a) * 4,
                    "x": cx + a * spread + rng.uniform(-2, 2), "y": cy + rng.uniform(-3, 4),
                    "phase": round(float(rng.uniform(0, 6.28)), 2)})
    return out


def profile_fn(keys):
    ks = np.array(keys, dtype=float)
    return lambda s: (np.interp(s, ks[:, 0], ks[:, 1]), np.interp(s, ks[:, 0], ks[:, 2]))


# ---------- level 1: Meadow Canyon ----------
def level_1():
    walls = [{"s": 470, "gap": (5, 2, 46, 32)}, {"s": 1260, "gap": (-9, 0, 44, 30)}]
    orbs = (orb_line(95, 215, 5, -10, 10, 0, 2, bend=-4) + orb_ring(430, 5, 2) + orb_line(520, 620, 3, 5, 0, 2, 4)
            + orb_line(790, 900, 5, 8, -8, -2, 4, bend=5) + orb_ring(1222, -9, 0) + orb_line(1320, 1400, 3, -9, 0, 0, 3)
            + orb_line(1600, 1720, 5, -6, 10, 6, 0, bend=-3) + orb_ring(1930, 0, 3, 5, 6) + orb_line(2080, 2180, 4, 4, -4, 0, 6))
    enemies = (group("drifter", 300, 3, 0, 2, seed=1) + group("drifter", 720, 5, -4, 4, seed=2)
               + group("drifter", 1010, 3, -10, -2, seed=3) + group("drifter", 1060, 1, 12, 6, seed=4)
               + group("drifter", 1520, 5, 2, 8, seed=5) + group("drifter", 1830, 3, 6, 0, seed=6))
    return {
        "id": 1, "name": "meadow_canyon", "mode": "air", "speed": 15.0, "seed": 101,
        "ctrl": [(0, 30, 0), (20, 30, -300), (-60, 34, -650), (-40, 38, -1000), (60, 32, -1350),
                 (90, 28, -1700), (20, 30, -2000), (-30, 32, -2300)],
        "profile": [(0, 42, 14), (400, 36, 14), (700, 48, 16), (1000, 32, 13), (1300, 42, 14), (1600, 34, 14), (2400, 42, 15)],
        "ceiling": 18.0, "walls": walls, "orbs": orbs, "enemies": enemies,
        "checkpoints": [0, 680, 1360, 2040], "rest_areas": [[500, 650], [1300, 1450]],
        "music": "music_meadow", "landmark": {"shape": "mesa", "colour": LEVELS[2]["r"][2]},
        "fog": [140, 520],
    }


# ---------- level 2: Sunrise Dunes (HOVER) ----------
def level_2():
    # hover: orb/enemy y is relative to hover height (0 = riding height, +y needs a hop)
    walls = [{"s": 620, "gap": (-4, -3, 38, 26)}]
    rocks = [(260, -9, 3.5, 4), (300, 8, 4.5, 5), (420, 0, 3.0, 3), (880, -12, 5.0, 6), (905, 10, 3.5, 4),
             (1180, 2, 4.0, 4), (1350, -8, 3.0, 3), (1380, 9, 4.5, 5)]
    orbs = (orb_line(80, 200, 5, 0, -6, 0, 0, bend=4) + orb_line(270, 330, 4, -1, 0, 0, 5)  # hop line over rocks
            + orb_ring(585, -4, 1, 5, 3) + orb_line(700, 800, 5, -6, 8, 0, 0, bend=-4)
            + orb_line(1000, 1100, 5, 10, -10, 1, 1) + orb_line(1170, 1200, 3, 2, 2, 2, 6)
            + orb_line(1420, 1540, 5, 8, -4, 0, 2, bend=3) + orb_line(1600, 1680, 4, -4, 4, 0, 0))
    enemies = (group("drifter", 380, 3, 2, 3, seed=11) + group("drifter", 760, 5, 0, 4, seed=12)
               + group("pod", 1050, 1, -14, 0, seed=13) + group("drifter", 1250, 3, -6, 3, seed=14)
               + group("pod", 1480, 1, 13, 0, seed=15) + group("drifter", 1560, 3, 4, 4, seed=16))
    return {
        "id": 2, "name": "sunrise_dunes", "mode": "hover", "speed": 11.0, "seed": 202, "dune": 3.5, "side": (30, 48),
        "ctrl": [(0, 10, 0), (-40, 10, -250), (10, 12, -560), (80, 10, -850), (60, 8, -1150), (-20, 10, -1450), (-50, 10, -1760)],
        "profile": [(0, 34, 6), (500, 30, 6), (900, 38, 6), (1300, 30, 6), (1800, 34, 6)],
        "ceiling": 12.0, "walls": walls, "rocks": rocks, "orbs": orbs, "enemies": enemies,
        "checkpoints": [0, 500, 1000, 1500], "rest_areas": [[640, 700], [1210, 1330]],
        "music": "music_dunes", "landmark": {"shape": "peak", "colour": LEVELS[3]["r"][3]},
        "fog": [110, 420],
    }


# ---------- level 3: Cloud Ridge (AIR) — gap-threading is the star ----------
def level_3():
    walls = [{"s": 450, "gap": (8, 4, 34, 26)}, {"s": 1120, "gap": (-10, -2, 30, 30)}, {"s": 1780, "gap": (4, 6, 28, 24)}]
    orbs = (orb_line(90, 200, 5, -8, 8, 4, 8, bend=3) + orb_ring(412, 8, 4) + orb_line(540, 640, 4, 6, -4, 2, -2)
            + orb_line(800, 920, 5, -12, 6, 0, 6, bend=-4) + orb_ring(1082, -10, -2) + orb_line(1250, 1350, 4, -6, 6, 0, 0)
            + orb_ring(1742, 4, 6, 5, 4) + orb_line(1900, 2050, 5, 0, 10, 6, 2, bend=4) + orb_line(2150, 2250, 3, 6, 0, 0, 0))
    enemies = (group("drifter", 300, 3, -4, 6, seed=21) + group("pod", 620, 1, -18, 0, seed=22) + group("pod", 660, 1, 16, 0, seed=23)
               + group("drifter", 860, 5, 4, 2, seed=24) + group("pod", 1400, 3, 0, 0, spread=14, seed=25)
               + group("drifter", 1550, 3, -8, 8, seed=26) + group("drifter", 2000, 5, 6, 0, seed=27))
    return {
        "id": 3, "name": "cloud_ridge", "mode": "air", "speed": 15.0, "seed": 303, "side": (110, 140),
        "ctrl": [(0, 40, 0), (-50, 42, -320), (10, 48, -680), (90, 44, -1000), (60, 40, -1350), (-30, 46, -1700),
                 (-60, 44, -2000), (0, 40, -2320)],
        "profile": [(0, 40, 15), (500, 34, 15), (900, 44, 16), (1300, 32, 14), (1700, 38, 15), (2400, 40, 15)],
        "ceiling": 18.0, "walls": walls, "orbs": orbs, "enemies": enemies,
        "checkpoints": [0, 680, 1360, 2040], "rest_areas": [[520, 620], [1200, 1330]],
        "music": "music_ridge", "landmark": {"shape": "spire", "colour": LEVELS[4]["r"][3]}, "fog": [150, 560],
    }


# ---------- level 4: Crystal River (HOVER) — narrower, Buzzers, arches ----------
def level_4():
    walls = [{"s": 520, "gap": (-3, -4, 30, 22)}, {"s": 1180, "gap": (5, -3, 30, 24)}]
    rocks = [(240, 8, 3.0, 6), (330, -7, 3.5, 7), (760, 0, 3.0, 5), (900, -9, 3.0, 6), (930, 9, 3.0, 7),
             (1350, -4, 3.5, 6), (1500, 7, 3.0, 5), (1620, -8, 3.0, 6)]
    orbs = (orb_line(80, 190, 5, -4, 4, 0, 0, bend=-3) + orb_line(300, 360, 3, 0, 0, 1, 5) + orb_ring(485, -3, 0, 5, 3)
            + orb_line(600, 700, 5, -6, 6, 0, 0, bend=3) + orb_line(800, 870, 3, -5, 5, 2, 2) + orb_ring(1145, 5, 1, 5, 3)
            + orb_line(1260, 1340, 4, 6, -6, 0, 0) + orb_line(1420, 1480, 3, 0, 0, 2, 6) + orb_line(1560, 1700, 6, -6, 6, 0, 1, bend=-4))
    enemies = (group("buzzer", 400, 1, 0, 4, seed=41) + group("drifter", 640, 3, 0, 3, spread=7, seed=42)
               + group("buzzer", 980, 3, 0, 4, spread=8, seed=43) + group("drifter", 1300, 5, 0, 3, spread=6, seed=44)
               + group("buzzer", 1580, 1, 4, 5, seed=45))
    return {
        "id": 4, "name": "crystal_river", "mode": "hover", "speed": 11.0, "seed": 404, "dune": 1.5, "side": (60, 80),
        "rock_style": "crystal",
        "ctrl": [(0, 10, 0), (30, 10, -280), (-30, 11, -600), (-80, 10, -900), (-40, 9, -1200), (30, 10, -1480), (40, 10, -1760)],
        "profile": [(0, 28, 6), (400, 24, 6), (800, 30, 6), (1200, 24, 6), (1800, 28, 6)],
        "ceiling": 12.0, "walls": walls, "rocks": rocks, "orbs": orbs, "enemies": enemies,
        "checkpoints": [0, 500, 1000, 1500], "rest_areas": [[540, 600], [1190, 1250]],
        "music": "music_crystal", "landmark": {"shape": "island", "colour": LEVELS[5]["r"][3]}, "fog": [110, 420],
    }


# ---------- level 5: Mist Peaks (AIR) — floating islands, sliding gaps, mixed critters ----------
def level_5():
    walls = [{"s": 700, "gap": (0, 2, 26, 26), "move": [8, 9]}, {"s": 1520, "gap": (-4, 0, 24, 24), "move": [9, 11]}]
    orbs = (orb_line(80, 200, 5, 6, -6, 2, 6, bend=4) + orb_line(330, 430, 5, -10, 10, 0, 0, bend=-5)
            + orb_ring(660, 0, 2) + orb_line(800, 900, 4, 0, -10, 4, 8) + orb_line(1050, 1180, 5, -8, 8, 0, 4, bend=3)
            + orb_ring(1480, -4, 0) + orb_line(1650, 1760, 5, 8, -8, 6, 0) + orb_line(1950, 2100, 5, 0, 0, -4, 8, bend=6))
    enemies = (group("drifter", 280, 3, 0, 4, seed=51) + group("buzzer", 520, 1, -8, 6, seed=52) + group("pod", 900, 1, 18, 0, seed=53)
               + group("drifter", 1000, 5, -4, 2, seed=54) + group("buzzer", 1300, 3, 4, 4, spread=10, seed=55)
               + group("pod", 1800, 3, 0, 0, spread=16, seed=56) + group("drifter", 2050, 3, 6, 6, seed=57))
    islands = [(150, -75, 40, 18), (420, 90, 60, 24), (760, -100, 30, 14), (980, 80, 20, 30), (1250, -85, 55, 22),
               (1600, 95, 35, 16), (1850, -70, 70, 26), (2150, 110, 45, 20)]
    return {
        "id": 5, "name": "mist_peaks", "mode": "air", "speed": 15.0, "seed": 505, "side": (120, 150), "islands": islands,
        "ctrl": [(0, 40, 0), (40, 40, -330), (-20, 44, -700), (-90, 40, -1050), (-50, 38, -1400), (40, 42, -1750),
                 (60, 40, -2050), (0, 40, -2340)],
        "profile": [(0, 40, 15), (600, 34, 15), (1000, 42, 16), (1500, 32, 14), (2400, 40, 15)],
        "ceiling": 18.0, "walls": walls, "orbs": orbs, "enemies": enemies,
        "checkpoints": [0, 680, 1360, 2040], "rest_areas": [[730, 790], [1550, 1640]],
        "music": "music_mist", "landmark": {"shape": "ring", "colour": LEVELS[6]["w"][3]}, "fog": [100, 430],
    }


# ---------- level 6: Sky Gate (AIR) — level 1's canyon at giant scale, the Guardian, sunrise ----------
def level_6():
    walls = [{"s": 700, "gap": (6, 2, 24, 24)}, {"s": 1350, "gap": (-6, 4, 22, 22)}]
    gate = 2200
    orbs = (orb_line(90, 220, 5, -10, 10, 0, 2, bend=-4) + orb_ring(662, 6, 2) + orb_line(800, 920, 5, 8, -8, -2, 4, bend=5)
            + orb_ring(1312, -6, 4) + orb_line(1450, 1560, 5, -6, 10, 6, 0, bend=-3) + orb_line(1700, 1820, 5, 4, -4, 0, 6)
            + orb_ring(gate - 20, 0, 0, 8, 10))
    enemies = (group("drifter", 320, 3, 0, 2, seed=61) + group("buzzer", 520, 1, 6, 6, seed=62) + group("pod", 1000, 1, -20, 0, seed=63)
               + group("drifter", 1100, 5, -2, 4, seed=64) + group("drifter", 1600, 3, 8, 0, seed=65)
               + [{"type": "guardian", "s": gate - 50, "x": 0.0, "y": 6.0, "phase": 0.0}])
    return {
        "id": 6, "name": "sky_gate", "mode": "air", "speed": 15.0, "seed": 101, "side": (180, 230),
        "ctrl": [(0, 30, 0), (20, 30, -300), (-60, 34, -650), (-40, 38, -1000), (60, 32, -1350),
                 (90, 28, -1700), (20, 30, -2000), (-10, 30, -2330)],
        "profile": [(0, 52, 18), (700, 46, 18), (1350, 50, 18), (2000, 58, 20), (2400, 58, 20)],
        "ceiling": 20.0, "walls": walls, "orbs": orbs, "enemies": enemies, "gate": gate, "guardian_hold": gate - 130,
        "checkpoints": [0, 680, 1360, 2040], "rest_areas": [[720, 790], [1380, 1440]],
        "music": "music_gate", "landmark": {"shape": "mesa", "colour": LEVELS[1]["r"][2]}, "fog": [160, 620],
    }


DEFS = {1: level_1, 2: level_2, 3: level_3, 4: level_4, 5: level_5, 6: level_6}


def rock_mesh(r, h, seed, ramp_, style="rock"):
    rng = np.random.default_rng(seed)
    if style == "crystal":  # cluster of 3 tilted hexagonal prisms with pointed tips
        parts = []
        for k in range(3):
            hk = h * rng.uniform(0.6, 1.3)
            c = lathe([(0, 0), (r * 0.45, 0), (r * 0.45, hk * 0.75), (0, hk)], 6)
            c = place(c, (rng.uniform(-r, r) * 0.5, 0, rng.uniform(-r, r) * 0.5), (rng.uniform(-20, 20), rng.uniform(0, 60), rng.uniform(-20, 20)))
            parts.append(Part(c, ramp_, 2 + (k == 0)))
        return bake(parts)
    m = ico(1, 1)
    m.vertices *= rng.uniform(0.8, 1.15, (len(m.vertices), 1))  # per-vertex jitter: no two rocks alike
    m.apply_scale([r, h, r * rng.uniform(0.8, 1.2)])
    m.apply_translation([0, h * 0.35, 0])
    return bake([Part(m, ramp_, 2)])


def island(r, seed, rock, moss):
    """Floating island: rough cone underside + flat mossy top (a deliberate motif, so it may float)."""
    rng = np.random.default_rng(seed)
    under = lathe([(0, -r * 1.3), (r * 0.35, -r * 0.9), (r * 0.8, -r * 0.3), (r, 0), (0, 0.01)], 7)
    under.vertices[:, [0, 2]] *= rng.uniform(0.85, 1.15, (len(under.vertices), 1))
    top = place(lathe([(0, 0), (r * 0.98, 0), (r * 0.9, r * 0.12), (0, r * 0.14)], 7), (0, 0, 0))
    return bake([Part(under, rock, 2), Part(top, moss, 3)])


def ring_mesh(rail, s, R, r, thick=6.0):
    """A ring standing across the rail (the Sky Gate)."""
    poly = Point(0, 0).buffer(R, 16).difference(Point(0, 0).buffer(r, 16))
    m = extrude(poly, thick)
    t, rr = rail.frame(np.array([s]))
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = rr[0], [0, 1, 0], -t[0], rail.pos(np.array([s]))[0]
    m.apply_transform(M)
    return m


def landmark(kind, colour):
    if kind == "mesa":
        m = lathe([(0, 0), (90, 0), (75, 60), (55, 85), (0, 88)], 9)
    elif kind == "spire":
        m = lathe([(0, 0), (40, 0), (28, 120), (6, 230), (0, 240)], 6)
    elif kind == "island":
        return island(70, 5, [colour] * 5, [colour] * 5)
    elif kind == "ring":
        m = trimesh.creation.annulus(60, 90, 20)
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        m.apply_translation([0, 120, 0])
    else:
        m = lathe([(0, 0), (60, 0), (20, 140), (0, 150)], 7)
    return bake([Part(m, [colour] * 5, 2)])


def build_level(d) -> dict:
    n = d["id"]
    pal = LEVELS[n]
    rail = Rail(d["ctrl"])
    prof = profile_fn(d["profile"])
    meshes = {}
    dune = d.get("dune", 0.0)
    for i, ch in enumerate(terrain_mesh(rail, prof, pal, d["seed"], dune, d.get("side", (70, 95)))):
        meshes[f"terrain_{i}"] = ch
    walls_json = []
    for i, w in enumerate(d["walls"]):
        cx, cy, gw, gh = w["gap"]
        assert gw >= MIN_GAP and gh >= MIN_GAP, f"gap too small in level {n}"
        gap = gap_shape(cx, cy, gw, gh, d["seed"] + 50 + i)
        _, F = prof(np.array([w["s"]]))
        slab, trim = wall_mesh(rail, w["s"], gap, float(F[0]), d["seed"] + 60 + i)
        meshes[f"wall_{i}"] = bake([Part(slab, pal["w"], 2)])
        meshes[f"trim_{i}"] = bake([Part(trim, BASE["e"], 1, glow=True)])
        safe = gap.buffer(-SHIP_R - 0.3)
        walls_json.append({"s": w["s"], "gap": [list(map(lambda v: round(v, 2), p)) for p in safe.exterior.coords],
                           "centre": [round(safe.centroid.x, 2), round(safe.centroid.y, 2)], "thickness": 10.0,
                           "move": w.get("move", [0, 1])})  # [amplitude m, period s]: slow sideways slide
    def floor_at(sv, x):
        _, Fv = prof(np.array([sv]))
        w = float(prof(np.array([sv]))[0][0])
        u = np.clip((x / w + 1) * 2, 0, 3.999)
        j = int(u)
        a = floor_h(np.array([sv]), FLOOR_COLS[j], Fv, d["seed"], dune)[0]
        b = floor_h(np.array([sv]), FLOOR_COLS[j + 1], Fv, d["seed"], dune)[0]
        return float(a + (b - a) * (u - j))

    rocks_json = []
    for i, (rs, rx, rr, rh) in enumerate(d.get("rocks", [])):
        t, r = rail.frame(np.array([rs]))
        fy = floor_at(rs, rx)
        m = rock_mesh(rr, rh, d["seed"] + 300 + i, pal.get("c", pal["r"]), d.get("rock_style", "rock"))
        ang = np.arctan2(-t[0][0], -t[0][2])
        m.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 1, 0]))
        m.apply_translation(rail.pos(np.array([rs]))[0] + r[0] * rx + np.array([0, fy, 0]))
        meshes[f"rock_{i}"] = m
        rocks_json.append({"s": rs, "x": rx, "r": rr, "top": round(fy + rh * 1.2, 2)})
    if d["mode"] == "hover":  # content heights are relative to riding height (floor + 3 m)
        for o in d["orbs"]:
            o["y"] = round(floor_at(o["s"], o["x"]) + 3.0 + o["y"], 2)
        for e in d["enemies"]:
            if e["type"] != "pod":
                e["y"] = round(floor_at(e["s"], e["x"]) + 3.0 + e["y"], 2)
    for i, (is_, ix, iy, ir) in enumerate(d.get("islands", [])):
        _, r = rail.frame(np.array([is_]))
        m = island(ir, d["seed"] + 400 + i, pal["r"], pal["m"])
        m.apply_translation(rail.pos(np.array([is_]))[0] + r[0] * ix + np.array([0, iy, 0]))
        meshes[f"island_{i}"] = m
    gate_json = None
    if "gate" in d:
        gs = d["gate"]
        meshes["gate_0"] = bake([Part(ring_mesh(rail, gs, 90, 72), pal["w"], 2)])
        gate_json = {"s": gs}
    # landmark beyond the end of the rail, in the fog
    t, _ = rail.frame(np.array([rail.length]))
    lp = rail.pos(np.array([rail.length]))[0] + t[0] * 700 + np.array([0, -60, 0])
    lm = landmark(d["landmark"]["shape"], d["landmark"]["colour"])
    lm.apply_translation(lp)
    meshes["landmark"] = lm
    # export one glb, many nodes
    scene = trimesh.Scene()
    tris = 0
    for name, m in meshes.items():
        scene.add_geometry(m, node_name=name, geom_name=name)
        tris += len(m.faces)
    out = ROOT / f"assets/kits/level_{n}.glb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(scene.export(file_type="glb"))
    # rail samples every 5 m: x,y,z,w,f
    ss = np.arange(0, rail.length, 5.0)
    P = rail.pos(ss)
    W, F = prof(ss)
    lvl = {k: d[k] for k in ("id", "name", "mode", "speed", "ceiling", "orbs", "enemies", "checkpoints",
                             "rest_areas", "music", "fog")}
    cols = np.array([floor_h(ss, o, F, d["seed"], dune) for o in FLOOR_COLS]).T  # (S, 5)
    lvl.update({"gate": gate_json, "guardian_hold": d.get("guardian_hold"),
                "length": round(rail.length, 1), "walls": walls_json, "palette": pal, "rocks": rocks_json,
                "rail": [[round(float(v), 2) for v in (*P[i], W[i], F[i], *(cols[i] if dune else []))] for i in range(len(ss))]})
    write_json(ROOT / f"levels/level_{n}.json", lvl)
    (ROOT / "docs/levels").mkdir(parents=True, exist_ok=True)
    debug_map(rail, prof, lvl, ROOT / f"docs/levels/level_{n}.png")
    curv = rail.max_curvature()
    assert curv < 1 / 250, f"level {n}: rail too sharp ({1/curv:.0f} m radius)"
    return {"level": n, "tris": tris, "length": round(rail.length), "orbs": len(lvl["orbs"]),
            "enemies": len(lvl["enemies"]), "min_radius_m": round(1 / curv)}


def build(ids=None):
    return [build_level(DEFS[i]()) for i in (ids or DEFS)]


if __name__ == "__main__":
    for r in build():
        print(r)
