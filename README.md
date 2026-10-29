# La rete — película

Corto de suspenso (11:44) para la escuela: *Essere "femmine" nella prostituzione*.
Autores: Luciano Moreno, Alessandro Vanzini, Lara Sasson. Clase IVS, 2026, Scuola Italiana di Montevideo.

- **Video final:** en la Release del repo (`La_rete_final.mp4`, 1080p30, H.264/AAC).
- **Subtítulos:** `subtitulos/La_rete.srt` (italiano). También van grabados en la imagen.
- **Informe:** `salida/INFORME.md`. Declaración de IA: `salida/DICHIARAZIONE_IA.md`.

## Estructura
```
guion/          guion (.docx) y el prompt de edición
analisis/       mapa de clips, EDL, problemas, transcripciones Whisper, sincronía de micrófonos, loudness
scripts/        todo el pipeline (Python + ffmpeg + HyperFrames)
assets/         voces TTS, fotos del debito, tipografías, LICENCIAS.md
composiciones/  proyecto HyperFrames (index.html: gráficos, subtítulos, UI del canal)
subtitulos/     La_rete.srt
salida/         informe y declaración (el .mp4 va en la Release)
```

## Cómo regenerar el video
Requisitos: Windows o macOS, ffmpeg ≥ 6, Python 3.12, Node ≥ 20 y, para Whisper, una GPU NVIDIA (opcional).
```bash
python -m venv .venv && .venv/Scripts/pip install torch --index-url https://download.pytorch.org/whl/cu128
.venv/Scripts/pip install faster-whisper librosa soundfile numpy scipy pillow pillow-heif edge-tts pyloudnorm fonttools
bash scripts/descargar_drive.sh                  # originales desde Drive -> clips/ y audios/
.venv/Scripts/python scripts/inventario.py      # proxies 1080p30 (tonemap HDR->SDR), wav, hojas de fotogramas
.venv/Scripts/python scripts/transcribir.py     # Whisper large-v3, italiano, por palabra
.venv/Scripts/python scripts/sincronizar_mic.py # desfase de cada micrófono por correlación cruzada
.venv/Scripts/python scripts/voces_tts.py       # voces de la apertura
.venv/Scripts/python scripts/sonido.py          # música/efectos sintetizados + pista de voces
.venv/Scripts/python scripts/build_base.py      # montaje + color + diálogos -> work/base.mp4, work/dialogo.wav
.venv/Scripts/python scripts/mezcla.py          # mezcla final -15 LUFS -> work/mix.wav
.venv/Scripts/python scripts/build_hf.py        # composiciones/index.html + subtitulos/La_rete.srt
cp work/base.mp4 work/mix.wav composiciones/assets/
cd composiciones && npx hyperframes@0.8.214 render -q delivery -o ../salida/La_rete_final.mp4
```
El corte entero vive en `scripts/edl.py`: planos, in/out, looks, presentaciones y subtítulos (en tiempo de fuente). Para cambiar un corte, editá ese archivo y volvé a correr `build_base.py`, `mezcla.py` y `build_hf.py`. Los clips originales (≈9 GB) no están en el repo: se bajan de Drive con el script.
