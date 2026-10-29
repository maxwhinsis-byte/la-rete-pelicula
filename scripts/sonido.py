"""Diseño sonoro sintetizado (todo creado por nosotros, sin material con derechos).

Genera en work/audio/:
  sfx_*.wav     efectos: latido, impacto BWOOM, whoosh, estática, pasos, puerta, respiración, reloj
  voces.wav     la apertura: "prostituzione" en 12 idiomas, acelerando como un latido
  voces.json    tiempos de cada golpe/palabra (los usa también la composición HyperFrames)
Uso: .venv/Scripts/python scripts/sonido.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "audio"
OUT.mkdir(parents=True, exist_ok=True)
SR = 48000
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=4):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=4):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def reverb(x, secs=2.2, wet=0.35, damp=3500):
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir = lp(ir, damp)
    ir /= np.sqrt(np.sum(ir ** 2))
    y = fftconvolve(x, ir)[: len(x) + n]
    xx = np.pad(x, (0, len(y) - len(x)))
    return (1 - wet) * xx + wet * y


def save(name, x, stereo=True):
    x = np.asarray(x, np.float32)
    if stereo and x.ndim == 1:
        x = np.stack([x, x], 1)
    sf.write(OUT / name, x, SR)


# ------------------------------------------------------------------ efectos

def heartbeat():
    def thump(f0, d, a):
        t = t_(d)
        f = f0 * (1 + 0.8 * np.exp(-t * 40))
        ph = 2 * np.pi * np.cumsum(f) / SR
        return a * np.sin(ph) * np.exp(-t * 18) * (1 - np.exp(-t * 900))
    lub = thump(58, 0.28, 1.0)
    dub = thump(70, 0.22, 0.7)
    x = np.zeros(int(0.75 * SR))
    x[: len(lub)] += lub
    o = int(0.24 * SR)
    x[o:o + len(dub)] += dub
    x = lp(x, 180) + 0.04 * lp(rng.standard_normal(len(x)), 400) * np.exp(-np.arange(len(x)) / SR * 12)
    return norm(x, 0.95)


def heartbeat_loud():
    """Mismo lub-dub, con armónicos y golpe seco (150-900 Hz) para que se oiga en parlantes chicos."""
    x = heartbeat()
    knock = np.zeros_like(x)
    for o, a in [(0, 1.0), (int(0.24 * SR), 0.75)]:
        t = t_(0.09)
        k = bp(rng.standard_normal(len(t)), 180, 900) * np.exp(-t * 55) + 0.6 * np.sin(2 * np.pi * 160 * t) * np.exp(-t * 35)
        knock[o:o + len(t)] += a * k
    body = np.tanh(2.2 * x) / np.tanh(2.2)
    return norm(body + 0.55 * norm(knock, 1.0), 0.95)


def impact():
    t = t_(4.0)
    f = 30 + 70 * np.exp(-t * 3.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-t * 0.9)
    noise = lp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 6)
    hit = hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 30) * 0.3
    x = sub + 0.5 * noise + hit
    return norm(reverb(x, 3.5, 0.4, 2500)[: int(5 * SR)], 0.98)


def whoosh(d=0.9, up=True):
    t = t_(d)
    n = rng.standard_normal(len(t))
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    out = np.zeros_like(n)
    steps = 40
    for i in range(steps):
        a, b = int(i * len(t) / steps), int((i + 1) * len(t) / steps)
        c = (300 + 4000 * (i / steps)) if up else (4300 - 4000 * (i / steps))
        seg = bp(n, max(60, c * 0.6), min(20000, c * 1.6), 2)
        out[a:b] = seg[a:b]
    return norm(out * env, 0.7)


def static(d=0.45):
    t = t_(d)
    n = rng.standard_normal(len(t))
    gate = (rng.random(int(d * 60)) > 0.35).repeat(int(SR / 60) + 1)[: len(t)]
    crushed = np.round(n * 6) / 6
    hum = 0.3 * np.sign(np.sin(2 * np.pi * 120 * t))
    x = (hp(crushed, 800) * gate + hum * gate * 0.4) * np.exp(-t * 2)
    return norm(x, 0.5)


def steps(n=6, gap=0.55):
    x = np.zeros(int((n * gap + 1) * SR))
    for i in range(n):
        t = t_(0.18)
        s = lp(rng.standard_normal(len(t)), 600) * np.exp(-t * 35) + 0.6 * np.sin(2 * np.pi * 80 * t) * np.exp(-t * 30)
        o = int((i * gap + 0.05 + rng.uniform(-0.03, 0.03)) * SR)
        x[o:o + len(s)] += s * (0.6 + 0.4 * i / n)
    return norm(reverb(x, 1.2, 0.25), 0.8)


def door():
    t = t_(1.6)
    th = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 9) + lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 14)
    latch = np.zeros_like(t)
    o = int(0.09 * SR)
    c = hp(rng.standard_normal(int(0.03 * SR)), 2500) * np.exp(-np.arange(int(0.03 * SR)) / SR * 150)
    latch[o:o + len(c)] = c * 0.5
    return norm(reverb(th + latch, 1.5, 0.3), 0.95)


def breath(d=3.4):
    t = t_(d)
    n = rng.standard_normal(len(t))
    rate = 2.6  # respiraciones por segundo (agitada)
    env = np.maximum(0, np.sin(2 * np.pi * rate / 2 * t)) ** 1.5
    return norm(bp(n, 400, 2500) * env, 0.45)


def tick(d=3.0):
    x = np.zeros(int(d * SR))
    for k in range(int(d)):
        c = hp(rng.standard_normal(int(0.012 * SR)), 3000) * np.exp(-np.arange(int(0.012 * SR)) / SR * 400)
        o = int(k * SR)
        x[o:o + len(c)] += c * (1.0 if k % 2 == 0 else 0.7)
    return norm(x, 0.4)


def drone(d, base=41.2, dark=1.0, seed=0):
    """Pad grave de tensión: quintas y una segunda menor que roza, con batidos lentos."""
    r = np.random.default_rng(seed)
    t = t_(d)
    x = np.zeros_like(t)
    for mult, amp in [(1, 1.0), (1.5, 0.5), (2, 0.45), (2.12, 0.18 * dark), (3, 0.12)]:
        f = base * mult
        for det in (-0.25, 0.25):
            x += amp * np.sin(2 * np.pi * (f + det) * t + r.uniform(0, 6.28))
    x += 0.25 * lp(r.standard_normal(len(t)), 300)
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t)
    fade = np.minimum(1, t / 3) * np.minimum(1, (d - t) / 3)
    return norm(lp(x * lfo * fade, 900), 0.7)


def pulse_bed(d, bpm=72):
    """Cama sutil para el canal: pulso grave suave + pad claro (no compite con la voz)."""
    t = t_(d)
    pad = sum(np.sin(2 * np.pi * f * t) * a for f, a in [(110, 0.4), (164.8, 0.3), (220, 0.2), (329.6, 0.08)])
    pad = lp(pad, 1500) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.05 * t))
    beat = np.zeros_like(t)
    per = 60 / bpm
    k = 0
    while k * per < d:
        tt = t_(0.35)
        b = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 14)
        o = int(k * per * SR)
        beat[o:o + len(b)] += b[: len(beat) - o]
        k += 1
    fade = np.minimum(1, t / 2) * np.minimum(1, (d - t) / 2)
    return norm((pad * 0.6 + beat * 0.5) * fade, 0.6)


def riser(d=6.0):
    t = t_(d)
    f = 80 * (1 + 6 * (t / d) ** 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * (t / d) ** 2 + 0.4 * bp(rng.standard_normal(len(t)), 500, 6000) * (t / d) ** 3
    return norm(x, 0.6)


def smoke_crackle(d=3.0):
    t = t_(d)
    x = np.zeros_like(t)
    for _ in range(int(d * 18)):
        o = rng.integers(0, len(t) - 200)
        x[o:o + 120] += hp(rng.standard_normal(120), 3000) * rng.uniform(0.2, 1)
    return norm(x * 0.3, 0.25)


# ------------------------------------------------------------------ apertura: voces

ORDER = ["it", "es", "fr", "en", "de", "pt", "ru", "ar", "zh", "ja", "tl", "hi"]


def voices_track(dur=18.5):
    meta = json.loads((ROOT / "assets" / "voces" / "voces.json").read_text(encoding="utf-8"))
    by_lang = {}
    for m in meta:
        by_lang.setdefault(m["lang"], []).append(m)
    # golpes: 4 lentos (pum... pum... pum...) y luego aceleración hasta ~0.11 s
    beats = [0.5, 2.05, 3.45, 4.7]
    iv = 1.05
    while beats[-1] < dur - 1.3:
        beats.append(beats[-1] + iv)
        iv = max(0.105, iv * 0.86)
    hb = heartbeat()
    y = np.zeros(int((dur + 2) * SR))
    events = []
    r = np.random.default_rng(11)

    def load(f):
        tmp = OUT / "_v.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(ROOT / "assets" / "voces" / f),
                        "-ac", "1", "-ar", str(SR), str(tmp)], check=True)
        a, _ = sf.read(tmp, dtype="float32")
        return a

    cache = {}
    for i, bt in enumerate(beats):
        prog = i / max(1, len(beats) - 1)
        o = int(bt * SR)
        h = hb * (0.6 + 0.4 * prog)
        y[o:o + len(h)] += h[: len(y) - o]
        k = 1 if i < 12 else int(1 + prog * 3)
        for j in range(k):
            lang = ORDER[i] if i < 12 else ORDER[r.integers(0, 12)]
            m = by_lang[lang][r.integers(0, len(by_lang[lang]))] if i >= 12 else by_lang[lang][0]
            if m["file"] not in cache:
                cache[m["file"]] = load(m["file"])
            v = cache[m["file"]].copy()
            # distorsión creciente + leve cambio de velocidad
            drive = 1 + 6 * prog ** 2
            v = np.tanh(v * drive) / np.tanh(drive)
            gain = (0.75 if i < 12 else 0.45) * (1 - 0.3 * j / 3)
            vo = o + int(0.03 * SR) + int(j * 0.04 * SR)
            pan = r.uniform(-0.6, 0.6) if i >= 12 else 0.0
            seg = v * gain
            end = min(len(y), vo + len(seg))
            y[vo:end] += seg[: end - vo] * (1 - abs(pan) * 0.3)
            events.append(dict(t=round(bt, 3), lang=lang, word=m["word"], voice=m["voice"], layer=j,
                               x=round(float(r.uniform(0.08, 0.92)), 3) if i >= 4 else 0.5,
                               y=round(float(r.uniform(0.12, 0.88)), 3) if i >= 4 else 0.5,
                               size=round(float(140 - 95 * prog + r.uniform(-15, 15)), 1)))
    # reverb que crece hacia el final
    wet = reverb(y, 2.8, 0.55)[: len(y)]
    mixw = np.clip((np.arange(len(y)) / SR) / dur, 0, 1) ** 1.5
    y = y * (1 - 0.5 * mixw) + wet * mixw
    # último golpe: impacto sordo y medio segundo de silencio total
    last = beats[-1] + 0.25
    imp = impact()[: int(1.4 * SR)] * np.exp(-np.arange(int(1.4 * SR)) / SR * 4)
    o = int(last * SR)
    y[o:] *= 0
    y[o:o + len(imp)] += imp[: len(y) - o] * 0.8
    y = y[: int(dur * SR)]
    fade = int(0.35 * SR)
    y[-fade:] *= np.linspace(1, 0, fade)
    save("voces.wav", norm(y, 0.9))
    (OUT / "voces.json").write_text(json.dumps(dict(beats=beats, impact=last, events=events), indent=1,
                                               ensure_ascii=False), encoding="utf-8")
    print("voces:", len(beats), "golpes,", len(events), "palabras, impacto en", round(last, 2))


def main():
    save("sfx_latido.wav", heartbeat())
    save("sfx_latido_fuerte.wav", heartbeat_loud())
    save("sfx_impacto.wav", impact())
    save("sfx_whoosh.wav", whoosh(0.8, True))
    save("sfx_whoosh_down.wav", whoosh(1.0, False))
    save("sfx_estatica.wav", static(0.45))
    save("sfx_pasos.wav", steps())
    save("sfx_puerta.wav", door())
    save("sfx_respiro.wav", breath())
    save("sfx_reloj.wav", tick(3.0))
    save("sfx_riser.wav", riser(6.0))
    save("sfx_crepitio.wav", smoke_crackle(3.0))
    for name, d, base, dark, seed in [("drone_s2", 80, 41.2, 0.6, 1), ("drone_s4", 60, 38.9, 1.0, 2),
                                      ("drone_s6", 45, 36.7, 1.4, 3), ("drone_open", 12, 41.2, 1.0, 4),
                                      ("drone_cred", 40, 43.65, 0.3, 5), ("drone_post", 8, 36.7, 1.2, 6)]:
        save(f"{name}.wav", drone(d, base, dark, seed))
    save("bed_canal.wav", pulse_bed(240))
    voices_track()  # usa assets/voces/voces.json (ya filtrado tras el control de pronunciación)


if __name__ == "__main__":
    main()
