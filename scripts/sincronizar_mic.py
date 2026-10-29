"""Sincroniza cada audio de micrófono con su clip por correlación cruzada de envolventes.

Calcula el desfase global (mic_t = clip_t + offset) y lo verifica en ventanas de 4 s a lo largo
del clip para detectar deriva o cortes. Guarda analisis/sync_mic.json.
Uso: .venv/Scripts/python scripts/sincronizar_mic.py
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import correlate, butter, sosfiltfilt

ROOT = Path(__file__).resolve().parent.parent
WAV = ROOT / "work" / "wav"
PAIRS = {"IMG_1345": "MIC_New_Recording_5", "IMG_1353": "MIC_General_Santander",
         "IMG_1360": "MIC_General_Santander_2"}
SR = 16000
HOP = 80  # 5 ms


def env(x):
    sos = butter(4, [200, 4000], btype="band", fs=SR, output="sos")
    y = np.abs(sosfiltfilt(sos, x))
    n = len(y) // HOP
    e = y[: n * HOP].reshape(n, HOP).mean(1)
    e = np.log1p(e * 100)
    return (e - e.mean()) / (e.std() + 1e-9)


def best_lag(a, b):
    """lag (en frames) tal que b[i+lag] ~ a[i]; devuelve lag y pico normalizado."""
    c = correlate(b, a, mode="valid") if len(b) >= len(a) else correlate(b, a, mode="full")
    k = int(np.argmax(c))
    lag = k if len(b) >= len(a) else k - (len(a) - 1)
    return lag, float(c[k] / len(a))


def main():
    res = {}
    for clip, mic in PAIRS.items():
        a, _ = sf.read(WAV / f"{clip}.wav", dtype="float32")
        b, _ = sf.read(WAV / f"{mic}.wav", dtype="float32")
        ea, eb = env(a), env(b)
        lag, peak = best_lag(ea, eb)
        off = lag * HOP / SR
        wins = []
        w = int(4 * SR / HOP)
        for s in range(0, len(ea) - w, w // 2):
            seg = ea[s:s + w]
            if seg.std() < 0.5:
                continue
            lo = max(0, s + lag - int(1.0 * SR / HOP))
            hi = min(len(eb), s + lag + w + int(1.0 * SR / HOP))
            l2, p2 = best_lag(seg, eb[lo:hi])
            wins.append(dict(t=round(s * HOP / SR, 2), offset=round((lo + l2 - s) * HOP / SR, 3),
                             peak=round(p2, 2)))
        res[clip] = dict(mic=mic, offset=round(off, 3), peak=round(peak, 2), windows=wins)
        print(clip, mic, "offset", round(off, 3), "peak", round(peak, 2))
        for x in wins:
            print("   ", x)
    (ROOT / "analisis" / "sync_mic.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
