# Licencias y procedencia de los recursos

Todo lo que suena o se ve en el video fue grabado por los autores o creado para este proyecto. No hay música ni efectos de bibliotecas con derechos.

## Imagen y sonido grabados por los autores
- 45 clips de video (iPhone, 4K) y 3 fotos (la hoja del *debito*). Autores: Luciano Moreno, Alessandro Vanzini y Lara Sasson.
- 3 audios de micrófono (`New Recording 5.m4a`, `General Santander.m4a`, `General Santander 2.m4a`), grabados por los autores.

## Voces sintéticas de la apertura
- **Herramienta:** `edge-tts` 7.x (biblioteca libre de Python). Usa las voces neuronales genéricas del catálogo de Microsoft Edge (texto a voz).
- **Voces:** it-IT-Elsa / Diego, es-UY-Valentina, es-ES-Alvaro, fr-FR-Denise / Henri, en-US-Guy, en-GB-Sonia, de-DE-Katja / Conrad, pt-BR-Francisca, pt-PT-Duarte, ru-RU-Svetlana / Dmitry, ar-EG-Salma, ar-SA-Hamed, zh-CN-Xiaoxiao / Yunxi, ja-JP-Nanami / Keita, fil-PH-Blessica / Angelo, hi-IN-Swara / Madhur.
- Son voces de catálogo. **No se clonó ni se imitó a ninguna persona real.** Para variar timbre y tono se cambiaron la altura y la velocidad.
- Cada voz se comprobó con Whisper (detección de idioma). Se descartaron 4 variantes que no se entendían bien; el detalle está en `analisis/qc_voces_tts*.json`.
- Archivos: `assets/voces/*.mp3`. Script: `scripts/voces_tts.py`.

## Música y efectos
- **Sintetizados por nosotros** con Python, en `scripts/sonido.py` (numpy/scipy): drones de tensión, cama del canal, latido, impacto "BWOOM", whoosh, estática de señal, pasos, puerta, respiración, reloj, *riser* y crepitar. No se usó ninguna muestra de terceros.
- La llave, el cajón y el teléfono son el sonido real de las tomas.

## Tipografías (todas SIL Open Font License 1.1, de Google Fonts)
Inter, Bebas Neue, Cormorant Garamond, JetBrains Mono, Noto Sans Arabic, Noto Sans Devanagari, Noto Sans SC y Noto Sans JP. Las dos últimas se recortaron a los glifos que se usan.

## Software
HyperFrames 0.8.214 (composición y render), GSAP 3.14.2 (animación), ffmpeg 9 (corte, color, audio), faster-whisper large-v3 (transcripción), Python 3.12 (numpy, scipy, soundfile, pyloudnorm, Pillow, pillow-heif).
