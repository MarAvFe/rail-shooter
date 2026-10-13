"""Level definitions (data) -> levels/level_N.json + assets/kits/level_N.glb + docs/levels/level_N.png.
Authoring helpers place orbs/enemies in clusters; nothing per-level lives in game code."""
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon
from meshkit import Part, bake, write_json, ROOT, lathe, place, export_glb, ico
from palette import LEVELS, BASE
from terrain import Rail, terrain_mesh, gap_shape, wall_mesh, debug_map

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


DEFS = {1: level_1}


def landmark(kind, colour):
    if kind == "mesa":
        m = lathe([(0, 0), (90, 0), (75, 60), (55, 85), (0, 88)], 9)
    else:
        m = lathe([(0, 0), (60, 0), (20, 140), (0, 150)], 7)
    return bake([Part(m, [colour] * 5, 2)])


def build_level(d) -> dict:
    n = d["id"]
    pal = LEVELS[n]
    rail = Rail(d["ctrl"])
    prof = profile_fn(d["profile"])
    meshes = {}
    for i, ch in enumerate(terrain_mesh(rail, prof, pal, d["seed"])):
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
                           "centre": [round(safe.centroid.x, 2), round(safe.centroid.y, 2)], "thickness": 10.0})
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
    lvl.update({"length": round(rail.length, 1), "walls": walls_json, "palette": pal,
                "rail": [[round(float(v), 2) for v in (*P[i], W[i], F[i])] for i in range(len(ss))]})
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
