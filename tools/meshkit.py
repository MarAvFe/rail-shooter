"""Geometry + palette toolkit: Shapely 2D -> trimesh 3D -> flat-shaded vertex-colour .glb.

Conventions: 1 unit = 1 m, forward = -Z, up = +Y. Colours named FAMILY+DIGIT, dark->light.
"""
from __future__ import annotations
import colorsys, json, math
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon

ROOT = Path(__file__).resolve().parent.parent
KEY_LIGHT = np.array([-0.45, 0.8, 0.4])  # from upper-left-behind (camera looks -Z)
KEY_LIGHT = KEY_LIGHT / np.linalg.norm(KEY_LIGHT)

# ---------- palette ----------
COOL_HUE, WARM_HUE = 255.0, 45.0


def _toward(h: float, target: float, amt: float) -> float:
    d = ((target - h + 540) % 360) - 180
    return (h + d * amt) % 360


def ramp(hue: float, sat: float, lo: float = 0.30, hi: float = 0.86, n: int = 5) -> list[str]:
    """Hue-shifted pastel ramp: shadows cooler/purpler, highlights warmer."""
    out = []
    for i in range(n):
        f = i / (n - 1)
        h = _toward(hue, COOL_HUE, (1 - f) * 0.22) if f < 0.5 else _toward(hue, WARM_HUE, (f - 0.5) * 0.25)
        l = lo + (hi - lo) * f
        s = sat * (0.85 + 0.3 * math.sin(math.pi * f))  # ends a bit greyer
        r, g, b = colorsys.hls_to_rgb(h / 360, l, min(s, 1))
        out.append("#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255)))
    return out


def hex_rgb(c: str) -> tuple[float, float, float]:
    return tuple(int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))


# ---------- 2D -> 3D ----------
def extrude(poly: Polygon, depth: float) -> trimesh.Trimesh:
    """Extrude in +Z then centre on Z."""
    m = trimesh.creation.extrude_polygon(poly, depth)
    m.apply_translation([0, 0, -depth / 2])
    return m


def extrude_profile_x(poly: Polygon, width: float) -> trimesh.Trimesh:
    """Side profile: poly x = ship Z (nose at -Z), poly y = ship Y. Extruded across X, centred."""
    m = extrude(poly, width)
    # poly (x,y) on XY plane, extruded along Z -> rotate so extrusion axis becomes X, poly x becomes Z
    rot = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]], dtype=float)
    m.apply_transform(rot)  # trimesh fixes winding on reflection
    return m


def extrude_top_y(poly: Polygon, height: float) -> trimesh.Trimesh:
    """Top-down outline: poly x = ship X, poly y = ship Z. Extruded along Y, centred."""
    m = extrude(poly, height)
    rot = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)
    m.apply_transform(rot)
    return m


def visual_hull(side: Polygon, top: Polygon, width: float, height: float) -> trimesh.Trimesh:
    return extrude_profile_x(side, width).intersection(extrude_top_y(top, height))


def lathe(profile: list[tuple[float, float]], seg: int = 10) -> trimesh.Trimesh:
    """profile = [(radius, y), ...] bottom->top, revolved around Y."""
    m = trimesh.creation.revolve(np.array(profile, dtype=float), sections=seg)  # axis = Z
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))  # Z -> Y
    return m


def ico(r: float, sub: int = 1) -> trimesh.Trimesh:
    return trimesh.creation.icosphere(subdivisions=sub, radius=r)


def place(m: trimesh.Trimesh, pos=(0, 0, 0), rot_deg=(0, 0, 0), scale=1.0) -> trimesh.Trimesh:
    m = m.copy()
    if np.isscalar(scale):
        m.apply_scale(scale)
    else:
        m.apply_transform(np.diag([*scale, 1.0]))
    rx, ry, rz = (math.radians(a) for a in rot_deg)
    m.apply_transform(trimesh.transformations.euler_matrix(rx, ry, rz, "sxyz"))
    m.apply_translation(pos)
    return m


def mirror_x(m: trimesh.Trimesh) -> trimesh.Trimesh:
    m = m.copy()
    m.apply_transform(np.diag([-1.0, 1, 1, 1]))
    return m


# ---------- colour bake ----------
class Part:
    """A mesh plus the colour ramp it is painted with."""

    def __init__(self, mesh: trimesh.Trimesh, ramp_: list[str], base: int = 2, glow: bool = False):
        self.mesh, self.ramp, self.base, self.glow = mesh, ramp_, base, glow


def bake(parts: list[Part], glow_points: list[tuple[np.ndarray, float]] = ()) -> trimesh.Trimesh:
    """Flat-shade: per-face ramp step from facing vs key light, +1 step near glow sources."""
    verts, faces, cols = [], [], []
    off = 0
    for p in parts:
        m = p.mesh
        tri = m.vertices[m.faces]  # (F,3,3)
        n = m.face_normals
        d = n @ KEY_LIGHT
        step = np.where(d > 0.55, 1, np.where(d < -0.15, -1, 0))
        idx = np.clip(p.base + step, 0, len(p.ramp) - 1)
        if glow_points and not p.glow:
            c = tri.mean(axis=1)
            for gp, rad in glow_points:
                near = np.linalg.norm(c - gp, axis=1) < rad
                idx = np.where(near, np.minimum(idx + 1, len(p.ramp) - 1), idx)
        rgb = np.array([hex_rgb(p.ramp[i]) for i in idx])
        verts.append(tri.reshape(-1, 3))
        faces.append(np.arange(len(m.faces) * 3).reshape(-1, 3) + off)
        cols.append(np.repeat(rgb, 3, axis=0))
        off += len(m.faces) * 3
    v, f, c = np.vstack(verts), np.vstack(faces), np.vstack(cols)
    out = trimesh.Trimesh(v, f, process=False)
    rgba = np.hstack([c, np.ones((len(c), 1))])
    out.visual = trimesh.visual.ColorVisuals(out, vertex_colors=(rgba * 255).astype(np.uint8))
    return out


def export_glb(mesh: trimesh.Trimesh, path: Path, name: str, col: trimesh.Trimesh | None = None) -> dict:
    """Write render mesh + simplified convex collision (`<name>_col`, not rendered in Godot)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name=name, geom_name=name)
    hull = (col if col is not None else mesh).convex_hull
    scene.add_geometry(hull, node_name=f"{name}_col-convcolonly", geom_name=f"{name}_col")
    path.write_bytes(scene.export(file_type="glb"))
    return {"name": name, "tris": int(len(mesh.faces)), "col": True}


def polys(geom) -> list[Polygon]:
    return list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1))
