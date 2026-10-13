"""Level geometry: rail spline -> canyon ribbon terrain, sky walls with gaps, level JSON, debug map.

Rail frame at distance s: T (forward), R = T x UP (right), U = UP. Cross-section coords (x right, y up)
are relative to the rail point. Corridor: |x| < w(s), floor at y = -f(s).
"""
import math
import numpy as np
import trimesh
from scipy.interpolate import CubicSpline
from shapely.geometry import Polygon, box
from shapely import affinity
from PIL import Image, ImageDraw
from meshkit import Part, bake, extrude, hex_rgb, write_json, ROOT, lathe, place, ico

UP = np.array([0.0, 1.0, 0.0])
STEP = 6.0  # terrain sample spacing along the rail (m)
OUTER = [8, 22, 45, 80, 130, 190]  # ribbon columns beyond the corridor edge (m)


class Rail:
    def __init__(self, ctrl: list[tuple[float, float, float]]):
        c = np.array(ctrl, dtype=float)
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
        sp = CubicSpline(d, c, bc_type="natural")
        dense = sp(np.linspace(0, d[-1], int(d[-1] / 0.5)))
        seg = np.linalg.norm(np.diff(dense, axis=0), axis=1)
        self.s_dense = np.r_[0, np.cumsum(seg)]
        self.p_dense = dense
        self.length = float(self.s_dense[-1])

    def pos(self, s):
        s = np.clip(s, 0, self.length)
        return np.array([np.interp(s, self.s_dense, self.p_dense[:, i]) for i in range(3)]).T

    def frame(self, s):
        s = np.clip(s, 1, self.length - 1)
        a, b = self.pos(np.maximum(s - 1, 0)), self.pos(np.minimum(s + 1, self.length))
        t = (b - a)
        t = t / np.linalg.norm(t, axis=-1, keepdims=True)
        r = np.cross(t, UP)
        r = r / np.linalg.norm(r, axis=-1, keepdims=True)
        return t, r

    def max_curvature(self) -> float:
        s = np.arange(2, self.length - 2, 4.0)
        t, _ = self.frame(s)
        ang = np.arccos(np.clip((t[1:] * t[:-1]).sum(-1), -1, 1))
        return float((ang / 4.0).max())  # rad per m


def noise1(x, seed, octaves=3):
    """Cheap smooth value-noise from summed sines with seeded phases (deterministic)."""
    rng = np.random.default_rng(seed)
    out = 0.0
    for o in range(octaves):
        f, ph = (0.011 * 2.1 ** o) * rng.uniform(0.8, 1.25), rng.uniform(0, 6.28)
        out = out + np.sin(x * f + ph) / (1.7 ** o)
    return out


def terrain_mesh(rail: Rail, prof, pal, seed: int) -> list[trimesh.Trimesh]:
    """Ribbon canyon. Asymmetric: each side has its own height curve and noise seed."""
    ss = np.arange(0, rail.length + STEP, STEP)
    P = rail.pos(ss)
    _, R = rail.frame(ss)
    W, F = prof(ss)
    side_h = {-1: 70 + 30 * noise1(ss, seed + 1), 1: 95 + 40 * noise1(ss, seed + 2)}
    us, hs = [], []
    order = [(-1, o) for o in reversed(OUTER)] + [(-1, -1.0), (0, -0.5), (0, 0.0), (0, 0.5), (1, -1.0)] + [(1, o) for o in OUTER]
    for side, o in order:
        if side == 0:  # inside floor columns: fraction of half-width
            u = o * W
            h = -F + 1.5 * noise1(ss + o * 50, seed + 7)
        elif o == -1.0:  # corridor edge
            u = side * W
            h = -F + 2.0
        else:
            u = side * (W + o)
            rise = side_h[side] * (1 - np.exp(-o / 45.0))
            h = -F + rise + (6 + o * 0.12) * noise1(ss * 1.3 + o * 7, seed + 11 + int(o) + (side > 0) * 100)
        us.append(u)
        hs.append(h)
    us, hs = np.array(us).T, np.array(hs).T  # (S, C)
    V = P[:, None, :] + R[:, None, :] * us[..., None] + UP * hs[..., None]
    chunks = []
    nC = V.shape[1]
    span = 40
    for c0 in range(0, len(ss) - 1, span):
        c1 = min(c0 + span, len(ss) - 1)
        sub = V[c0:c1 + 1]
        S = sub.shape[0]
        verts = sub.reshape(-1, 3)
        faces = []
        for i in range(S - 1):
            for j in range(nC - 1):
                a, b, c, d = i * nC + j, i * nC + j + 1, (i + 1) * nC + j, (i + 1) * nC + j + 1
                faces += [[a, b, c], [b, d, c]]  # normals up (+Y)
        m = trimesh.Trimesh(verts, np.array(faces), process=False)
        # colour by height above local floor: low = ground ramp, high = rock ramp, tops = ground again
        hgt = m.triangles_center @ UP - (P[c0:c1 + 1, 1].mean() - F[c0:c1 + 1].mean())
        low = m.submesh([np.where(hgt < 4)[0]], append=True) if (hgt < 4).any() else None
        mid = m.submesh([np.where((hgt >= 4) & (hgt < 85))[0]], append=True) if ((hgt >= 4) & (hgt < 85)).any() else None
        top = m.submesh([np.where(hgt >= 85)[0]], append=True) if (hgt >= 85).any() else None
        parts = [Part(x, r, 2) for x, r in ((low, pal["m"]), (mid, pal["r"]), (top, pal["m"])) if x is not None]
        chunks.append(bake(parts))
    return chunks


def gap_shape(cx, cy, w, h, seed) -> Polygon:
    """Irregular rounded gap: never a perfect rectangle."""
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(14):
        a = 2 * math.pi * i / 14
        rx, ry = w / 2 * rng.uniform(0.9, 1.05), h / 2 * rng.uniform(0.9, 1.05)
        # superellipse-ish so it reads as a doorway, not a circle
        c, s = math.cos(a), math.sin(a)
        pts.append((cx + rx * np.sign(c) * abs(c) ** 0.6, cy + ry * np.sign(s) * abs(s) ** 0.6))
    return Polygon(pts)


def wall_mesh(rail: Rail, s, gap: Polygon, F, seed, thick=10.0):
    rng = np.random.default_rng(seed)
    top_pts = [(x, 95 + rng.uniform(-14, 14)) for x in np.linspace(240, -240, 9)]  # chipped, uneven top
    slab = Polygon([(-240, -F - 20), (240, -F - 20)] + top_pts).difference(gap)
    trim = gap.buffer(2.5).difference(gap)
    t, r = rail.frame(np.array([s]))
    t, r = t[0], r[0]
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = r, UP, -t, rail.pos(np.array([s]))[0]
    out = []
    for poly, depth in ((slab, thick), (trim, thick + 1.5)):
        m = trimesh.util.concatenate([extrude(p, depth) for p in getattr(poly, "geoms", [poly])])
        m.apply_transform(M)
        out.append(m)
    return out  # [slab, trim]


def debug_map(rail, prof, lvl, out):
    s = np.arange(0, rail.length, 4.0)
    P = rail.pos(s)
    _, R = rail.frame(s)
    W, _ = prof(s)
    xs, zs = P[:, 0], P[:, 2]
    lo, hi = np.array([xs.min() - 80, zs.min() - 80]), np.array([xs.max() + 80, zs.max() + 80])
    sc = 900 / (hi - lo).max()
    img = Image.new("RGB", (int((hi - lo)[0] * sc) + 1, int((hi - lo)[1] * sc) + 1), (245, 245, 240))
    dr = ImageDraw.Draw(img)
    tp = lambda p: ((p[0] - lo[0]) * sc, (p[2] - lo[1]) * sc)
    for sign in (-1, 1):
        dr.line([tp(p) for p in P + R * (sign * W)[:, None]], fill=(150, 120, 100), width=2)
    dr.line([tp(p) for p in P], fill=(120, 160, 220), width=1)
    def at(sv, x):
        sv = np.array([sv]); _, r = rail.frame(sv); return tp(rail.pos(sv)[0] + r[0] * x)
    for w in lvl["walls"]:
        a, b = at(w["s"], -60), at(w["s"], 60)
        dr.line([a, b], fill=(90, 70, 70), width=4)
    for o in lvl["orbs"]:
        x, y = at(o["s"], o["x"]); dr.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(60, 200, 190))
    for e in lvl["enemies"]:
        x, y = at(e["s"], e["x"]); dr.rectangle([x - 3, y - 3, x + 3, y + 3], fill=(220, 90, 150))
    for c in lvl["checkpoints"]:
        x, y = at(c, 0); dr.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(0, 0, 0))
    img.save(out)
