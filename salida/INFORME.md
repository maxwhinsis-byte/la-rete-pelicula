# Informe de edición — "La rete"

## Entrega
| | |
|---|---|
| Video final | `La_rete_final.mp4`: 1920×1080, 30 fps, H.264 + AAC, **11:44.5** (704.5 s) |
| Borrador liviano | `La_rete_borrador_720p.mp4` (65 MB) |
| Subtítulos | `La_rete.srt` (italiano; también grabados en la imagen) |
| Dónde | GitHub `maxwhinsis-byte/la-rete-pelicula` → Release `v1.0`, y Drive "la rete videos/salida" |
| Loudness | −15.0 LUFS integrado · true peak −2.1 dBTP |

## Qué hice
1. **Inventario:**
   - Bajé de Drive los 45 videos, 3 fotos y 3 audios sin recodificar, y verifiqué el tamaño de cada uno. El 29/10 se sumó IMG_1320 (la huida). Las copias duplicadas en Drive (mismo nombre y tamaño) se bajaron una sola vez.
   - Pasé las tomas HDR (HLG) del iPhone a SDR y armé proxies 1080p30.
   - Transcribí todo con Whisper large-v3 en italiano, palabra por palabra, y extraje fotogramas.
   - Identifiqué cada clip cruzando audio, imagen y guion (`analisis/mapa_clips.csv`).
2. **Micrófonos:**
   - Asocié cada audio con su clip: *New Recording 5* va con IMG_1345 (+72.97 s), *General Santander* con IMG_1353 (+168.82 s) y *General Santander 2* con IMG_1360 (+66.99 s).
   - Sincronicé por correlación cruzada de envolventes, con verificación cada 2 s a lo largo del clip. No hay deriva.
   - El micrófono reemplaza la voz de cámara; el ambiente de cámara queda al 12 %.
3. **Montaje** (`scripts/edl.py`, `analisis/EDL.md`):
   - Respeta la estructura del guion: apertura, bloques 1–4 (novità → escena → información), domanda finale y la escena de Moro. Los créditos van al final de todo.
   - Elegí las mejores tomas y saqué los silencios largos dentro de las tomas del canal, con reencuadres alternados para que no se noten los saltos.
   - Saqué los "ya" de los conteos del rodaje que quedaban al arranque de nueve tomas, y tres repeticiones dentro de tomas (Bianchi con la ONU, Petrotali con el Super-Io y Ale con "uno schema descritto"). En "Abbiamo l'ultima ricostruzione, relativa all'ultimo mese" se usa el segundo intento, que es el completo; ver `analisis/problemas.md`.
   - Entre la pregunta final y la escena de Moro hay 2,5 s de negro.
4. **Duración:**
   - El material útil daba unos 15 min. Para llegar a 11:44 apliqué el criterio del guion: **"tagliate dettagli, non concetti"**.
   - Corté detalles: las tres fases de Selye, "con prudenza…", el ejemplo de las hormonas sexuales, la lista de mitos y la tradición china. Saqué también "per l'epoca imperiale", "la prostituzione sacra", la pregunta sobre los límites de Freud (el concepto queda en pantalla: "Freud è uno strumento filosofico…") y los párrafos de *dignità* y *stereotipi* (la idea de *stereotipi* ya está en el caso Parioli).
   - Las partes habladas del canal van a **1.12× con el tono preservado**.
5. **Color:**
   - Canal: limpio y frío.
   - Exteriores: neutro.
   - Historia: sombras profundas, teal/ámbar, viñeta, grano y letterbox 2.39:1. Se oscurece de escena en escena: la 2 apenas sombría, la 4 más cerrada, la 6 casi monocroma y nocturna.
   - Push-in lento en los primeros planos de tensión.
6. **Gráficos** (HyperFrames + GSAP):
   - Apertura: 151 palabras sincronizadas con los golpes, retroceso, título "LA RETE" con barrido de luz.
   - Interfaz DOSSIER: logo, IN DIRETTA, reloj, ticker por bloque y lower thirds. Etiquetas de fuente **[n]**.
   - Infografías: red Mesopotamia–India–Cina, 61 %/60 % de la ONU, Parioli, respuesta rápida, eje ipotalamo–ipofisi–surrene con feedback, dopamina/ossitocina, "Ipotesi ≠ dimostrazione", consenso, salud, mito/realidad, las tres frases del texto, ES/IO/SUPER-IO, razionalizzazione y la scala libertà → violenza.
   - Historia: carteles "Ricostruzione", Mese 4/6/11 (las fotos reales de la hoja) y Mese 12.
   - Transiciones canal ↔ historia: estática de señal.
   - Presentación de los 6 personajes: 1 s congelado en blanco y negro, flecha y tarjeta. En la historia, oscura (Cormorant / ámbar); en el canal, estilo TV.
7. **Subtítulos:** en italiano durante todo el video, 2 líneas, unos 42 caracteres por línea, sincronizados con las palabras de Whisper. En la historia van en la franja negra, con color por personaje (DANA ámbar, EVA celeste, SIG. MORO hueso) y etiqueta la primera vez en cada escena. Donde no hay diálogo hay subtítulos de sonido entre corchetes. En la apertura, cada voz se subtitula con su idioma.
8. **Sonido:**
   - Voces: limpieza de ruido, EQ y compresión.
   - Música y efectos sintetizados por nosotros: drones, latido que acelera, impacto, whoosh, estática, pasos, puerta, respiración, reloj y crepitar. La cama del canal baja sola cuando alguien habla.
   - Final de la escena 6: la huida completa (IMG_1320) con "Fermatevi!" fuera de cuadro. Después del grito el latido queda solo, pasa al negro sin cortarse, golpe a golpe (lub-dub), se acelera un poco, se detiene de golpe a los 3 s y deja silencio. No hay disparo.
   - El latido es un doble golpe sordo, como en el cine: el primero (lub) más grave y largo, el segundo (dub) más agudo y corto, con ataque suave y sin agudos, para que suene "desde adentro del cuerpo" y no como un golpe en la puerta. La saturación del grave le da armónicos de 100–300 Hz, así que se oye también en el celular.
   - Mezcla a −15 LUFS, true peak ≤ −1.5 dBTP.
9. **Créditos:** autores, clase IVS · 2026, escuela, materias, *Dichiarazione di onestà*, aviso de ficción, teléfonos de ayuda (tal como los dieron) y las 14 fuentes. **No se menciona la IA en el video**: está aparte, en `DICHIARAZIONE_IA.md`.

## Decisiones tomadas por mi cuenta
- **Novità en exteriores:** las de los bloques 2 y 4 las hace Ale como enviado en exteriores, y la del 3 Lara, porque así se grabaron. A Ale no le inventé un nombre: su lower third dice "In collegamento · Inviato di Dossier".
- **"Due uomini":** en IMG_1360 Ale dice "due **uomini** stranieri… trattenuti". El subtítulo dice "**donne**", para no romper la historia. Ver más abajo.
- **Escena de Moro:** va después de la pregunta final y antes de los créditos, entera y casi en silencio: cuelga ("Ho già risolto tutto."), mira el pasaporte y sonríe. No fuma, así que saqué el humo digital.
- **Transformación de Lara:** Dana está quieta en las dos tomas, así que no hizo falta rotoscopia. Resolví el pasaje con un congelado, el latido que se detiene y un cambio gradual de color de la historia al canal.
- **Corrección de mirada:** no la apliqué. No había una herramienta simple para este equipo y la mayoría de los planos a cámara ya funcionan.
- **Créditos:** en el reparto puse "Ricerca, testi, regia e interpretazione: tutti e tre gli autori", porque me dijeron "todos hicimos todo".

## Qué falta o convendría regrabar
- **IMG_1360 (10 s):** "Ultima ora. Due **donne** straniere, scomparse… sono state ritrovate senza vita… erano trattenute…". Hoy se oye "uomini".
- **Opcional:** las líneas del guion que no se grabaron (lista en `analisis/problemas.md`). Las más notorias son las definiciones de *Il fenomeno* y los modelos legales (ley Merlin / ley 17.515).
- **Verificar** los teléfonos de ayuda (Italia 800 290 290; Uruguay 2400 0302 int. 5506/5510, 0800 4141, 0800 5050) antes de entregar.

## Control de calidad
- Duración 704.53 s (11:44.53) — esperado 704.53 s; OK (10:00–12:00)
- Video h264 1920×1080 30/1 fps; audio aac 48000 Hz 2 ch
- Duración video/audio: 704.533 / 704.533 s (diferencia 0 ms)
- Tramos negros detectados:
    -    5.40–   5.93 s (0.5 s): A1 plano oscuro de la llave
    -    8.40–  10.47 s (2.1 s): A2/A3 apertura (voces sobre negro)
    -   10.50–  11.87 s (1.4 s): A2/A3 apertura (voces sobre negro)
    -   11.90–  14.17 s (2.3 s): A2/A3 apertura (voces sobre negro)
    -   14.30–  15.07 s (0.8 s): A2/A3 apertura (voces sobre negro)
    -   25.97–  26.90 s (0.9 s): A2/A3 apertura (voces sobre negro)
    -  528.37– 530.37 s (2.0 s): S6a cartel Mese 12
    -  561.97– 567.47 s (5.5 s): S6g negro con el latido
    -  661.43– 663.77 s (2.3 s): Q2 corte a negro
    -  672.67– 686.97 s (14.3 s): PCb negro + créditos (texto sobre negro)
    -  703.27– 704.50 s (1.2 s): PCb negro + créditos (texto sobre negro)
- Loudness integrado -15.0 LUFS (objetivo −16 a −14); true peak -2.1 dBTP (≤ −1)
- Los únicos tramos negros son los intencionales: el plano muy oscuro de la llave, las voces de la apertura, el cartel "Mese 12", el negro del latido, el corte tras la pregunta final y los créditos.
- Revisé fotogramas de cada bloque, la huida (IMG_1320), el negro, la escena de Moro, los créditos y las fuentes (`work/qc/contactos.jpg`).
- En la mezcla, "Fermatevi!" queda por encima del latido. En el negro cada latido llega al nivel máximo de la mezcla con silencio entre golpe y golpe; el último termina a los 3,0 s y siguen 2,5 s de silencio total.
- Subtítulos: 193 líneas, ninguna de más de 2 renglones.
- `hyperframes check`: pasó, con 0 errores.

## Dudas abiertas
- ¿Prefieren conservar algún detalle cortado por duración, por ejemplo Selye o *dignità*? Se puede: el video tiene 15 s de margen antes de los 12:00.
