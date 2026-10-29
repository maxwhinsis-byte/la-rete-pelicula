"""Genera analisis/EDL.md y analisis/mapa_clips.csv a partir del EDL y la línea de tiempo.
Uso: .venv/Scripts/python scripts/docs.py
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import edl  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "work" / "timeline.json").read_text())

# Identificación de cada clip (a partir de transcripción + fotogramas + guion)
CLIPS = {
    "IMG_1229": ("Apertura", "I passaporti", "inserto: mano guarda pasaporte en cajón", "Moro (mano)", "Lucho", "sí"),
    "IMG_1230": ("Blocco 1", "Scena 2", "Moro abre el mueble para guardar los pasaportes", "Moro", "Lucho", "no (recortado por duración)"),
    "IMG_1231": ("Apertura / Blocco 1", "I passaporti / Scena 2", "inserto: la llave cierra el mueble", "—", "—", "sí (dos veces, motivo)"),
    "IMG_1237": ("Apertura", "Entra Lara", "BIANCHI: Buonasera…", "Giulia Bianchi", "Lara", "sí"),
    "IMG_1239": ("Blocco 1", "Novità del caso", "BIANCHI: Le prime informazioni…", "Giulia Bianchi", "Lara", "sí"),
    "IMG_1243": ("Blocco 3", "Scena 6", "Dana en la puerta (fuga)", "Dana", "Ale", "no (reemplazado por IMG_1320)"),
    "IMG_1320": ("Blocco 3", "Scena 6", "la fuga: pasillo, puerta, corren; 'Fermatevi!' fuera de cuadro", "Dana, Eva, Moro (off)", "Ale, Lara, Lucho", "sí"),
    "IMG_1246": ("Blocco 1", "Scena 2", "llegada: Dana y Eva entran; MORO: Salve, benvenute…", "Dana, Eva, Moro (off)", "Ale, Lara, Lucho", "sí"),
    "IMG_1252": ("Blocco 1", "Scena 2", "EVA: Dov'è il ristorante?", "Eva", "Lara", "sí"),
    "IMG_1255": ("Blocco 1", "Scena 2", "MORO: Il lavoro c'è…", "Moro", "Lucho", "sí"),
    "IMG_1256": ("Blocco 1", "Scena 2", "inserto vertical: Moro escribe la cifra", "Moro", "Lucho", "sí (recorte 16:9 del original 4K)"),
    "IMG_1258": ("Blocco 1", "Scena 2", "DANA: Non ci avete parlato di nessun debito…", "Dana", "Ale", "sí"),
    "IMG_1261": ("Blocco 1", "Scena 2", "MORO: Datemi i passaporti…", "Moro", "Lucho", "sí"),
    "IMG_1266": ("Blocco 1", "Scena 2", "MORO: Io vi proteggo. Senza di me, siete nessuno.", "Moro", "Lucho", "sí"),
    "IMG_1268": ("Blocco 1", "Scena 2", "Dana duda con el pasaporte en la mano", "Dana, Eva", "Ale, Lara", "sí"),
    "IMG_1269": ("Blocco 1", "Scena 2", "manos que se toman (bajo la mesa)", "Dana, Eva", "Ale, Lara", "no (se usó IMG_1291 en la escena 4)"),
    "IMG_1272": ("Blocco 1", "Transizione 1", "Lara se pone la camisa y pasa a Bianchi; 'Fermiamoci su due dettagli…'", "Eva → Bianchi", "Lara", "sí"),
    "IMG_1279": ("Blocco 2", "Scena 4", "DANA/EVA: debito… mia mamma…", "Dana, Eva", "Ale, Lara", "sí"),
    "IMG_1280": ("Blocco 2", "Scena 4", "Moro entra por la puerta", "Moro", "Lucho", "no (recortado por duración)"),
    "IMG_1285": ("Blocco 2", "Scena 4", "MORO: Vi ho portato da mangiare…", "Moro", "Lucho", "sí"),
    "IMG_1288": ("Blocco 2", "Scena 4", "DANA: Voglio il mio passaporto. MORO: Quando avrete pagato…", "Dana, Moro", "Ale, Lucho", "sí"),
    "IMG_1291": ("Blocco 2", "Scena 4", "Eva le toma la mano a Dana", "Dana, Eva", "Ale, Lara", "sí"),
    "IMG_1302": ("Blocco 2", "Scena 4", "Dana y Eva en la cama; Eva se levanta", "Dana, Eva", "Ale, Lara", "sí"),
    "IMG_1304": ("Blocco 2", "Transizione 2", "Lara se viste de periodista junto a Dana", "Eva → Bianchi", "Lara", "sí"),
    "IMG_1307": ("Blocco 3", "Scena 6", "noche: 'Un anno. Non può essere per sempre.'", "Dana, Eva", "Ale, Lara", "sí"),
    "IMG_1311": ("Blocco 3", "Scena 6", "Dana y Eva frente a Moro: 'Voi siete qui perché io lo decido.'", "Dana, Eva, Moro", "Ale, Lara, Lucho", "sí"),
    "IMG_1312": ("Blocco 3", "Scena 6", "primer plano de Dana: 'Abbiamo lavorato un anno…'", "Dana", "Ale", "sí"),
    "IMG_1314": ("Blocco 3", "Scena 6", "primer plano de Moro: 'No.'", "Moro", "Lucho", "sí (solo el 'No')"),
    "IMG_1339": ("Blocco 1", "Il fenomeno", "BIANCHI: historia antigua (dos tomas)", "Giulia Bianchi", "Lara", "sí (2ª toma)"),
    "IMG_1340": ("Blocco 1", "Il fenomeno", "BIANCHI: datos ONU y caso Parioli", "Giulia Bianchi", "Lara", "sí"),
    "IMG_1341": ("Blocco 1", "Scena 2", "exterior: jardín / reja (casa de la vecina)", "—", "—", "sí (plano de situación)"),
    "IMG_1345": ("Blocco 2", "Novità del caso", "INVIATO (Ale) en exteriores con micrófono", "Inviato", "Ale", "sí + mic 'New Recording 5'"),
    "IMG_1347": ("Blocco 2", "Il corpo", "ROSSI + BIANCHI en el estudio (con tomas repetidas)", "Dr. Rossi, Bianchi", "Ale, Lara", "sí (mejores tomas)"),
    "IMG_1348": ("Blocco 2", "Il corpo", "consenso (toma alternativa)", "Rossi, Bianchi", "Ale, Lara", "no (se usó IMG_1350: dice 'decisione libera')"),
    "IMG_1350": ("Blocco 2", "Il corpo", "consenso + salute delle vittime (con tomas falladas)", "Rossi, Bianchi", "Ale, Lara", "sí (0:01–0:12 y 0:22–0:42)"),
    "IMG_1351": ("Blocco 2", "Il corpo", "miti e realtà", "Rossi, Bianchi", "Ale, Lara", "sí"),
    "IMG_1353": ("Blocco 3", "Novità del caso", "BIANCHI en exteriores con micrófono", "Giulia Bianchi", "Lara", "sí + mic 'General Santander'"),
    "IMG_1359": ("Blocco 3", "La psiche", "entrevista BIANCHI – PETROTALI en el sofá", "Bianchi, Petrotali", "Lara, Lucho", "sí"),
    "IMG_1360": ("Blocco 4", "Novità del caso", "INVIATO (Ale) en exteriores con micrófono", "Inviato", "Ale", "sí + mic 'General Santander 2'"),
    "IMG_1361": ("Blocco 4", "La società", "BIANCHI: consenso, scala, Parioli", "Giulia Bianchi", "Lara", "sí"),
    "IMG_1362": ("Blocco 4", "La società", "BIANCHI: tomas repetidas; dignità, stereotipi", "Giulia Bianchi", "Lara", "no (recortado por duración)"),
    "IMG_1363": ("Domanda finale", "La domanda finale", "los tres en la mesa (dos tomas)", "Rossi, Bianchi, Petrotali", "Ale, Lara, Lucho", "sí (2ª toma)"),
    "IMG_1368": ("Finale", "Moro", "Moro cuelga, mira el pasaporte y sonríe (antes de los créditos)", "Moro", "Lucho", "sí (entera)"),
    "IMG_1273": ("Blocco 2", "Scena 4", "foto: hoja del debito 'Mese 4 250$'", "—", "—", "sí"),
    "IMG_1274": ("Blocco 2", "Scena 4", "foto: 'Mese 6 500$' (girada)", "—", "—", "sí (rotada 90°)"),
    "IMG_1275": ("Blocco 2", "Scena 4", "foto: 'Mese 11 1250$'", "—", "—", "sí"),
}
MIC = {"IMG_1345": "New Recording 5.m4a (+72.97 s)", "IMG_1353": "General Santander.m4a (+168.82 s)",
       "IMG_1360": "General Santander 2.m4a (+66.99 s)"}


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def main():
    used = {}
    for s in TL["shots"]:
        if s["clip"]:
            c = s["clip"].replace("PHOTO:", "")
            used.setdefault(c, []).append(f"{s['tin']:.2f}-{s['tout']:.2f}")
    with open(ROOT / "analisis" / "mapa_clips.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "bloque", "escena", "contenido / línea", "personaje", "actor", "usado", "in-out (s, fuente)", "audio micrófono"])
        for c, (b, sc, line, per, act, u) in sorted(CLIPS.items()):
            w.writerow([c, b, sc, line, per, act, u, "; ".join(used.get(c, [])), MIC.get(c, "")])
    lines = ["# EDL — La rete", "",
             f"Duración total: **{fmt(TL['total'])}** ({TL['total']:.2f} s, 30 fps). Generado desde `scripts/edl.py`.", "",
             "| # | inicio | dur. | plano | fuente | in–out | look | velocidad | notas |",
             "|---|---|---|---|---|---|---|---|---|"]
    for k, s in enumerate(TL["shots"], 1):
        notes = []
        if s["intro"]:
            notes.append(f"presentación: {s['intro']['who']}")
        notes += [f for f in s["fx"]]
        src = s["clip"] or "negro / gráfico"
        io = f"{s['tin']:.2f}–{s['tout']:.2f}" if s["clip"] and not s["clip"].startswith("PHOTO") else ""
        lines.append(f"| {k} | {fmt(s['start'])} | {s['end'] - s['start']:.2f} | {s['id']} | {src} | {io} | {s['look']} | "
                     f"{s['rate']:.2f} | {', '.join(notes)} |")
    sec = {}
    for s in TL["shots"]:
        sec.setdefault(s["section"], [s["start"], s["end"]])[1] = s["end"]
    lines += ["", "## Secciones", "", "| sección | inicio | fin | duración |", "|---|---|---|---|"]
    for k, (a, b) in sec.items():
        lines.append(f"| {k} | {fmt(a)} | {fmt(b)} | {b - a:.1f} s |")
    (ROOT / "analisis" / "EDL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("ok")


if __name__ == "__main__":
    main()
