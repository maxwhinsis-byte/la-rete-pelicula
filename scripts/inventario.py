"""Paso 1: inventario de clips.

Para cada video en clips/:
  - ffprobe -> analisis/inventario.json
  - proxy 1080p30 (libx264 CRF 16) en proxies/<nombre>.mov
  - wav 16 kHz mono en work/wav/<nombre>.wav (para Whisper y sincronía)
  - hoja de contactos (1 fotograma cada 2 s) en work/sheets/<nombre>.jpg
Uso: .venv/Scripts/python scripts/inventario.py
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIPS = ROOT / "clips"
PROX = ROOT / "proxies"
WAV = ROOT / "work" / "wav"
SHEETS = ROOT / "work" / "sheets"
for d in (PROX, WAV, SHEETS):
    d.mkdir(parents=True, exist_ok=True)


def probe(p):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    inv = {}
    vids = sorted(p for p in CLIPS.iterdir() if p.suffix.lower() == ".mov")
    for p in vids:
        info = probe(p)
        v = next(s for s in info["streams"] if s["codec_type"] == "video")
        a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
        rot = 0
        for sd in v.get("side_data_list", []):
            rot = int(sd.get("rotation", 0) or 0)
        dur = float(info["format"]["duration"])
        w, h = v["width"], v["height"]
        if rot in (90, -90, 270, -270):
            w, h = h, w
        inv[p.name] = dict(duration=dur, width=w, height=h, rotation=rot,
                           codec=v["codec_name"], fps=v["r_frame_rate"],
                           audio=bool(a), color=v.get("color_transfer"))
        stem = p.stem
        prox = PROX / f"{stem}.mov"
        if not prox.exists():
            vf = ("scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,"
                  "fps=30,format=yuv420p")
            # Las tomas HEVC de iPhone suelen ser HDR (HLG): tonemap a SDR BT.709
            if v.get("color_transfer") in ("arib-std-b67", "smpte2084"):
                vf = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
                      "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"
                      + vf)
            run(["ffmpeg", "-y", "-i", str(p), "-vf", vf, "-c:v", "libx264",
                 "-preset", "veryfast", "-crf", "16",
                 "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
                 str(prox)])
        wav = WAV / f"{stem}.wav"
        if a and not wav.exists():
            run(["ffmpeg", "-y", "-i", str(p), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
        sheet = SHEETS / f"{stem}.jpg"
        if not sheet.exists():
            n = max(1, int(dur // 2) + 1)
            cols = 6
            rows = (n + cols - 1) // cols
            run(["ffmpeg", "-y", "-i", str(prox), "-vf",
                 f"fps=0.5,scale=320:-2,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=18:"
                 f"fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x{rows}",
                 "-frames:v", "1", "-q:v", "4", str(sheet)])
        print("ok", p.name, round(dur, 1), flush=True)
    (ROOT / "analisis" / "inventario.json").write_text(json.dumps(inv, indent=2))


if __name__ == "__main__":
    main()
