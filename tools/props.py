"""Biome props: small kit pieces placed in odd-sized clusters OUTSIDE the corridor, sitting on the terrain.
Each kind has its own silhouette; per-instance seeds vary every copy. All baked with thin outlines."""
import numpy as np
import trimesh
from shapely.geometry import Polygon
from meshkit import Part, bake, lathe, ico, place, extrude_profile_x, extrude_top_y, mirror_x
from palette import BASE

OUT = 0.12  # outline width for props (m)


def tree(rng, pal):
    h = rng.uniform(10, 17)
    trunk = lathe([(0, 0), (1.0, 0), (0.6, h * 0.6), (0, h * 0.62)], 5)
    blobs = [Part(trunk, pal["r"], 1)]
    for k in range(rng.integers(1, 4)):  # 1-3 soft lollipop blobs, never identical
        r = rng.uniform(3.4, 5.2)
        c = place(ico(1, 0), (rng.uniform(-1.2, 1.2), h * 0.62 + r * 0.5 + k * 1.6, rng.uniform(-1.2, 1.2)),
                  scale=(r, r * rng.uniform(0.8, 1.05), r))
        blobs.append(Part(c, pal["m"], 3))
    return bake(blobs, outline=OUT), 5.0


def boulder(rng, pal):
    r = rng.uniform(3.0, 7.0)
    m = ico(1, 1)
    m.vertices *= rng.uniform(0.75, 1.15, (len(m.vertices), 1))
    m.apply_scale([r, r * rng.uniform(0.5, 0.8), r * rng.uniform(0.8, 1.2)])
    parts = [Part(m, pal["r"], 2)]
    if rng.random() < 0.5:  # moss on the top (imperfection tells the story)
        moss = place(ico(1, 0), (0, r * 0.55, 0), scale=(r * 0.7, r * 0.18, r * 0.7))
        parts.append(Part(moss, pal["m"], 3))
    return bake(parts, outline=OUT), r


def bush(rng, pal):
    parts = []
    for k in range(rng.integers(3, 6)):
        a = rng.uniform(0, 6.28)
        h = rng.uniform(2.5, 4.5)
        parts.append(Part(place(lathe([(0, 0), (0.35, 0), (0, h)], 4), (np.cos(a) * 0.7, 0, np.sin(a) * 0.7),
                                (rng.uniform(-25, 25), 0, rng.uniform(-25, 25))), pal["m"], 1 + k % 3))
    return bake(parts, outline=OUT * 0.6), 1.5


def crystal(rng, pal):
    parts = []
    ramp_ = pal.get("c", pal["r"])
    for k in range(3):
        hk = rng.uniform(6, 13)
        c = lathe([(0, 0), (1.8, 0), (1.2, hk * 0.75), (0, hk)], 6)
        parts.append(Part(place(c, (rng.uniform(-1.5, 1.5), 0, rng.uniform(-1.5, 1.5)),
                                (rng.uniform(-22, 22), rng.uniform(0, 60), rng.uniform(-22, 22))), ramp_, 2 + (k == 0)))
    return bake(parts, outline=OUT), 3.0


def cloud(rng, pal):
    parts = []
    w = rng.uniform(10, 18)
    for k in range(rng.integers(3, 6)):
        r = rng.uniform(3, 6)
        parts.append(Part(place(ico(1, 1), (rng.uniform(-w / 2, w / 2), rng.uniform(0, 2), rng.uniform(-3, 3)),
                                scale=(r * 1.3, r * 0.7, r)), ["#c9d6ea", "#dfe8f5", "#eef3fb", "#f8fbff", "#ffffff"], 3))
    return bake(parts), w / 2 + 6


def wreck(rng, pal):
    """An old crashed skimmer, half-buried and patched: a little story in the canyon."""
    hull = extrude_profile_x(Polygon([(-4, 0), (-2.5, 1.2), (2.5, 1.4), (4.5, 0.8), (4.5, -0.6), (-3, -0.6)]), 2.4)
    wing = extrude_top_y(Polygon([(1, -1), (6, 1.5), (5.6, 2.6), (1, 2.2)]), 0.3)
    patch = place(trimesh.creation.box((1.2, 0.1, 1.0)), (0.6, 1.35, 0.2), (0, 20, 0))
    m = [Part(hull, ["#8a8aa8", "#a3a3bd", "#bcbcd0", "#d3d3e0", "#e8e8f0"], 2),
         Part(wing, ["#8a8aa8", "#a3a3bd", "#bcbcd0", "#d3d3e0", "#e8e8f0"], 1),
         Part(patch, BASE["t"], 3)]
    mesh = bake(m, outline=OUT)
    mesh.apply_transform(trimesh.transformations.euler_matrix(0.25, rng.uniform(0, 6.28), 0.35))
    mesh.apply_translation([0, -0.8, 0])  # half-buried
    return mesh, 6.0


KINDS = {"tree": tree, "boulder": boulder, "bush": bush, "crystal": crystal, "cloud": cloud, "wreck": wreck}

# per level: (kind, clusters, cluster size choices, (min, max) distance beyond the corridor edge, height offset)
RECIPES = {
    1: [("tree", 22, (1, 3, 5), (0, 12), 0), ("boulder", 16, (1, 3), (0, 8), 0), ("bush", 10, (3, 5), (0, 6), 0),
        ("wreck", 1, (1,), (1, 3), 0)],
    2: [("boulder", 18, (1, 3, 5), (0, 10), 0), ("bush", 20, (3, 5), (0, 8), 0)],
    3: [("boulder", 18, (1, 3), (0, 10), 0), ("cloud", 16, (1, 3), (5, 40), -6), ("tree", 8, (1, 3), (0, 8), 0)],
    4: [("crystal", 26, (1, 3, 5), (0, 10), 0), ("boulder", 8, (1, 3), (0, 8), 0)],
    5: [("boulder", 16, (1, 3), (0, 10), 0), ("tree", 14, (1, 3), (0, 10), 0), ("cloud", 10, (1, 3), (10, 50), -4)],
    6: [("tree", 22, (3, 5), (0, 16), 0), ("boulder", 16, (1, 3, 5), (0, 12), 0), ("bush", 10, (3, 5), (0, 6), 0),
        ("wreck", 1, (1,), (1, 3), 0)],
}
