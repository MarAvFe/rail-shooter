"""Bold, wordless UI icons (Pillow polygons, 4x supersampled). White fill + soft dark rim; tinted in-engine."""
import math
from PIL import Image, ImageDraw
from meshkit import ROOT

S = 512  # draw size; saved at 128


def circ(cx, cy, r, n=40, a0=0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)), cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def star(cx, cy, r1, r2, n=5):
    return [(cx + (r1 if i % 2 == 0 else r2) * math.sin(math.pi * i / n), cy - (r1 if i % 2 == 0 else r2) * math.cos(math.pi * i / n)) for i in range(2 * n)]


SHAPES = {
    "play": lambda d: d.polygon([(170, 110), (410, 256), (170, 402)], fill="white"),
    "resume": lambda d: d.polygon([(170, 110), (410, 256), (170, 402)], fill="white"),
    "pause": lambda d: [d.rounded_rectangle(b, 30, fill="white") for b in ((140, 110, 230, 402), (282, 110, 372, 402))],
    "book": lambda d: [d.rounded_rectangle((90, 120, 250, 400), 24, fill="white"), d.rounded_rectangle((262, 120, 422, 400), 24, fill="white")],
    "star": lambda d: d.polygon(star(256, 270, 200, 85), fill="white"),
    "restart": lambda d: [d.arc((110, 110, 402, 402), 40, 330, fill="white", width=70),
                          d.polygon([(360, 70), (420, 210), (280, 190)], fill="white")],
    "home": lambda d: [d.polygon([(256, 80), (440, 250), (72, 250)], fill="white"), d.rectangle((130, 240, 382, 420), fill="white")],
    "gear": lambda d: [d.polygon(star(256, 256, 200, 150, 8), fill="white"), d.ellipse((186, 186, 326, 326), fill=(0, 0, 0, 0))],
    "lock": lambda d: [d.arc((160, 80, 352, 300), 180, 360, fill="white", width=50), d.rounded_rectangle((120, 220, 392, 430), 30, fill="white")],
    "orb": lambda d: d.polygon([(256, 70), (380, 256), (256, 442), (132, 256)], fill="white"),
    "speaker": lambda d: d.polygon([(90, 200), (180, 200), (300, 100), (300, 412), (180, 312), (90, 312)], fill="white"),
    "cone": lambda d: [d.polygon([(256, 70), (360, 400), (152, 400)], fill="white"), d.rounded_rectangle((90, 390, 422, 450), 20, fill="white"),
                       d.polygon([(220, 185), (292, 185), (310, 245), (202, 245)], fill=(0, 0, 0, 0)),
                       d.polygon([(186, 295), (326, 295), (344, 350), (168, 350)], fill=(0, 0, 0, 0))],
    "ship": lambda d: d.polygon([(256, 90), (450, 380), (300, 340), (256, 400), (212, 340), (62, 380)], fill="white"),
}


def build() -> list[str]:
    out = ROOT / "assets/ui"
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in SHAPES.items():
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        fn(ImageDraw.Draw(im))
        # soft rim: dilate alpha, darken
        a = im.getchannel("A")
        rim = Image.new("RGBA", (S, S), (59, 51, 80, 0))
        from PIL import ImageFilter
        rim.putalpha(a.filter(ImageFilter.MaxFilter(25)))
        rim.alpha_composite(im)
        rim.resize((128, 128), Image.LANCZOS).save(out / f"icon_{name}.png")
    return list(SHAPES)


if __name__ == "__main__":
    print(build())
