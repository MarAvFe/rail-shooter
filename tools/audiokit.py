"""Procedural, original audio: soft effects + calm pentatonic loops. Fixed seeds -> identical rebuilds.
WAV 16-bit mono 22.05 kHz. Music loops are an integer number of bars with the release tail wrapped to the head."""
import wave
import numpy as np
from meshkit import ROOT

SR = 22050
OUT = ROOT / "assets/audio"


def db(x):
    return 10 ** (x / 20)


def env(n, a=0.01, d=0.1, s=0.6, r=0.2):
    t = np.arange(n) / SR
    dur = n / SR
    e = np.where(t < a, t / max(a, 1e-4), np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    rel = np.clip((dur - t) / max(r, 1e-4), 0, 1)
    return e * rel


def tone(f, dur, kind="sine", **kw):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(f, (n,)) if np.ndim(f) else np.full(n, f)) / SR
    if kind == "tri":
        w = 2 / np.pi * np.arcsin(np.sin(ph))
    else:
        w = np.sin(ph)
    return w * env(n, **kw)


def soft_noise(dur, cutoff=0.05, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=int(dur * SR))
    y = np.zeros_like(x)
    for i in range(1, len(x)):  # one-pole lowpass: soft "puff"
        y[i] = y[i - 1] + cutoff * (x[i] - y[i - 1])
    return y / (np.abs(y).max() + 1e-9)


def save(name, x, peak_db):
    x = x / (np.abs(x).max() + 1e-9) * db(peak_db)
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    return x


def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


PENTA = [0, 2, 4, 7, 9]


def sfx():
    out = {}
    out["sfx_shot"] = save("sfx_shot", tone(np.linspace(520, 760, int(0.12 * SR)), 0.12, a=0.005, d=0.05, s=0.4, r=0.06), -16)
    puff = soft_noise(0.35, 0.04, 1) * env(int(0.35 * SR), 0.01, 0.1, 0.4, 0.25) + 0.4 * tone(np.linspace(600, 300, int(0.35 * SR)), 0.35, r=0.3)
    out["sfx_puff"] = save("sfx_puff", puff, -12)
    for i in range(8):  # rising pentatonic chimes
        m = 72 + PENTA[i % 5] + 12 * (i // 5)
        x = tone(note(m), 0.5, a=0.004, d=0.15, s=0.25, r=0.35) + 0.3 * tone(note(m + 12), 0.5, a=0.004, d=0.1, s=0.1, r=0.3)
        out[f"sfx_chime_{i}"] = save(f"sfx_chime_{i}", x, -12)
    out["sfx_boop"] = save("sfx_boop", tone(np.linspace(330, 220, int(0.22 * SR)), 0.22, a=0.01, d=0.08, s=0.5, r=0.1), -14)
    honk = tone(note(64), 0.35, "tri", a=0.02, d=0.1, s=0.7, r=0.12) + 0.6 * tone(note(67), 0.35, "tri", a=0.02, d=0.1, s=0.7, r=0.12)
    out["sfx_honk"] = save("sfx_honk", honk, -12)
    sp = sum(tone(note(84 + p), 0.6, a=0.003 + k * 0.06, d=0.1, s=0.2, r=0.4) * 0.6 ** k for k, p in enumerate([0, 4, 7, 12]))
    out["sfx_gap"] = save("sfx_gap", sp, -12)
    out["sfx_blip"] = save("sfx_blip", tone(note(79), 0.08, a=0.003, d=0.03, s=0.3, r=0.04), -16)
    jing = np.concatenate([tone(note(72 + p), 0.22, a=0.01, d=0.08, s=0.5, r=0.1) for p in [0, 4, 7, 9]] + [tone(note(84), 0.8, a=0.01, d=0.2, s=0.4, r=0.5)])
    out["sfx_jingle"] = save("sfx_jingle", jing, -10)
    # engine hum loop: exactly 2 s, integer cycles -> seamless
    t = np.arange(2 * SR) / SR
    hum = np.sin(2 * np.pi * 90 * t) + 0.4 * np.sin(2 * np.pi * 135 * t) + 0.2 * np.sin(2 * np.pi * 0.5 * t) * np.sin(2 * np.pi * 180 * t)
    out["loop_engine"] = save("loop_engine", hum, -28)
    return out


def music(name, root, bpm, prog, seed, bars=8, mode=PENTA):
    """bass + arpeggio + pad, integer bars, tail wrapped onto the head."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    L = int(bars * 4 * beat * SR)
    buf = np.zeros(L + 3 * SR)

    def add(x, t0):
        i = int(t0 * SR)
        buf[i:i + len(x)] += x[: len(buf) - i]

    for b in range(bars):
        deg = prog[b % len(prog)]
        r = root + deg
        add(0.5 * tone(note(r - 12), 4 * beat, a=0.05, d=0.3, s=0.6, r=0.6), b * 4 * beat)
        for k in (0, 4, 7):  # pad
            add(0.12 * tone(note(r + k) * 1.003, 4 * beat, a=1.0, d=0.5, s=0.8, r=1.2), b * 4 * beat)
        for e in range(8):  # gentle arpeggio, sometimes resting
            if rng.random() < 0.2:
                continue
            m = root + 12 + deg + mode[(e * 2 + b + rng.integers(0, 2)) % len(mode)]
            add(0.22 * tone(note(m), beat, "tri", a=0.01, d=0.15, s=0.2, r=0.3), (b * 4 + e * 0.5) * beat)
    buf[: len(buf) - L] += buf[L:]
    return save(name, buf[:L], -9)


MUSIC = {
    "music_title": (60, 72, [0, 5, 7, 5], 1),
    "music_meadow": (62, 80, [0, 7, 9, 5], 2),
    "music_dunes": (65, 76, [0, 5, 0, 7], 3),
    "music_ridge": (67, 84, [0, 4, 9, 7], 4),
    "music_crystal": (64, 78, [0, 9, 5, 7], 5),
    "music_mist": (60, 70, [0, 2, 9, 7], 6),
    "music_gate": (62, 74, [0, 5, 9, 7], 7),
    "music_ending": (65, 68, [0, 7, 5, 0], 8),
}


def check(x) -> dict:
    """peak dBFS, RMS dBFS, seam jump (last->first sample)."""
    pk = 20 * np.log10(np.abs(x).max() + 1e-9)
    rms = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    return {"peak": round(pk, 1), "rms": round(rms, 1), "seam": round(float(abs(x[-1] - x[0])), 4)}


def build() -> dict:
    out = sfx()
    for k, (root, bpm, prog, seed) in MUSIC.items():
        out[k] = music(k, root, bpm, prog, seed)
    rep = {k: check(v) for k, v in out.items()}
    for k, r in rep.items():
        assert r["peak"] <= -6.0, f"{k} too loud"
        if k.startswith(("music", "loop")):
            assert r["seam"] < 0.05, f"{k} loop seam pops"
    return rep


if __name__ == "__main__":
    for k, v in build().items():
        print(k, v)
