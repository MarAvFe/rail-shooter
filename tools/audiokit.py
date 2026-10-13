"""Procedural, original audio: soft effects + calm pentatonic loops. Fixed seeds -> identical rebuilds.
Smooth by construction: sine voices, soft attacks (>= 8 ms), one-pole low-pass, convolution reverb with a
decaying filtered-noise impulse (no comb filters -> no metallic/periodic buzz). WAV 16-bit mono 44.1 kHz. Music loops are an integer number of bars; reverb + release tails wrap onto the head."""
import wave
import numpy as np
from scipy.signal import lfilter, fftconvolve
from meshkit import ROOT

SR = 44100  # = Godot's mix rate: no resampling at play time
OUT = ROOT / "assets/audio"


def db(x):
    return 10 ** (x / 20)


def env(n, a=0.02, d=0.1, s=0.6, r=0.2):
    t = np.arange(n) / SR
    dur = n / SR
    att = 0.5 - 0.5 * np.cos(np.pi * np.clip(t / max(a, 1e-4), 0, 1))  # raised-cosine attack: no click
    dec = np.where(t < a + d, 1 - (1 - s) * np.clip((t - a) / max(d, 1e-4), 0, 1), s)
    rel = np.clip((dur - t) / max(r, 1e-4), 0, 1) ** 2  # curved release
    return att * dec * rel


def tone(f, dur, kind="sine", **kw):
    n = int(dur * SR)
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(f, (n,)) if np.ndim(f) else np.full(n, f)) / SR
    w = np.sin(ph) if kind == "sine" else 2 / np.pi * np.arcsin(np.sin(ph))
    return w * env(n, **kw)


def lowpass(x, hz):
    a = np.exp(-2 * np.pi * hz / SR)
    return lfilter([1 - a], [1, -a], x)


_IR = None


def reverb(x, mix=0.2, tail=1.2):
    """Soft room via convolution with a smooth, darkened, exponentially decaying noise burst.
    No feedback delays, so tails have no periodic 'hum'. Returns x with tail appended."""
    global _IR
    if _IR is None:
        n = int(1.4 * SR)
        t = np.arange(n) / SR
        ir = np.random.default_rng(1234).normal(size=n) * np.exp(-t / 0.32)
        ir = lowpass(lowpass(ir, 2500), 2500)
        ir[: int(0.012 * SR)] = 0  # 12 ms pre-delay
        _IR = ir / np.sqrt((ir ** 2).sum())
    x = np.concatenate([x, np.zeros(int(tail * SR))])
    wet = fftconvolve(x, _IR)[: len(x)]
    wet *= np.abs(x).max() / (np.abs(wet).max() + 1e-9)
    return x * (1 - mix) + wet * mix


def soft_noise(dur, hz=900, seed=0):
    x = lowpass(lowpass(np.random.default_rng(seed).normal(size=int(dur * SR)), hz), hz)
    return x / (np.abs(x).max() + 1e-9)


def fade_tail(x, ms=20):
    n = int(ms * SR / 1000)
    x[-n:] *= np.linspace(1, 0, n) ** 2
    return x


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

    def fx(name, x, peak, rv=0.0, lp=3000):
        x = lowpass(x, lp)
        if rv:
            x = reverb(x, rv, 0.6)
        out[name] = save(name, fade_tail(x), peak)

    # zap: fast downward sweep with a little wobble, soft edges
    n = int(0.15 * SR)
    t = np.arange(n) / SR
    f = 220 + 800 * np.exp(-t * 24) + 25 * np.sin(2 * np.pi * 40 * t)
    fx("sfx_shot", tone(f, 0.15, a=0.008, d=0.04, s=0.5, r=0.08), -18, lp=2200)
    m = int(0.45 * SR)
    puff = 0.6 * soft_noise(0.45, 700, 1) * env(m, 0.02, 0.12, 0.35, 0.3) + tone(np.linspace(330, 190, m), 0.45, a=0.02, r=0.35)
    fx("sfx_puff", puff, -16, rv=0.2, lp=1800)
    for i in range(8):  # rising pentatonic chimes
        mi = 67 + PENTA[i % 5] + 12 * (i // 5)
        x = tone(note(mi), 0.7, a=0.008, d=0.2, s=0.25, r=0.5) + 0.15 * tone(note(mi + 12), 0.7, a=0.008, d=0.1, s=0.1, r=0.4)
        fx(f"sfx_chime_{i}", x, -16, rv=0.25, lp=3000)
    fx("sfx_boop", tone(np.linspace(260, 200, int(0.24 * SR)), 0.24, a=0.02, d=0.08, s=0.5, r=0.12), -18, lp=1500)
    fx("sfx_hit", tone(np.linspace(720, 640, int(0.07 * SR)), 0.07, a=0.006, d=0.03, s=0.3, r=0.04), -24, lp=2500)
    honk = sum(g * tone(note(m) * h, 0.38, a=0.03, d=0.1, s=0.7, r=0.15) for m in (64, 67) for h, g in ((1, 1), (2, 0.25), (3, 0.08)))
    fx("sfx_honk", honk, -16, rv=0.12, lp=1400)
    sp = sum(np.pad(tone(note(76 + p), 0.5, a=0.01, d=0.1, s=0.2, r=0.35), (int(k * 0.07 * SR), int(0.3 * SR) - int(k * 0.07 * SR)))
             * 0.75 ** k for k, p in enumerate([0, 4, 7, 12]))
    fx("sfx_gap", sp, -16, rv=0.3, lp=3000)
    fx("sfx_blip", tone(note(69), 0.09, a=0.008, d=0.03, s=0.3, r=0.05), -20, lp=3000)
    jing = np.concatenate([tone(note(72 + p), 0.24, a=0.015, d=0.08, s=0.5, r=0.12) for p in [0, 4, 7, 9]]
                          + [tone(note(84), 0.9, a=0.015, d=0.2, s=0.4, r=0.6)])
    fx("sfx_jingle", jing, -14, rv=0.3, lp=3000)
    # engine: warm hum (110 Hz family, audible on small speakers) + a breath of filtered air.
    # 4 s loop; every partial completes whole cycles in 4 s, and the noise is crossfaded -> seamless.
    L = 4 * SR
    t = np.arange(L) / SR
    hum = (np.sin(2 * np.pi * 110 * t) + 0.3 * np.sin(2 * np.pi * 220.25 * t)) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.5 * t))
    X = SR // 2
    w = soft_noise(4.5, 600, 9)
    air = w[:L].copy()
    air[:X] = w[:X] * np.linspace(0, 1, X) + w[L:L + X] * np.linspace(1, 0, X)
    out["loop_engine"] = save("loop_engine", hum + 0.35 * air, -14)  # no filter on hum: a filter start-up transient would click at the seam
    return out


def music(name, root, bpm, prog, seed, bars=8, mode=PENTA):
    """bass + soft sine arpeggio + pad, integer bars; low-passed, roomy; tails wrapped onto the head."""
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
        add(0.45 * tone(note(r - 12), 4 * beat, a=0.08, d=0.4, s=0.6, r=0.8), b * 4 * beat)
        for k in (0, 4, 7):  # pad: slow swell, slightly detuned pair
            for det in (0.998, 1.002):
                add(0.07 * tone(note(r + k) * det, 4 * beat, a=1.2, d=0.5, s=0.85, r=1.4), b * 4 * beat)
        for e in range(8):  # gentle arpeggio, sometimes resting
            if rng.random() < 0.25:
                continue
            m = root + 12 + deg + mode[(e * 2 + b + rng.integers(0, 2)) % len(mode)]
            add(0.2 * tone(note(m), beat * 1.2, a=0.03, d=0.2, s=0.25, r=0.45), (b * 4 + e * 0.5) * beat)
    wet = reverb(lowpass(buf, 2600), 0.28, 0)
    wet[: len(wet) - L] += wet[L:]
    return save(name, wet[:L], -12)


MUSIC = {
    "music_title": (60, 72, [0, 5, 7, 5], 1),
    "music_meadow": (62, 76, [0, 7, 9, 5], 2),
    "music_dunes": (65, 72, [0, 5, 0, 7], 3),
    "music_ridge": (67, 78, [0, 4, 9, 7], 4),
    "music_crystal": (64, 74, [0, 9, 5, 7], 5),
    "music_mist": (60, 68, [0, 2, 9, 7], 6),
    "music_gate": (62, 72, [0, 5, 9, 7], 7),
    "music_ending": (65, 66, [0, 7, 5, 0], 8),
}


def check(x) -> dict:
    """peak dBFS, RMS dBFS, seam jump (last->first sample)."""
    pk = 20 * np.log10(np.abs(x).max() + 1e-9)
    rms = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    return {"peak": round(float(pk), 1), "rms": round(float(rms), 1), "seam": round(float(abs(x[-1] - x[0])), 4)}


def build() -> dict:
    out = sfx()
    for k, (root, bpm, prog, seed) in MUSIC.items():
        out[k] = music(k, root, bpm, prog, seed)
    rep = {k: check(v) for k, v in out.items()}
    for k, r in rep.items():
        assert r["peak"] <= -6.0, f"{k} too loud"
        if k.startswith(("music", "loop")):
            assert r["seam"] < 0.02, f"{k} loop seam pops"
    return rep


if __name__ == "__main__":
    for k, v in build().items():
        print(k, v)
