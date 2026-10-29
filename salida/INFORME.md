# Informe de edición — "La rete"

## Entrega
| | |
|---|---|
| Video final | `La_rete_final.mp4`: 1920×1080, 30 fps, H.264 + AAC, **11:56.5** (716.5 s) |
| Borrador liviano | `La_rete_borrador_720p.mp4` (127 MB) |
| Subtítulos | `La_rete.srt` (italiano; también grabados en la imagen) |
| Dónde | GitHub `maxwhinsis-byte/la-rete-pelicula` → Release `v1.0`, y Drive "la rete videos/salida" |
| Loudness | −15.0 LUFS integrado · true peak −2.4 dBTP |

## Qué hice
1. **Inventario:**
   - Bajé de Drive los 45 videos, 3 fotos y 3 audios sin recodificar, y verifiqué el tamaño de cada uno. Las copias duplicadas en Drive (mismo nombre y tamaño) se bajaron una sola vez.
   - Pasé las tomas HDR (HLG) del iPhone a SDR y armé proxies 1080p30.
   - Transcribí todo con Whisper large-v3 en italiano, palabra por palabra, y extraje fotogramas.
   - Identifiqué cada clip cruzando audio, imagen y guion (`analisis/mapa_clips.csv`).
2. **Micrófonos:**
   - Asocié cada audio con su clip: *New Recording 5* va con IMG_1345 (+72.97 s), *General Santander* con IMG_1353 (+168.82 s) y *General Santander 2* con IMG_1360 (+66.99 s).
   - Sincronicé por correlación cruzada de envolventes, con verificación cada 2 s a lo largo del clip. No hay deriva.
   - El micrófono reemplaza la voz de cámara; el ambiente de cámara queda al 12 %.
3. **Montaje** (`scripts/edl.py`, `analisis/EDL.md`):
   - Respeta la estructura del guion: apertura, bloques 1–4 (novità → escena → información), domanda finale, créditos y post-créditos.
   - Elegí las mejores tomas y saqué los silencios largos dentro de las tomas del canal, con reencuadres alternados para que no se noten los saltos.
4. **Duración:**
   - El material útil daba unos 15 min. Para llegar a 11:56 apliqué el criterio del guion: **"tagliate dettagli, non concetti"**.
   - Corté detalles: las tres fases de Selye, "con prudenza…", el ejemplo de las hormonas sexuales, la lista de mitos y la tradición china. Saqué también "per l'epoca imperiale", "la prostituzione sacra", la pregunta sobre los límites de Freud (el concepto queda en pantalla: "Freud è uno strumento filosofico…") y el párrafo de *dignità*.
   - Las partes habladas del canal van a **1.12× con el tono preservado**.
5. **Color:**
   - Canal: limpio y frío.
   - Exteriores: neutro.
   - Historia: sombras profundas, teal/ámbar, viñeta, grano y letterbox 2.39:1. Se oscurece de escena en escena: la 2 apenas sombría, la 4 más cerrada, la 6 casi monocroma y nocturna.
   - Push-in lento en los primeros planos de tensión.
6. **Gráficos** (HyperFrames + GSAP):
   - Apertura: 151 palabras sincronizadas con los golpes, retroceso, título "LA RETE" con barrido de luz.
   - Interfaz DOSSIER: logo, IN DIRETTA, reloj, ticker por bloque y lower thirds. Etiquetas de fuente **[n]**.
   - Infografías: red Mesopotamia–India–Cina, 61 %/60 % de la ONU, Parioli, respuesta rápida, eje ipotalamo–ipofisi–surrene con feedback, dopamina/ossitocina, "Ipotesi ≠ dimostrazione", consenso, salud, mito/realidad, las tres frases del texto, ES/IO/SUPER-IO, razionalizzazione, la scala libertà → violenza y stereotipi.
   - Historia: carteles "Ricostruzione", Mese 4/6/11 (las fotos reales de la hoja) y Mese 12.
   - Transiciones canal ↔ historia: estática de señal.
   - Presentación de los 6 personajes: 1 s congelado en blanco y negro, flecha y tarjeta. En la historia, oscura (Cormorant / ámbar); en el canal, estilo TV.
7. **Subtítulos:** en italiano durante todo el video, 2 líneas, unos 42 caracteres por línea, sincronizados con las palabras de Whisper. En la historia van en la franja negra, con color por personaje (DANA ámbar, EVA celeste, SIG. MORO hueso) y etiqueta la primera vez en cada escena. Donde no hay diálogo hay subtítulos de sonido entre corchetes. En la apertura, cada voz se subtitula con su idioma.
8. **Sonido:**
   - Voces: limpieza de ruido, EQ y compresión.
   - Música y efectos sintetizados por nosotros: drones, latido que acelera, impacto, whoosh, estática, pasos, puerta, respiración, reloj y crepitar. La cama del canal baja sola cuando alguien habla.
   - Final de la escena 6: 5 s de negro con la puerta, el silencio y un latido que se apaga.
   - Mezcla a −15 LUFS, true peak ≤ −1.5 dBTP.
9. **Créditos:** autores, clase IVS · 2026, escuela, materias, *Dichiarazione di onestà*, aviso de ficción, teléfonos de ayuda (tal como los dieron) y las 14 fuentes. **No se menciona la IA en el video**: está aparte, en `DICHIARAZIONE_IA.md`.

## Decisiones tomadas por mi cuenta
- **Novità en exteriores:** las de los bloques 2 y 4 las hace Ale como enviado en exteriores, y la del 3 Lara, porque así se grabaron. A Ale no le inventé un nombre: su lower third dice "In collegamento · Inviato di Dossier".
- **"Due uomini":** en IMG_1360 Ale dice "due **uomini** stranieri… trattenuti". El subtítulo dice "**donne**", para no romper la historia. Ver más abajo.
- **Post-créditos:** se grabó a Moro colgando el teléfono ("Ho già risolto tutto."), no fumando. Lo usé así, con humo digital muy tenue en la luz.
- **Transformación de Lara:** Dana está quieta en las dos tomas, así que no hizo falta rotoscopia. Resolví el pasaje con un congelado, el latido que se detiene y un cambio gradual de color de la historia al canal.
- **Corrección de mirada:** no la apliqué. No había una herramienta simple para este equipo y la mayoría de los planos a cámara ya funcionan.
- **Créditos:** en el reparto puse "Ricerca, testi, regia e interpretazione: tutti e tre gli autori", porque me dijeron "todos hicimos todo".

## Qué falta o convendría regrabar
- **IMG_1360 (10 s):** "Ultima ora. Due **donne** straniere, scomparse… sono state ritrovate senza vita… erano trattenute…". Hoy se oye "uomini".
- **Opcional:** las líneas del guion que no se grabaron (lista en `analisis/problemas.md`). Las más notorias son las definiciones de *Il fenomeno*, los modelos legales (ley Merlin / ley 17.515) y el plano de la puerta que se cierra en la escena 6.
- **Verificar** los teléfonos de ayuda (Italia 800 290 290; Uruguay 2400 0302 int. 5506/5510, 0800 4141, 0800 5050) antes de entregar.

## Control de calidad
- Duración 716.53 s (11:56.53) — esperado 716.53 s; OK (10:00–12:00)
- Video h264 1920×1080 30/1 fps; audio aac 48000 Hz 2 ch
- Duración video/audio: 716.533 / 716.533 s (diferencia 0 ms)
- Tramos negros detectados:
    -    5.40–   5.93 s (0.5 s): intencional
    -    8.40–  14.17 s (5.8 s): A2/A3 apertura (voces sobre negro)
    -   14.30–  15.07 s (0.8 s): A2/A3 apertura (voces sobre negro)
    -   25.97–  26.90 s (0.9 s): A2/A3 apertura (voces sobre negro)
    -  541.70– 543.73 s (2.0 s): intencional
    -  570.03– 575.03 s (5.0 s): S6g negro de 5 s
    -  680.17– 694.07 s (13.9 s): créditos (texto sobre negro)
    -  710.37– 712.50 s (2.1 s): créditos (texto sobre negro)
    -  715.03– 716.50 s (1.5 s): PCb corte final
- Loudness integrado -15.0 LUFS (objetivo −16 a −14); true peak -2.4 dBTP (≤ −1)
- Los dos tramos marcados como intencionales son el plano muy oscuro del mueble con la llave (5.4–5.9 s) y el cartel negro "Mese 12" (9:01).
- Revisé fotogramas clave de cada bloque, los lower thirds, las infografías, los créditos, las fuentes y el post-créditos (`work/qc/contactos.jpg`).
- Subtítulos: 193 líneas, ninguna de más de 2 renglones. Unas pocas van a más de 21 caracteres/s porque los actores hablan rápido (y van a 1.12×).
- `hyperframes check`: pasó, con 0 errores.

## Dudas abiertas
- ¿Prefieren conservar algún detalle cortado por duración, por ejemplo Selye o *dignità*? Se puede: el video tiene 3 s de margen antes de los 12:00, así que habría que sacar algo equivalente en otro lado.
