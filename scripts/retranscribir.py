"""Re-transcribe clips concretos sin VAD (cuando la primera pasada dejó huecos).

Uso: .venv/Scripts/python scripts/retranscribir.py IMG_1239 IMG_1351 ...
Sobrescribe analisis/transcripciones/<clip>.json e imprime los segmentos.
"""
import json
import os
import sys
from pathlib import Path

import torch

os.add_dll_directory(str(Path(torch.__file__).parent / "lib"))
os.environ["PATH"] = str(Path(torch.__file__).parent / "lib") + os.pathsep + os.environ["PATH"]
import soundfile as sf  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
for clip in sys.argv[1:]:
    audio, _ = sf.read(str(ROOT / "work" / "wav" / f"{clip}.wav"), dtype="float32")
    segs, _ = model.transcribe(audio, language="it", word_timestamps=True, vad_filter=True,
                               vad_parameters=dict(threshold=0.25, min_silence_duration_ms=400),
                               condition_on_previous_text=False, beam_size=5)
    data = []
    for s in segs:
        data.append(dict(start=round(s.start, 2), end=round(s.end, 2), text=s.text.strip(),
                         words=[dict(w=x.word, s=round(x.start, 2), e=round(x.end, 2),
                                     p=round(x.probability, 2)) for x in (s.words or [])]))
    (ROOT / "analisis" / "transcripciones" / f"{clip}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n## {clip}")
    for s in data:
        print(f"{s['start']:7.2f}-{s['end']:7.2f} {s['text']}")
