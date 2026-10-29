"""Construye la imagen base (montaje + color) y la pista de diálogos a partir del EDL.

Salida:
  work/shots/<id>.mp4   un archivo por plano, 1920x1080 30 fps, exactamente N cuadros
  work/shots/<id>.wav   diálogo del plano, 48 kHz estéreo, exactamente N*1600 muestras
  work/base.mp4         todos los planos concatenados (sin audio)
  work/dialogo.wav      pista de diálogos concatenada
  work/timeline.json    inicio/fin de cada plano en la línea de tiempo (para gráficos y sonido)
Uso: .venv/Scripts/python scripts/build_base.py [--only ID,ID] [--force]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))
import edl  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROX = ROOT / "proxies"
CLIPS = ROOT / "clips"
OUT = ROOT / "work" / "shots"
OUT.mkdir(parents=True, exist_ok=True)
SR = 48000
FPS = edl.FPS
TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")

LB = 138  # letterbox 2.39:1 en 1920x1080

# Looks: corrección + grading. Historia: cada escena más oscura y fría.
LOOKS = {
    "canal": ("colortemperature=temperature=7600:mix=0.55,"
              "eq=contrast=1.06:brightness=0.005:saturation=0.9:gamma=1.0,"
              "unsharp=5:5:0.45"),
    "campo": ("colortemperature=temperature=7000:mix=0.4,"
              "curves=all='0/0 0.6/0.57 1/0.93',eq=contrast=1.05:saturation=0.88,unsharp=5:5:0.4"),
    "open": ("eq=brightness=-0.09:contrast=1.25:saturation=0.45:gamma=0.82,"
             "colorbalance=rs=-0.05:bs=0.07:rh=0.09:gh=0.03:bh=-0.06,"
             "vignette=PI/3.6,noise=alls=6:allf=t"),
    "s2": ("curves=all='0/0 0.12/0.06 0.5/0.42 0.85/0.8 1/0.93',"
           "eq=contrast=1.14:saturation=0.7:gamma=0.95,"
           "colorbalance=rs=-0.06:gs=-0.01:bs=0.07:rm=-0.02:bm=0.02:rh=0.07:gh=0.025:bh=-0.05,"
           "vignette=PI/4.4,noise=alls=5:allf=t"),
    "s4": ("curves=all='0/0 0.15/0.05 0.5/0.36 0.85/0.72 1/0.86',"
           "eq=contrast=1.2:saturation=0.5:gamma=0.9,"
           "colorbalance=rs=-0.08:gs=-0.01:bs=0.09:rm=-0.03:bm=0.03:rh=0.08:gh=0.02:bh=-0.06,"
           "vignette=PI/3.8,noise=alls=6:allf=t"),
    "s6": ("curves=all='0/0 0.18/0.04 0.5/0.28 0.85/0.6 1/0.74',"
           "eq=contrast=1.22:saturation=0.14:gamma=0.86,"
           "colorbalance=rs=-0.05:bs=0.08:rm=-0.03:bm=0.05,"
           "vignette=PI/3.4,noise=alls=7:allf=t"),
    "post": ("curves=all='0/0 0.15/0.04 0.5/0.3 0.85/0.64 1/0.78',"
             "eq=contrast=1.22:saturation=0.55:gamma=0.86,"
             "colorbalance=rs=-0.04:bs=0.05:rh=0.12:gh=0.04:bh=-0.08,"
             "vignette=PI/3.2,noise=alls=7:allf=t"),
}
STORY = {"open", "s2", "s4", "s6", "post", "photo"}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(" ".join(map(str, cmd))[:400] + "\n" + r.stderr[-1500:])


def letterbox(vf):
    return vf + f",drawbox=x=0:y=0:w=iw:h={LB}:color=black:t=fill,drawbox=x=0:y=ih-{LB}:w=iw:h={LB}:color=black:t=fill"


def framing(s, n):
    """Reencuadre fijo (punch) + push-in lento, sin jitter (scale por cuadro y crop centrado)."""
    p0 = s.punch
    p1 = s.punch * (1 + s.push)
    if p0 == 1.0 and p1 == 1.0:
        return ""
    if p0 == p1:
        return (f"scale=w=trunc(1920*{p0}/2)*2:h=trunc(1080*{p0}/2)*2:flags=lanczos,"
                "crop=1920:1080:(iw-1920)/2:(ih-1080)*0.42,")
    dur = max(n / FPS, 0.1)
    z = f"({p0}+({p1}-{p0})*min(t/{dur:.3f},1))"
    return (f"scale=w='trunc(1920*{z}/2)*2':h='trunc(1080*{z}/2)*2':eval=frame:flags=bicubic,"
            "crop=1920:1080:(iw-1920)/2:(ih-1080)*0.45,")


def source_input(s):
    """(args de entrada, prefiltro) para el clip del plano."""
    if s.clip == "IMG_1256":  # vertical: recorte 16:9 del original 4K
        return (["-ss", f"{s.tin:.3f}", "-t", f"{(s.tout - s.tin) + 0.5:.3f}", "-i", str(CLIPS / "IMG_1256.mov")],
                "crop=2160:1215:0:(ih-1215)*0.55,scale=1920:1080:flags=lanczos,fps=30,")
    return (["-ss", f"{s.tin:.3f}", "-t", f"{(s.tout - s.tin) + 0.5:.3f}", "-i", str(PROX / f"{s.clip}.mov")], "")


def look_chain(look):
    vf = LOOKS[look]
    return letterbox(vf) if look in STORY else vf


def render_video(s, n, path):
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "13", "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-frames:v", str(n), "-an"]
    if s.clip is None:
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r={FPS}", *enc, str(path)])
        return
    if s.clip.startswith("PHOTO:"):
        img = ROOT / "assets" / "fotos" / f"{s.clip[6:]}.jpg"
        rot = "transpose=1," if "rot90" in s.fx else ""
        dur = n / FPS
        z = f"(1.02+0.06*t/{dur:.3f})"
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(img), "-vf",
             f"{rot}scale=2400:-2:flags=lanczos,crop=2400:1350:0:(ih-1350)*0.3,scale=1920:1080,"
             f"scale=w='trunc(1920*{z}/2)*2':h='trunc(1080*{z}/2)*2':eval=frame,"
             f"crop=1920:1080:(iw-1920)/2:(ih-1080)/2,{look_chain('s4')}", *enc, str(path)])
        return
    inp, pre = source_input(s)
    vf = pre + f"setpts=(PTS-STARTPTS)/{s.rate}," + framing(s, n)
    if s.look == "transform":
        # de la historia (oscuro, desaturado, "congelado") al blanco frío del canal
        dur = n / FPS
        a = vf + look_chain("s4" if s.section == "t2" else "s2")
        b = vf + LOOKS["canal"]
        fc = (f"[0:v]split[x][y];[x]{a},format=yuv444p[A];[y]{b},format=yuv444p[B];"
              f"[A][B]blend=all_expr='A*(1-clip((T-1.2)/{dur - 2.4:.2f},0,1))+B*clip((T-1.2)/{dur - 2.4:.2f},0,1)',"
              "format=yuv420p")
        run(["ffmpeg", "-y", *inp, "-filter_complex", fc, *enc, str(path)])
        return
    vf += look_chain(s.look)
    if "red" in s.fx:
        vf += ",colorbalance=rs=0.25:rm=0.18:gm=-0.05:bm=-0.06,eq=saturation=1.2"
    if "freeze_end" in s.fx:
        vf += f",tpad=stop_mode=clone:stop_duration={edl.FREEZE_END},hue=s='max(0,1-max(0,t-{n / FPS - edl.FREEZE_END:.2f})*2)'"
    run(["ffmpeg", "-y", *inp, "-vf", vf, *enc, str(path)])


def render_intro(s, path):
    """1 s congelado en blanco y negro (presentación de personaje)."""
    it = s.intro
    story = it["kind"] == "storia"
    src = PROX / f"{s.clip}.mov"
    png = OUT / f"{s.id}_intro.png"
    run(["ffmpeg", "-y", "-ss", f"{it['at']:.3f}", "-i", str(src), "-frames:v", "1", str(png)])
    fr = framing(s, FPS)
    bw = ("hue=s=0,eq=contrast=1.45:brightness=-0.07:gamma=0.85,vignette=PI/3.4,noise=alls=12:allf=t"
          if story else "hue=s=0,eq=contrast=1.3:brightness=-0.02,noise=alls=5:allf=t")
    vf = fr + "scale=w='trunc(1920*(1+0.025*t)/2)*2':h='trunc(1080*(1+0.025*t)/2)*2':eval=frame,crop=1920:1080," + bw
    if story:
        vf = letterbox(vf)
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(png), "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "13", "-pix_fmt", "yuv420p",
         "-frames:v", str(FPS), str(path)])


VOICE = ("highpass=f=85,afftdn=nr=10:nf=-42,equalizer=f=250:t=q:w=1.2:g=-2,"
         "equalizer=f=3200:t=q:w=1.0:g=2.5,acompressor=threshold=-22dB:ratio=2.8:attack=8:release=120:makeup=2")


def render_audio(s, n, path):
    ns = n * (SR // FPS)
    if s.clip is None or s.clip.startswith("PHOTO:"):
        sf.write(path, np.zeros((ns, 2), np.float32), SR)
        return
    tmp = OUT / f"{s.id}_raw.wav"
    src = CLIPS / "IMG_1256.mov" if s.clip == "IMG_1256" else PROX / f"{s.clip}.mov"
    af = f"atempo={s.rate}," if s.rate != 1.0 else ""
    if s.mic:
        mic = ROOT / "audios" / (s.mic.replace("MIC_", "").replace("_", " ") + ".m4a")
        fc = (f"[0:a]{af}aresample={SR},pan=stereo|c0=c0|c1=c0,volume={s.camvol}[c];"
              f"[1:a]{af}aresample={SR},pan=stereo|c0=c0|c1=c0,{VOICE},volume=1.0[m];"
              "[c][m]amix=inputs=2:normalize=0[o]")
        run(["ffmpeg", "-y", "-ss", f"{s.tin:.3f}", "-t", f"{s.tout - s.tin:.3f}", "-i", str(src),
             "-ss", f"{s.tin + s.mic_offset:.3f}", "-t", f"{s.tout - s.tin:.3f}", "-i", str(mic),
             "-filter_complex", fc, "-map", "[o]", "-ac", "2", "-ar", str(SR), str(tmp)])
    else:
        voice = VOICE if s.look in ("canal", "campo", "transform") or s.section in ("finale",) else \
            "highpass=f=70,afftdn=nr=8:nf=-45,acompressor=threshold=-24dB:ratio=2.2:makeup=1.5"
        run(["ffmpeg", "-y", "-ss", f"{s.tin:.3f}", "-t", f"{s.tout - s.tin:.3f}", "-i", str(src),
             "-af", f"{af}aresample={SR},{voice}", "-ac", "2", "-ar", str(SR), str(tmp)])
    x, _ = sf.read(tmp, dtype="float32", always_2d=True)
    y = np.zeros((ns, 2), np.float32)
    m = min(ns, len(x))
    y[:m] = x[:m]
    f = int(0.012 * SR)  # micro-fundidos contra clics
    if m > 2 * f:
        y[:f] *= np.linspace(0, 1, f)[:, None]
        y[m - f:m] *= np.linspace(1, 0, f)[:, None]
    sf.write(path, y, SR)
    tmp.unlink()


def main():
    force = "--force" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    tl, total = edl.timeline()
    meta = []
    vlist, alist = [], []
    for s, t0 in tl:
        n = edl.body_frames(s)
        parts = []
        if s.intro:
            ip = OUT / f"{s.id}_intro.mp4"
            if force or not ip.exists() or (only and s.id in only):
                render_intro(s, ip)
            parts.append(("intro", ip, FPS))
        vp, ap = OUT / f"{s.id}.mp4", OUT / f"{s.id}.wav"
        if force or not vp.exists() or (only and (s.id in only or s.id.split(".")[0] in only)):
            print("plano", s.id, s.clip, n, flush=True)
            render_video(s, n, vp)
            render_audio(s, n, ap)
        parts.append(("body", vp, n))
        for kind, p, k in parts:
            vlist.append(p)
            if kind == "intro":
                silent = OUT / f"{s.id}_intro.wav"
                sf.write(silent, np.zeros((k * (SR // FPS), 2), np.float32), SR)
                alist.append(silent)
            else:
                alist.append(ap)
        meta.append(dict(id=s.id, clip=s.clip, look=s.look, section=s.section, start=round(t0, 4),
                         end=round(t0 + edl.shot_len(s), 4), intro=s.intro, fx=s.fx,
                         tin=s.tin, tout=s.tout, rate=s.rate,
                         body_start=round(t0 + (1.0 if s.intro else 0.0), 4)))
    (ROOT / "work" / "timeline.json").write_text(json.dumps(dict(total=total, shots=meta), indent=1))
    lst = ROOT / "work" / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in vlist))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(ROOT / "work" / "base.mp4")])
    audio = np.concatenate([sf.read(p, dtype="float32", always_2d=True)[0] for p in alist])
    sf.write(ROOT / "work" / "dialogo.wav", audio, SR)
    print(f"total {total:.2f}s  audio {len(audio) / SR:.2f}s")


if __name__ == "__main__":
    main()
