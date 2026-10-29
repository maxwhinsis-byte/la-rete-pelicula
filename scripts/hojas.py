"""Hoja de fotogramas de un clip a intervalos dados (para revisar a ojo).

Uso: .venv/Scripts/python scripts/hojas.py IMG_1347 [cada_seg=4] [desde=0] [hasta=fin]
Salida: work/sheets/<clip>_<desde>-<hasta>.jpg
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def main():
    clip = sys.argv[1]
    step = float(sys.argv[2]) if len(sys.argv) > 2 else 4
    a = float(sys.argv[3]) if len(sys.argv) > 3 else 0
    src = ROOT / "proxies" / f"{clip}.mov"
    b = float(sys.argv[4]) if len(sys.argv) > 4 else dur(src)
    tiles = []
    t = a
    while t < b:
        out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                              "-vf", "scale=320:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True).stdout
        if out:
            from io import BytesIO
            im = Image.open(BytesIO(out)).convert("RGB")
            ImageDraw.Draw(im).text((4, 4), f"{t:.1f}", fill=(255, 255, 0))
            tiles.append(im)
        t += step
    cols = 6
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    out = ROOT / "work" / "sheets" / f"{clip}_{int(a)}-{int(b)}.jpg"
    sheet.save(out, quality=80)
    print(out)


if __name__ == "__main__":
    main()
