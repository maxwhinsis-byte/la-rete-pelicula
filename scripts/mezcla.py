"""Mezcla final: diálogos + apertura + música/drones + efectos, con ducking y loudness -15 LUFS.

Lee work/timeline.json (inicio/fin de cada plano) y work/audio/*.wav.
Salida: work/mix.wav (48 kHz estéreo) y analisis/loudness.txt
Uso: .venv/Scripts/python scripts/mezcla.py
"""
import json
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "work" / "audio"
SR = 48000
TL = json.loads((ROOT / "work" / "timeline.json").read_text())
SH = {s["id"]: s for s in TL["shots"]}
N = int(round(TL["total"] * SR))


def load(name):
    x, sr = sf.read(A / name, dtype="float32", always_2d=True)
    assert sr == SR
    return x if x.shape[1] == 2 else np.repeat(x, 2, 1)


def db(v):
    return 10 ** (v / 20)


music = np.zeros((N, 2), np.float32)   # drones / cama (se duckea con la voz)
fx = np.zeros((N, 2), np.float32)      # efectos (no se duckean)


def place(buf, x, t, gain_db=0.0, fade_in=0.0, fade_out=0.0, dur=None):
    o = int(round(t * SR))
    if dur is not None:
        x = x[: int(dur * SR)]
    x = x.copy() * db(gain_db)
    n = len(x)
    if fade_in > 0:
        k = min(n, int(fade_in * SR))
        x[:k] *= np.linspace(0, 1, k)[:, None]
    if fade_out > 0:
        k = min(n, int(fade_out * SR))
        x[n - k:] *= np.linspace(1, 0, k)[:, None]
    a, b = max(0, o), min(N, o + n)
    if b > a:
        buf[a:b] += x[a - o:b - o]


def span(first, last):
    return SH[first]["start"], SH[last]["end"]


def loop_to(x, d):
    n = int(d * SR)
    reps = int(np.ceil(n / len(x)))
    return np.tile(x, (reps, 1))[:n]


def main():
    dia = sf.read(ROOT / "work" / "dialogo.wav", dtype="float32", always_2d=True)[0][:N]
    vox = load("voces.wav")
    hb = load("sfx_latido.wav")

    # ---- apertura
    a2 = SH["A2"]["start"]
    place(music, load("drone_open.wav"), 0.0, -14, 1.0, 1.5, dur=a2 + 0.5)
    place(fx, vox, a2, -1.0)
    a3 = SH["A3"]["start"]
    place(fx, load("sfx_whoosh_down.wav"), a3 - 0.2, -10)
    place(fx, load("sfx_impacto.wav"), a3 + 0.3, -1.5)
    place(music, load("drone_cred.wav"), a3 + 1.5, -18, 2.0, 2.5, dur=SH["A3"]["end"] - a3 - 1.0)

    # ---- historia: drones que se oscurecen
    for d, (a, b), g in [("drone_s2.wav", span("S2a", "S2n"), -13), ("drone_s4.wav", span("S4a", "S4i"), -12),
                         ("drone_s6.wav", span("S6a", "S6f"), -11)]:
        place(music, loop_to(load(d), b - a), a, g, 1.5, 0.05 if d == "drone_s6.wav" else 1.2)
    # latidos
    def beats(t0, t1, bpm0, bpm1, g=-6):
        t = t0
        while t < t1:
            f = (t - t0) / max(0.01, t1 - t0)
            place(fx, hb, t, g + 4 * f)
            t += 60 / (bpm0 + (bpm1 - bpm0) * f)
    s, e = span("S2m", "S2n")
    beats(SH["S2n"]["start"] - 0.3, e - 0.2, 70, 96)
    beats(SH["S4h"]["start"], SH["S4i"]["end"] - 0.5, 80, 130, -7)
    # T1/T2: el latido se detiene; el silencio deja entrar a Bianchi
    place(fx, load("sfx_whoosh.wav"), SH["T1"]["start"] + 0.2, -16)
    place(fx, load("sfx_whoosh.wav"), SH["T2"]["start"] + 0.2, -16)
    # meses: reloj
    for sid in ("S4a", "S4c", "S4g"):
        place(fx, load("sfx_reloj.wav"), SH[sid]["start"], -14, 0.2, 0.4, dur=SH[sid]["end"] - SH[sid]["start"])
    # escena 6: fuga
    f0 = SH["S6f"]["start"]
    beats(SH["S6e"]["start"] + 2.0, SH["S6f"]["end"], 95, 150, -6)
    place(fx, load("sfx_respiro.wav"), f0, -8)
    place(fx, load("sfx_pasos.wav"), f0 + 1.2, -11)
    place(fx, load("sfx_pasos.wav"), f0 + 6.0, -7)
    place(fx, load("sfx_riser.wav")[-int(4 * SR):], SH["S6f"]["end"] - 4.0, -14)
    # negro: el latido sigue, se acelera y se detiene de golpe (alguien muere); después, silencio
    g0 = SH["S6g"]["start"]
    t, k = g0 + 0.05, 0
    while t < g0 + 2.75:
        place(fx, hb, t, -5 + 0.4 * k)
        t += 60 / (150 + 9 * k)
        k += 1

    # ---- canal: cama sutil y "glitches"
    bed = load("bed_canal.wav")
    canal_runs = []
    cur = None
    for s in TL["shots"]:
        tv = s["look"] in ("canal", "campo") and s["section"] not in ("finale",)
        if tv and cur is None:
            cur = [s["start"], s["end"]]
        elif tv:
            cur[1] = s["end"]
        elif cur is not None:
            canal_runs.append(cur)
            cur = None
    if cur:
        canal_runs.append(cur)
    for a, b in canal_runs:
        if b - a > 3:
            place(music, loop_to(bed, b - a), a, -27, 1.5, 1.5)
    for s, nxt in zip(TL["shots"], TL["shots"][1:]):
        story = {"open", "s2", "s4", "s6", "post", "photo"}
        if (s["look"] in ("canal", "campo") and nxt["look"] in story) or nxt["id"] == "S6a":
            place(fx, load("sfx_estatica.wav"), nxt["start"] - 0.2, -9)
    # presentaciones de personaje: whoosh + golpe, la música baja
    imp = load("sfx_impacto.wav")
    for s in TL["shots"]:
        if s["intro"]:
            t = s["start"]
            place(fx, load("sfx_whoosh.wav"), t - 0.15, -14)
            place(fx, imp[: int(0.9 * SR)], t, -16, 0, 0.5)
            a, b = int(t * SR), int((t + 1.0) * SR)
            music[a:b] *= 0.35
    # finale y créditos
    q0, q1 = span("Q1", "Q1")
    place(music, loop_to(load("drone_cred.wav"), q1 - q0), q0, -21, 2.0, 0.08)
    c0, c1 = span("CR", "CR2")
    place(music, loop_to(load("drone_cred.wav"), c1 - c0), c0, -15, 2.0, 2.0)
    # escena final de Moro: casi en silencio, solo su toma y un drone muy bajo
    p0 = SH["PC"]["start"]
    place(music, loop_to(load("drone_post.wav"), SH["PC"]["end"] - p0), p0, -32, 1.0, 0.6)

    # ---- ducking de música bajo la voz
    def movavg(x, w):
        c = np.cumsum(np.concatenate([[0.0], x]))
        y = (c[w:] - c[:-w]) / w
        return np.concatenate([np.full(w // 2, y[0]), y, np.full(len(x) - len(y) - w // 2, y[-1])])
    mono = np.abs(dia).mean(1).astype(np.float64)
    env = np.sqrt(movavg(mono ** 2, int(0.08 * SR)))
    duck = 1 - 0.75 * np.clip(env / 0.02, 0, 1)
    duck = movavg(duck, int(0.25 * SR)).astype(np.float32)
    music[:] = music * duck[:, None]

    # "Fermatevi!" (IMG_1320, 10.75-11.6 s de fuente) tiene que oírse por encima del latido y el riser
    s6f = next(s for s in TL["shots"] if s["id"] == "S6f")
    k0 = s6f["start"] + (10.65 - s6f["tin"]) / s6f["rate"]
    k1 = s6f["start"] + (11.7 - s6f["tin"]) / s6f["rate"]
    a, b, r = int(k0 * SR), int(k1 * SR), int(0.12 * SR)
    g = np.ones(N, np.float32)
    g[a:b] = db(-13)
    g[a - r:a] = np.linspace(1, db(-13), r)
    g[b:b + r] = np.linspace(db(-13), 1, r)
    fx[:] = fx * g[:, None]
    music[:] = music * g[:, None]
    dia[a - r:b + r] *= db(4)

    mix = dia + music + fx
    # cortes en seco a negro: silencio absoluto donde el guion lo pide
    for sid, a_off, b_off in [("Q2", 0.05, 0.0), ("PCb", 0.0, 0.0), ("S6g", 3.1, 0.0)]:
        a, b = int((SH[sid]["start"] + a_off) * SR), int((SH[sid]["end"] - b_off) * SR)
        mix[a:b] *= 0.0

    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(mix)
    target = -15.0
    mix = mix * db(target - lufs)
    # limitador + loudnorm en dos pasadas (ffmpeg): -15 LUFS integrado, true peak -1.5 dBTP
    import subprocess, re
    pre = ROOT / "work" / "_premix.wav"
    sf.write(pre, mix.astype(np.float32), SR, subtype="FLOAT")
    lim = "alimiter=limit=0.70:attack=4:release=60:level=disabled"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                        f"{lim},loudnorm=I=-15:TP=-1.5:LRA=14:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    post = ROOT / "work" / "_post.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-v", "error", "-i", str(pre), "-af",
                    f"{lim},loudnorm=I=-15:TP=-1.5:LRA=14:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true",
                    "-ar", str(SR), "-c:a", "pcm_f32le", str(post)], check=True)
    mix = sf.read(post, dtype="float32", always_2d=True)[0][:N]
    if len(mix) < N:
        mix = np.pad(mix, ((0, N - len(mix)), (0, 0)))
    pre.unlink(); post.unlink()
    from scipy.signal import resample_poly
    lufs2 = meter.integrated_loudness(mix)
    tp2 = 20 * np.log10(np.max(np.abs(resample_poly(mix, 4, 1, axis=0))) + 1e-9)
    sf.write(ROOT / "work" / "mix.wav", mix.astype(np.float32), SR, subtype="PCM_24")
    rep = f"integrated {lufs2:.2f} LUFS  true-peak~ {tp2:.2f} dBTP  dur {len(mix) / SR:.2f}s\n"
    (ROOT / "analisis" / "loudness.txt").write_text(rep)
    print(rep)


if __name__ == "__main__":
    main()
