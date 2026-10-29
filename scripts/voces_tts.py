"""Apertura: la palabra "prostituzione" en 12 idiomas con voces sintéticas genéricas (edge-tts).

No clona ni imita a ninguna persona real: son voces neuronales de catálogo, variando género y tono.
Salida: assets/voces/<idx>_<lang>_<voz>.mp3 + assets/voces/voces.json
Uso: .venv/Scripts/python scripts/voces_tts.py
"""
import asyncio
import json
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "voces"
OUT.mkdir(parents=True, exist_ok=True)

WORDS = [
    ("it", "prostituzione", ["it-IT-ElsaNeural", "it-IT-DiegoNeural"]),
    ("es", "prostitución", ["es-UY-ValentinaNeural", "es-ES-AlvaroNeural"]),
    ("fr", "prostitution", ["fr-FR-DeniseNeural", "fr-FR-HenriNeural"]),
    ("en", "prostitution", ["en-US-GuyNeural", "en-GB-SoniaNeural"]),
    ("de", "Prostitution", ["de-DE-KatjaNeural", "de-DE-ConradNeural"]),
    ("pt", "prostituição", ["pt-BR-FranciscaNeural", "pt-PT-DuarteNeural"]),
    ("ru", "проституция", ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]),
    ("ar", "دعارة", ["ar-EG-SalmaNeural", "ar-SA-HamedNeural"]),
    ("zh", "卖淫", ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"]),
    ("ja", "売春", ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"]),
    ("tl", "prostitusyon", ["fil-PH-BlessicaNeural", "fil-PH-AngeloNeural"]),
    ("hi", "वेश्यावृत्ति", ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"]),
]
# Variaciones de tono/velocidad para que parezcan muchas personas distintas
STYLES = [("+0Hz", "+0%"), ("-12Hz", "-8%"), ("+10Hz", "+6%")]
# Descartadas tras el control con Whisper (analisis/qc_voces_tts*.json): no se entendía la palabra
BAD = {"08_zh_10.mp3", "08_zh_11.mp3", "07_ar_11.mp3", "11_hi_11.mp3"}


async def main():
    meta = []
    for i, (lang, word, voices) in enumerate(WORDS):
        for j, voice in enumerate(voices):
            for k, (pitch, rate) in enumerate(STYLES[: 2 if j else 3]):
                f = OUT / f"{i:02d}_{lang}_{j}{k}.mp3"
                if not f.exists():
                    await edge_tts.Communicate(word, voice, pitch=pitch, rate=rate).save(str(f))
                if f.name in BAD:
                    continue
                meta.append(dict(file=f.name, lang=lang, word=word, voice=voice,
                                 pitch=pitch, rate=rate))
    (OUT / "voces.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(meta), "voces")


asyncio.run(main())
