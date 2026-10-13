"""One palette for everything. Ramps are hue-shifted (see meshkit.ramp). Writes assets/palette.json."""
from meshkit import ramp, write_json, ROOT

BASE = {
    "h": ramp(205, 0.55),          # hull (kite default: sky blue)
    "t": ramp(35, 0.35),           # soft trim
    "g": ramp(185, 0.45, 0.35, 0.92, 4),  # glass
    "e": ["#5fd6c8", "#8ff0e0", "#c8fff3", "#ffffff"],  # shared glow ramp teal->white
    "x": ramp(15, 0.55),           # hover sled hull (coral)
    "d": ramp(330, 0.45),          # drifter (pink)
    "p": ramp(275, 0.40),          # pod (lilac)
    "b": ramp(55, 0.55),           # buzzer (butter)
    "u": ramp(245, 0.30),          # guardian (dusk blue)
    "face": ["#3b3350", "#ffffff"],
}

# Colourways: hull ramp swaps (unlocked after levels 2, 4, 6)
COLOURWAYS = [ramp(205, 0.55), ramp(140, 0.45), ramp(300, 0.40)]

# Per-level: rock (r), ground/moss (m), sky top/bottom, fog, light.
LEVELS = {
    1: {"r": ramp(28, 0.22, 0.34, 0.82), "w": ramp(262, 0.22, 0.42, 0.86), "m": ramp(95, 0.45, 0.32, 0.84),
        "sky": ["#8ec9f0", "#fde9d6"], "fog": "#d9e8ef", "light": "#fff4e0"},
    2: {"r": ramp(25, 0.45, 0.32, 0.86), "m": ramp(35, 0.55, 0.38, 0.90),
        "sky": ["#f5b39a", "#ffe9c7"], "fog": "#fbdcc4", "light": "#ffe2c0"},
    3: {"r": ramp(215, 0.30, 0.28, 0.86), "m": ramp(200, 0.25, 0.50, 0.95),
        "sky": ["#7fb4ea", "#e8f3ff"], "fog": "#dfeaf7", "light": "#ffffff"},
    4: {"r": ramp(300, 0.35, 0.28, 0.84), "m": ramp(270, 0.40, 0.34, 0.86),
        "sky": ["#c9a3e8", "#ffe1f0"], "fog": "#efd8ee", "light": "#fff0f6"},
    5: {"r": ramp(260, 0.22, 0.30, 0.82), "m": ramp(150, 0.25, 0.40, 0.85),
        "sky": ["#a99ad6", "#f2e6f7"], "fog": "#ddd3ec", "light": "#fff7ec"},
    6: {"r": ramp(28, 0.22, 0.34, 0.82), "w": ramp(262, 0.22, 0.42, 0.86), "m": ramp(95, 0.45, 0.32, 0.84),
        "sky": ["#f6a98f", "#ffeec2"], "fog": "#f7dcc8", "light": "#ffe6b8"},
}


for _k, _v in LEVELS.items():  # sky-wall ramp default: pale lavender stone, distinct from canyon rock
    _v.setdefault("w", ramp(262, 0.22, 0.42, 0.86))


def build() -> dict:
    data = {"base": BASE, "colourways": COLOURWAYS, "levels": {str(k): v for k, v in LEVELS.items()}}
    write_json(ROOT / "assets/palette.json", data)
    return data


if __name__ == "__main__":
    build()
