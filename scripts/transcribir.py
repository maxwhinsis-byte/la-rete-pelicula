"""Transcribe en italiano (palabra por palabra) los wav de work/wav y los audios de micrófono.

Salida: analisis/transcripciones/<nombre>.json  y un resumen legible en analisis/transcripciones.md
Uso: .venv/Scripts/python scripts/transcribir.py
"""
import json
import subprocess
from pathlib import Path

import os

import torch  # noqa: F401  (carga las DLL de CUDA/cuDNN que usa CTranslate2)

os.add_dll_directory(str(Path(torch.__file__).parent / "lib"))
os.environ["PATH"] = str(Path(torch.__file__).parent / "lib") + os.pathsep + os.environ["PATH"]
import soundfile as sf
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
WAV = ROOT / "work" / "wav"
OUT = ROOT / "analisis" / "transcripciones"
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = ("Dossier, Giulia Bianchi, Dottor Rossi, Professor Petrotali, signor Moro, Dana, Eva, "
          "passaporti, debito, tratta, ipotalamo, ipofisi, surrene, cortisolo, Freud, Super-Io.")


def mic_wavs():
    for p in sorted((ROOT / "audios").glob("*.m4a")):
        w = WAV / f"MIC_{p.stem.replace(' ', '_')}.wav"
        if not w.exists():
            subprocess.run(["ffmpeg", "-y", "-i", str(p), "-ac", "1", "-ar", "16000", str(w)],
                           check=True, capture_output=True)


def main():
    mic_wavs()
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    md = ["# Transcripciones (Whisper large-v3, it)\n"]
    for w in sorted(WAV.glob("*.wav")):
        js = OUT / f"{w.stem}.json"
        if js.exists():
            data = json.loads(js.read_text(encoding="utf-8"))
        else:
            audio, _sr = sf.read(str(w), dtype="float32")
            segs, _ = model.transcribe(audio, language="it", word_timestamps=True,
                                       vad_filter=True, initial_prompt=PROMPT, beam_size=5)
            data = []
            for s in segs:
                data.append(dict(start=round(s.start, 2), end=round(s.end, 2), text=s.text.strip(),
                                 words=[dict(w=x.word, s=round(x.start, 2), e=round(x.end, 2),
                                             p=round(x.probability, 2)) for x in (s.words or [])]))
            js.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        md.append(f"\n## {w.stem}\n")
        for s in data:
            md.append(f"- `{s['start']:7.2f}-{s['end']:7.2f}` {s['text']}")
        print("ok", w.stem, len(data), flush=True)
    (ROOT / "analisis" / "transcripciones.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
