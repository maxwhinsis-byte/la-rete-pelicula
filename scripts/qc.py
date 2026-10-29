"""Control de calidad del render final.

- ffprobe: duración, resolución, fps, códecs
- blackdetect: tramos negros (se esperan: negro de la escena 6, antes del post-créditos y el corte final)
- loudness integrado y true peak (ebur128)
- fotogramas clave en work/qc/ + hoja de contactos
Uso: .venv/Scripts/python scripts/qc.py salida/La_rete_final.mp4
"""
import json
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
video = Path(sys.argv[1])
TL = json.loads((ROOT / "work" / "timeline.json").read_text())
SH = {s["id"]: s for s in TL["shots"]}
out = ROOT / "work" / "qc"
out.mkdir(parents=True, exist_ok=True)
rep = []

pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)],
                               capture_output=True, text=True).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video")
a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
dur = float(pr["format"]["duration"])
rep.append(f"- Duración {dur:.2f} s ({int(dur // 60)}:{dur % 60:05.2f}) — esperado {TL['total']:.2f} s; "
           f"{'OK' if 600 <= dur <= 720 else 'FUERA DE RANGO'} (10:00–12:00)")
rep.append(f"- Video {v['codec_name']} {v['width']}×{v['height']} {v['r_frame_rate']} fps; "
           f"audio {a['codec_name'] if a else 'NINGUNO'} {a.get('sample_rate', '') if a else ''} Hz {a.get('channels', '') if a else ''} ch")
vd, ad = float(v.get("duration", dur)), float(a.get("duration", dur)) if a else 0
rep.append(f"- Duración video/audio: {vd:.3f} / {ad:.3f} s (diferencia {abs(vd - ad) * 1000:.0f} ms)")

r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "blackdetect=d=0.5:pix_th=0.06", "-an", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r)
expected = [("A1 plano oscuro de la llave", SH["A1"]["start"], SH["A1"]["end"]),
            ("A2/A3 apertura (voces sobre negro)", SH["A2"]["start"], SH["A3"]["end"]),
            ("S6a cartel Mese 12", SH["S6a"]["start"], SH["S6a"]["end"]),
            ("S6g negro con el latido", SH["S6g"]["start"], SH["S6g"]["end"]),
            ("Q2 corte a negro", SH["Q2"]["start"], SH["Q2"]["end"]),
            ("PCb negro + créditos (texto sobre negro)", SH["PCb"]["start"], SH["CR2"]["end"])]
rep.append("- Tramos negros detectados:")
for b0, b1 in blacks:
    b0, b1 = float(b0), float(b1)
    tag = next((n for n, x0, x1 in expected if b0 >= x0 - 1.0 and b1 <= x1 + 1.0), "⚠ NO ESPERADO")
    rep.append(f"    - {b0:7.2f}–{b1:7.2f} s ({b1 - b0:.1f} s): {tag}")

r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
rep.append(f"- Loudness integrado {I[-1] if I else '?'} LUFS (objetivo −16 a −14); true peak {TP[-1] if TP else '?'} dBTP (≤ −1)")

points = [("apertura voces", SH["A2"]["start"] + 12), ("título", SH["A3"]["start"] + 3), ("Bianchi intro", SH["A4"]["start"] + 0.5),
          ("bloque 1", SH["B1n"]["start"] + 5), ("escena 2", SH["S2f"]["body_start"] + 4), ("transición 1", SH["T1"]["start"] + 9),
          ("fenómeno", SH["F1"]["start"] + 8), ("bloque 2", SH["B2n.0"]["start"] + 5), ("escena 4", SH["S4f"]["start"] + 4),
          ("cuerpo HPA", SH["C3.0"]["start"] + 18), ("bloque 3", SH["B3n"]["start"] + 18), ("psique", SH["P1"]["start"] + 32),
          ("escena 6", SH["S6e"]["start"] + 3), ("fuga", SH["S6f"]["start"] + 7), ("bloque 4", SH["B4n.0"]["start"] + 4), ("sociedad", SH["SO2"]["start"] + 16),
          ("final", SH["Q1"]["start"] + 12), ("créditos", SH["CR"]["start"] + 3), ("ayuda", SH["CR"]["start"] + 15),
          ("fuentes", SH["CR"]["start"] + 25), ("Moro final", SH["PC"]["start"] + 7.6)]
tiles = []
for name, t in points:
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True).stdout
    im = Image.open(BytesIO(png)).convert("RGB")
    im.save(out / f"{t:07.2f}_{name.replace(' ', '_')}.jpg", quality=90)
    th = im.resize((480, 270))
    ImageDraw.Draw(th).text((6, 6), f"{name} {t:.1f}s", fill=(255, 255, 0))
    tiles.append(th)
sheet = Image.new("RGB", (480 * 4, 270 * ((len(tiles) + 3) // 4)))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % 4) * 480, (i // 4) * 270))
sheet.save(out / "contactos.jpg", quality=85)
text = "\n".join(rep)
(ROOT / "analisis" / "qc.md").write_text("# Control de calidad\n\n" + text + "\n", encoding="utf-8")
print(text)
