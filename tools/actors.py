"""Ships, enemies, pickups. Each build_* returns (mesh, collision_or_None). Seeds per element, fixed."""
import numpy as np
from shapely.geometry import Polygon, Point
from shapely import affinity
import trimesh
from meshkit import (Part, bake, extrude, extrude_profile_x, extrude_top_y, visual_hull, lathe, ico,
                     place, mirror_x, export_glb, ROOT)
from palette import BASE, COLOURWAYS, ramp

E = BASE["e"]


# ---------- Kite (air): wide swept delta, short nose, twin engines ----------
def kite(hull=None):
    h, t, g = hull or BASE["h"], BASE["t"], BASE["g"]
    side = Polygon([(-3.2, 0.1), (-1.6, 0.55), (0.6, 0.75), (2.8, 0.45), (2.9, -0.3), (-1.0, -0.4), (-3.0, -0.15)])
    top = Polygon([(0, -3.3), (0.7, -1.2), (0.9, 2.9), (-0.9, 2.9), (-0.7, -1.2)])
    body = visual_hull(side, top, 2.0, 2.0)
    # swept wing, right side (x>0), top-view polygon (x, z); with a notch at the trailing edge (wear/identity)
    wing = Polygon([(0.5, -0.6), (4.6, 2.0), (4.4, 2.7), (3.2, 2.5), (2.9, 2.2), (0.5, 2.3)])
    wing_r = place(extrude_top_y(wing, 0.22), (0, -0.05, 0))
    tip = place(extrude_top_y(Polygon([(4.1, 1.7), (4.7, 1.95), (4.6, 2.8), (4.1, 2.6)]), 0.6), (0, 0.15, 0))
    eng = lathe([(0.0, 0), (0.42, 0.1), (0.48, 1.0), (0.36, 1.6), (0.0, 1.65)], 8)
    eng_r = place(eng, (1.25, 0.05, 1.4), (90, 0, 0))
    nozzle = place(lathe([(0.0, 0), (0.32, 0.0), (0.32, 0.12), (0.0, 0.12)], 8), (1.25, 0.05, 3.05), (90, 0, 0))
    canopy = place(ico(1, 1), (0, 0.62, -0.6), scale=(0.55, 0.38, 1.2))
    parts = [Part(body, h), Part(wing_r, h, 2), Part(mirror_x(wing_r), h, 2),
             Part(tip, t, 2), Part(mirror_x(tip), t, 2),
             Part(eng_r, t, 1), Part(mirror_x(eng_r), t, 1),
             Part(nozzle, E, 1, glow=True), Part(mirror_x(nozzle), E, 1, glow=True),
             Part(canopy, g, 2)]
    glow = [(np.array([1.25, 0.05, 3.1]), 1.6), (np.array([-1.25, 0.05, 3.1]), 1.6)]
    return bake(parts, glow), body


# ---------- Sled (hover): low rounded slab, wide skirt, one rear engine ----------
def sled(hull=None):
    h, t, g = hull or BASE["x"], BASE["t"], BASE["g"]
    top = Point(0, 0).buffer(1, 8)
    top = affinity.scale(top, 2.0, 3.0)
    body = place(extrude_top_y(top, 1.1), (0, 0.35, 0))
    skirt = place(extrude_top_y(affinity.scale(Point(0, 0).buffer(1, 8), 2.5, 3.2), 0.4), (0, -0.4, 0))
    canopy = place(ico(1, 1), (0, 0.95, -0.9), scale=(0.9, 0.5, 1.1))
    eng = place(lathe([(0, 0), (0.6, 0.0), (0.7, 0.9), (0.0, 1.0)], 8), (0, 0.5, 2.5), (90, 0, 0))
    noz = place(lathe([(0, 0), (0.45, 0), (0.45, 0.1), (0, 0.1)], 8), (0, 0.5, 3.45), (90, 0, 0))
    fin = place(extrude_profile_x(Polygon([(1.6, 0.9), (2.9, 0.9), (3.0, 2.0), (2.5, 2.0)]), 0.2), (0.0, 0, 0))
    patch = place(trimesh.creation.box((0.6, 0.06, 0.5)), (1.1, 0.92, 0.6), (0, 15, 0))  # patched hull
    parts = [Part(skirt, t, 1), Part(body, h), Part(canopy, g, 2), Part(eng, t, 1),
             Part(noz, E, 1, glow=True), Part(fin, h, 2), Part(patch, t, 3)]
    return bake(parts, [(np.array([0, 0.5, 3.5]), 1.8)]), place(trimesh.creation.box((5, 2, 6.4)))


# ---------- Enemies ----------
def _face(z_front: float, y: float, s: float, grumpy: bool = True):
    """Friendly-grumpy face: two round eyes + slanted brows. Returns parts placed on the -Z front."""
    dk, wh = BASE["face"]
    out = []
    for sx in (-1, 1):
        out.append(Part(place(ico(1, 1), (sx * 0.38 * s, y, z_front), scale=(0.24 * s, 0.28 * s, 0.1 * s)), [wh] * 3, 1))
        out.append(Part(place(ico(1, 0), (sx * 0.36 * s, y - 0.03 * s, z_front - 0.06 * s), scale=(0.11 * s, 0.13 * s, 0.06 * s)), [dk] * 3, 1))
        if grumpy:
            out.append(Part(place(trimesh.creation.box((0.34 * s, 0.07 * s, 0.08 * s)),
                                  (sx * 0.38 * s, y + 0.3 * s, z_front), (0, 0, sx * 14)), [dk] * 3, 1))
    return out


def drifter():
    d = BASE["d"]
    body = place(ico(1, 2), scale=(1.5, 1.3, 1.4))
    fin = place(extrude_profile_x(Polygon([(-0.3, 0), (0.6, 0), (0.9, 0.9), (0.1, 0.5)]), 0.25), (1.45, 0.1, 0), (0, 0, -35))
    tuft = place(lathe([(0, 0), (0.25, 0.1), (0.05, 0.6), (0, 0.62)], 6), (0.2, 1.2, 0), (0, 0, -15))
    parts = [Part(body, d), Part(fin, d, 3), Part(mirror_x(fin), d, 3), Part(tuft, d, 1)] + _face(-1.33, 0.2, 1.4)
    return bake(parts), body


def pod():
    p = BASE["p"]
    stalk = lathe([(0, 0), (0.7, 0), (0.5, 1.5), (0.45, 3.0), (0, 3.05)], 8)
    cap = place(lathe([(0, 0), (1.9, 0.05), (1.7, 0.7), (0.9, 1.3), (0, 1.45)], 10), (0, 2.8, 0))
    spots = [Part(place(ico(0.32, 0), (np.cos(a) * 1.1, 3.6 + 0.2 * np.sin(3 * a), np.sin(a) * 1.1)), E, 0, glow=True)
             for a in np.linspace(0.3, 6.0, 4)]
    parts = [Part(stalk, p, 1), Part(cap, p, 3)] + spots + _face(-0.48, 2.1, 1.0)
    return bake(parts), cap


def buzzer():
    b = BASE["b"]
    cres = Point(0, 0).buffer(2.0, 12).difference(Point(0.9, 0.5).buffer(1.7, 12))
    m = place(extrude_profile_x(cres, 0.9), (0, 0, 0), (0, 90, 0))
    wing = place(extrude_top_y(Polygon([(0, 0), (1.6, -0.4), (1.4, 0.5)]), 0.08), (0.3, 0.6, 0))
    parts = [Part(m, b), Part(wing, BASE["g"], 3), Part(mirror_x(wing), BASE["g"], 3)] + _face(-0.47, -0.3, 0.8)
    return bake(parts), m


def guardian():
    u = BASE["u"]
    dome = place(ico(1, 3), scale=(12, 9, 11))
    belly = place(lathe([(0, 0), (9, 0.5), (11, 3), (0, 3.2)], 14), (0, -6, 0))
    horns = [place(ico(1, 1), (sx * 7, 7.2, 1), (0, 0, -sx * 30), scale=(2.4, 1.6, 1.4)) for sx in (-1, 1)]  # round ears, not horns
    parts = [Part(dome, u), Part(belly, u, 1)] + [Part(h, BASE["t"], 2) for h in horns] + _face(-10.6, 1.5, 7.0)
    return bake(parts), dome


def orb():
    gem = place(ico(1, 1), scale=(0.9, 1.2, 0.9))  # drawn ~2.5x real size
    return bake([Part(gem, E, 1, glow=True)]), None


BUILDERS = {
    "ships/ship_air_kite": kite, "ships/ship_hover_sled": sled,
    "enemies/enemy_drifter": drifter, "enemies/enemy_pod": pod, "enemies/enemy_buzzer": buzzer,
    "enemies/enemy_guardian": guardian, "fx/pickup_orb": orb,
}
BUDGET = {"ships": 1500, "enemies": 700, "fx": 300, "enemy_guardian": 4000}


SLED_WAYS = [BASE["x"], ramp(45, 0.55), ramp(175, 0.40)]
for _i in range(3):  # colourways: palette swap of the hull ramp only
    BUILDERS[f"ships/ship_air_kite_c{_i}"] = (lambda i=_i: kite(COLOURWAYS[i]))
    BUILDERS[f"ships/ship_hover_sled_c{_i}"] = (lambda i=_i: sled(SLED_WAYS[i]))
del BUILDERS["ships/ship_air_kite"], BUILDERS["ships/ship_hover_sled"]


def build() -> list[dict]:
    report = []
    for rel, fn in BUILDERS.items():
        mesh, col = fn()
        name = rel.split("/")[-1]
        r = export_glb(mesh, ROOT / f"assets/{rel}.glb", name, col)
        r["budget"] = BUDGET.get(name, BUDGET[rel.split("/")[0]])
        report.append(r)
    return report


if __name__ == "__main__":
    for r in build():
        print(r)
