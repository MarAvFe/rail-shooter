"""Review sheets: painter's-algorithm orthographic renders with Pillow.
Per asset: rear 3/4, side, top, front, black silhouette, and a 48-px game-distance thumbnail on 3 backgrounds."""
import math, sys
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from meshkit import ROOT

VIEWS = {"rear3q": (20, 200), "side": (0, 90), "top": (89, 0), "front": (8, 0)}  # (elev, azim) deg


def _rot(elev, azim):
    a, e = math.radians(azim), math.radians(elev)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return rx @ ry


def render(mesh, elev, azim, size=256, bg=(235, 235, 240), silhouette=False):
    img = Image.new("RGB", (size, size), bg)
    dr = ImageDraw.Draw(img)
    v = mesh.vertices @ _rot(elev, azim).T
    ext = np.abs(v[:, :2]).max() * 1.1
    tri = v[mesh.faces]
    cols = mesh.visual.vertex_colors[mesh.faces[:, 0], :3]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    for i in np.argsort(tri[:, :, 2].mean(axis=1)):  # far (-z) first; camera looks -z
        if n[i, 2] <= 0:  # back-face cull (also makes inverted-hull outlines read as rims)
            continue
        pts = [((p[0] / ext + 1) * size / 2, (1 - p[1] / ext) * size / 2) for p in tri[i]]
        dr.polygon(pts, fill=(20, 20, 30) if silhouette else tuple(int(c) for c in cols[i]))
    return img


def sheet(glb: Path, out: Path):
    mesh = trimesh.load(glb, force="mesh", process=False) if False else None
    scene = trimesh.load(glb, process=False)
    geoms = [g for n, g in scene.geometry.items() if not n.endswith("_col")]
    mesh = trimesh.util.concatenate(geoms)
    tiles = [render(mesh, *ev) for ev in VIEWS.values()]
    tiles.append(render(mesh, *VIEWS["rear3q"], silhouette=True))
    small = []
    for bg in [(250, 240, 225), (150, 170, 190), (45, 45, 70)]:
        t = render(mesh, *VIEWS["rear3q"], size=48, bg=bg).resize((48, 48))
        small.append(t.resize((128, 128), Image.NEAREST))
    W = Image.new("RGB", (256 * 5, 256 + 128), (255, 255, 255))
    for i, t in enumerate(tiles):
        W.paste(t, (i * 256, 0))
    for i, t in enumerate(small):
        W.paste(t, (i * 128, 256))
    out.parent.mkdir(parents=True, exist_ok=True)
    W.save(out)


def contact(paths, out: Path, cols=2):
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size
    rows = math.ceil(len(ims) / cols)
    C = Image.new("RGB", (w * cols, h * rows), (255, 255, 255))
    for i, im in enumerate(ims):
        C.paste(im, ((i % cols) * w, (i // cols) * h))
    C.save(out)


def main():
    outs = []
    for g in sorted((ROOT / "assets").rglob("*.glb")):
        if "/kits/" in str(g):
            continue
        o = ROOT / f"docs/review/{g.stem}.png"
        sheet(g, o)
        outs.append(o)
    contact(outs, ROOT / "docs/review/_all.png", cols=1)
    print("sheets:", len(outs))


if __name__ == "__main__":
    main()
