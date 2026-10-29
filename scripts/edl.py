"""EDL de "La rete": la línea de tiempo completa como datos.

Cada plano (Shot) toma un rango de un clip fuente (en segundos del proxy 1080p30) con un look,
y opcionalmente un audio de otro origen (p. ej. micrófono sincronizado). Los subtítulos se
escriben en tiempo de FUENTE (clip, inicio, fin), así se re-sincronizan solos si cambia el corte.

Los textos de los subtítulos son lo que dicen los actores en lo grabado, corregido con la
ortografía y las palabras del guion cuando coinciden (ver analisis/problemas.md).
"""
from dataclasses import dataclass, field

# ---------------------------------------------------------------- tipos


@dataclass
class Shot:
    id: str
    clip: str | None          # "IMG_1239" | None (negro / gráfico puro) | "PHOTO:IMG_1273"
    tin: float = 0.0
    tout: float = 0.0
    look: str = "canal"       # canal | campo | s2 | s4 | s6 | open | post | black | photo
    section: str = ""
    rate: float = 1.0         # >1 acelera (con tono preservado)
    dur: float | None = None  # para negro / fotos / gráficos
    mic: str | None = None    # micrófono que reemplaza la voz de cámara
    mic_offset: float = 0.0   # t_mic = t_clip + mic_offset
    camvol: float = 1.0       # nivel del audio de cámara (bajo cuando hay mic)
    intro: dict | None = None  # presentación de personaje (freeze 1 s antes del plano)
    push: float = 0.0         # push-in total (0.04 = 4 %)
    punch: float = 1.0        # reencuadre fijo (para ocultar saltos de corte)
    fx: list = field(default_factory=list)  # efectos especiales: transform, freeze_end, red, ...
    vclip: str | None = None  # imagen de otro clip (cutaway) manteniendo el audio de `clip`
    vin: float = 0.0


@dataclass
class Cue:
    clip: str
    s: float
    e: float
    who: str      # B R P I D E M T  (o "" = neutro, "sfx" = descripción sonora)
    text: str
    sid: str = ""  # plano concreto, cuando el mismo clip se usa más de una vez


SPEAKERS = {
    "B": ("BIANCHI", "#ffffff"), "R": ("ROSSI", "#ffffff"), "P": ("PETROTALI", "#ffffff"),
    "I": ("INVIATO", "#ffffff"), "T": ("TUTTI", "#ffffff"),
    "D": ("DANA", "#f3c98b"), "E": ("EVA", "#a9dcec"), "M": ("SIG. MORO", "#e9e2d6"),
}

TALK = 1.12  # velocidad de los bloques hablados del canal (se ajusta para la duración total)

INTRO_TEXT = {
    "moro": ("Sig. Moro", "Lucho (Luciano Moreno)", "Il capo della rete. Controlla tutto."),
    "dana": ("Dana, 22", "Ale (Alessandro Vanzini)", "Arrivata per un lavoro. Le tolgono il passaporto."),
    "eva": ("Eva, 20", "Lara (Lara Sasson)", "La compagna di Dana. Spera ancora di andarsene."),
    "bianchi": ("Giulia Bianchi", "Lara (Lara Sasson)", "Inviata di Dossier. Segue il caso."),
    "rossi": ("Dr. Rossi", "Ale (Alessandro Vanzini)", "Medico. Spiega cosa accade al corpo."),
    "petrotali": ("Prof. Petrotali", "Lucho (Luciano Moreno)", "Filosofo. Legge la psiche con Freud."),
}

# ---------------------------------------------------------------- línea de tiempo

SHOTS: list[Shot] = [
    # ============ APERTURA
    Shot("A1", "IMG_1229", 0.0, 5.4, "open", "apertura", push=0.05),
    Shot("A1b", "IMG_1231", 0.4, 3.4, "open", "apertura"),
    Shot("A2", None, look="black", section="voci", dur=18.5),
    Shot("A3", None, look="black", section="titolo", dur=8.0),
    Shot("A4", "IMG_1237", 11.05, 23.35, "canal", "apertura", rate=TALK,
         intro=dict(who="bianchi", at=11.05, x=0.50, y=0.30, kind="canal")),

    # ============ BLOCCO 1 — novità
    Shot("B1n", "IMG_1239", 5.0, 27.95, "canal", "b1", rate=TALK, fx=["ticker:b1"]),
    Shot("B1n2", "IMG_1239", 36.45, 41.35, "canal", "b1", rate=TALK, punch=1.08),
    # Scena 2 — L'arrivo
    Shot("S2a", "IMG_1341", 1.0, 3.8, "s2", "s2", fx=["card:L'arrivo"]),
    Shot("S2c", "IMG_1246", 4.0, 12.2, "s2", "s2",
         intro=dict(who="dana", at=4.0, x=0.46, y=0.33, kind="storia")),
    Shot("S2d", "IMG_1246", 12.2, 14.9, "s2", "s2",
         intro=dict(who="eva", at=12.2, x=0.72, y=0.30, kind="storia")),
    Shot("S2e", "IMG_1252", 0.35, 4.45, "s2", "s2"),
    Shot("S2f", "IMG_1255", 0.45, 12.75, "s2", "s2", push=0.04,
         intro=dict(who="moro", at=0.45, x=0.68, y=0.22, kind="storia")),
    Shot("S2g", "IMG_1256", 0.0, 2.9, "s2", "s2"),
    Shot("S2h", "IMG_1258", 1.6, 6.6, "s2", "s2", push=0.04),
    Shot("S2i", "IMG_1261", 0.0, 9.45, "s2", "s2", push=0.03),
    Shot("S2j", "IMG_1268", 0.0, 2.9, "s2", "s2"),
    Shot("S2m", "IMG_1266", 0.2, 4.9, "s2", "s2", push=0.05),
    Shot("S2n", "IMG_1268", 1.4, 2.9, "s2", "s2", push=0.06, fx=["red", "freeze_end"]),
    # Transizione 1 — Eva diventa Bianchi
    Shot("T1", "IMG_1272", 0.15, 12.3, "transform", "t1", fx=["transform"]),

    # ============ BLOCCO 1 — Il fenomeno
    Shot("F1", "IMG_1339", 38.55, 53.65, "canal", "fen", rate=TALK, fx=["map:meso"]),
    Shot("F2", "IMG_1339", 58.2, 68.6, "canal", "fen", rate=TALK, punch=1.08, fx=["map:india"]),
    Shot("F3", "IMG_1339", 94.15, 100.6, "canal", "fen", rate=TALK, fx=["map:all"]),
    Shot("F4", "IMG_1340", 5.45, 21.7, "canal", "fen", rate=TALK, punch=1.06, fx=["stat:onu"]),
    Shot("F5", "IMG_1340", 21.7, 40.9, "canal", "fen", rate=TALK, fx=["stat:parioli"]),

    # ============ BLOCCO 2 — novità (inviato sul posto, micrófono)
    Shot("B2n", "IMG_1345", 0.75, 26.45, "campo", "b2", rate=TALK,
         mic="MIC_New_Recording_5", mic_offset=72.97, camvol=0.12, fx=["ticker:b2", "lt:inviato"]),
    # Scena 4 — Il controllo
    Shot("S4a", "PHOTO:IMG_1273", look="photo", section="s4", dur=3.0, fx=["card:Mese 4"]),
    Shot("S4b", "IMG_1279", 0.36, 8.3, "s4", "s4", push=0.04),
    Shot("S4c", "PHOTO:IMG_1274", look="photo", section="s4", dur=2.6, fx=["card:Mese 6", "rot90"]),
    Shot("S4e", "IMG_1285", 3.5, 13.9, "s4", "s4"),
    Shot("S4f", "IMG_1288", 0.0, 11.0, "s4", "s4", push=0.04),
    Shot("S4g", "PHOTO:IMG_1275", look="photo", section="s4", dur=2.8, fx=["card:Mese 11"]),
    Shot("S4h", "IMG_1291", 0.45, 3.7, "s4", "s4", push=0.05),
    Shot("S4i", "IMG_1302", 0.2, 3.2, "s4", "s4", fx=["freeze_end"]),
    # Transizione 2 — Eva diventa Bianchi; Rossi già in studio
    Shot("T2", "IMG_1304", 0.3, 5.6, "transform", "t2", fx=["transform"]),

    # ============ BLOCCO 2 — Il corpo
    Shot("C0", "IMG_1347", 21.35, 26.85, "canal", "corpo", rate=TALK,
         intro=dict(who="rossi", at=21.35, x=0.25, y=0.30, kind="canal"), fx=["lt:rossi"]),
    Shot("C1", "IMG_1347", 45.2, 50.35, "canal", "corpo", rate=TALK, punch=1.07, fx=["gfx:tre"]),
    Shot("C2", "IMG_1347", 64.95, 91.7, "canal", "corpo", rate=TALK, fx=["gfx:simpatico"]),
    Shot("C3", "IMG_1347", 92.8, 129.6, "canal", "corpo", rate=TALK, punch=1.07, fx=["gfx:hpa"]),
    Shot("C4", "IMG_1347", 129.7, 133.0, "canal", "corpo", rate=TALK),
    Shot("C6", "IMG_1347", 155.25, 162.7, "canal", "corpo", rate=TALK, punch=1.07),
    Shot("C7", "IMG_1347", 176.05, 197.65, "canal", "corpo", rate=TALK, punch=1.07, fx=["gfx:dopa"]),
    Shot("C9", "IMG_1347", 213.05, 224.5, "canal", "corpo", rate=TALK, punch=1.07, fx=["gfx:causa"]),
    Shot("C10", "IMG_1350", 0.75, 11.75, "canal", "corpo", rate=TALK, fx=["gfx:consenso"]),
    Shot("C11", "IMG_1350", 22.0, 42.2, "canal", "corpo", rate=TALK, punch=1.07, fx=["gfx:salute"]),
    Shot("C12", "IMG_1351", 3.0, 5.8, "canal", "corpo", rate=TALK),
    Shot("C12b", "IMG_1351", 19.0, 44.3, "canal", "corpo", rate=TALK, punch=1.07, fx=["gfx:miti"]),

    # ============ BLOCCO 3 — novità (Bianchi sul posto, micrófono)
    Shot("B3n", "IMG_1353", 0.4, 21.5, "campo", "b3", rate=TALK,
         mic="MIC_General_Santander", mic_offset=168.82, camvol=0.12,
         fx=["ticker:b3", "lt:bianchi_campo", "gfx:frasi"]),
    # La psiche — intervista
    Shot("P1", "IMG_1359", 17.6, 52.95, "canal", "psiche", rate=TALK,
         intro=dict(who="petrotali", at=17.6, x=0.72, y=0.27, kind="canal"),
         fx=["lt:petrotali", "gfx:esio"]),
    Shot("P2", "IMG_1359", 53.15, 71.95, "canal", "psiche", rate=TALK, punch=1.07, fx=["gfx:esio2"]),
    # 72.0-76.1: falso arranque de "il Super-Io…" fuera
    Shot("P2b", "IMG_1359", 76.15, 81.45, "canal", "psiche", rate=TALK),
    Shot("P3", "IMG_1359", 81.4, 88.45, "canal", "psiche", rate=TALK),
    Shot("P4", "IMG_1359", 93.25, 110.6, "canal", "psiche", rate=TALK, punch=1.07, fx=["gfx:civilta", "gfx:freud"]),
    Shot("P7", "IMG_1359", 130.9, 133.7, "canal", "psiche", rate=TALK),
    # Scena 6 — La fuga
    Shot("S6a", None, look="black", section="s6", dur=2.4, fx=["card:Mese 12"]),
    Shot("S6b", "IMG_1307", 0.5, 11.7, "s6", "s6", push=0.04),
    Shot("S6c", "IMG_1312", 0.35, 3.55, "s6", "s6", push=0.05),
    Shot("S6d", "IMG_1314", 1.45, 3.35, "s6", "s6"),
    Shot("S6e", "IMG_1311", 6.6, 12.3, "s6", "s6", push=0.04),
    # la fuga: entran al pasillo, abren la puerta y salen corriendo; desde afuera, "Fermatevi!"
    Shot("S6f", "IMG_1320", 2.5, 12.1, "s6", "s6", fx=["fuga"]),
    # negro: latido acelerado que se detiene de golpe, y silencio
    Shot("S6g", None, look="black", section="s6", dur=5.5, fx=["sfx:fine"]),

    # ============ BLOCCO 4 — novità (inviato, micrófono)
    Shot("B4n", "IMG_1360", 0.3, 19.45, "campo", "b4", rate=TALK,
         mic="MIC_General_Santander_2", mic_offset=66.99, camvol=0.12,
         fx=["ticker:b4", "lt:inviato"]),
    # 19.45-25.65: "è uno schema…" repetido dos veces, fuera
    Shot("B4nb", "IMG_1360", 25.65, 35.6, "campo", "b4", rate=TALK, punch=1.07,
         mic="MIC_General_Santander_2", mic_offset=66.99, camvol=0.12),
    # La società
    Shot("SO1", "IMG_1361", 0.75, 16.95, "canal", "soc", rate=TALK, fx=["gfx:consenso2"]),
    Shot("SO2", "IMG_1361", 16.85, 46.2, "canal", "soc", rate=TALK, punch=1.07, fx=["gfx:scala"]),

    # ============ LA DOMANDA FINALE
    Shot("Q1", "IMG_1363", 61.5, 89.2, "canal", "finale", fx=["finale"]),
    Shot("Q2", None, look="black", section="finale", dur=2.5),

    # ============ ESCENA FINAL (antes de los créditos): Moro, en silencio, la toma entera
    Shot("PC", "IMG_1368", 0.0, 8.9, "post", "post", push=0.03),
    Shot("PCb", None, look="black", section="post", dur=1.2),
    # ============ CREDITI (gráfico sobre negro)
    Shot("CR", None, look="black", section="crediti", dur=29.5),
    Shot("CR2", None, look="black", section="crediti", dur=1.0),
]

# ---------------------------------------------------------------- subtítulos (tiempo de fuente)

CUES: list[Cue] = [
    # Apertura
    Cue("IMG_1229", 0.0, 2.6, "sfx", "[una chiave gira]"),
    Cue("IMG_1229", 2.8, 5.3, "sfx", "[un cassetto si chiude]"),
    Cue("IMG_1231", 0.5, 3.3, "sfx", "[clic della serratura]", "A1b"),
    Cue("IMG_1237", 11.3, 14.5, "B", "Buonasera. Aggiornamento su un caso che stiamo seguendo da ieri sera."),
    Cue("IMG_1237", 14.6, 20.6, "B", "Una segnalazione anonima parla di una rete che potrebbe trattenere donne straniere in questa città."),
    Cue("IMG_1237", 20.6, 23.2, "B", "Vi diciamo cosa sappiamo e cosa ancora no."),
    # Blocco 1 novità
    Cue("IMG_1239", 5.2, 8.6, "B", "Le prime informazioni. La segnalazione è arrivata ieri sera."),
    Cue("IMG_1239", 8.8, 16.6, "B", "Una vicina dichiara alla nostra inviata di aver visto, da un anno, due giovani donne straniere entrare in un appartamento e non uscire mai da sole."),
    Cue("IMG_1239", 16.9, 20.0, "B", "Le autorità non hanno ancora confermato nulla."),
    Cue("IMG_1239", 20.05, 27.9, "B", "Abbiamo però ottenuto una ricostruzione, basata su testimonianze e documenti, di ciò che sarebbe successo il giorno in cui le donne sono arrivate."),
    Cue("IMG_1239", 36.6, 41.3, "B", "Le chiameremo Dana ed Eva: nomi inventati per proteggere la loro identità."),
    # Scena 2
    Cue("IMG_1341", 0.3, 4.5, "sfx", "[vento, uccelli lontani]"),
    Cue("IMG_1246", 0.6, 4.0, "sfx", "[la porta si apre]"),
    Cue("IMG_1246", 4.3, 8.9, "M", "Salve, benvenute. Il viaggio è stato lungo, immagino."),
    Cue("IMG_1246", 9.0, 11.6, "", "Sì, un po'."),
    Cue("IMG_1252", 0.0, 4.4, "E", "Dov'è il ristorante? Ci hanno detto che il lavoro inizia domani."),
    Cue("IMG_1255", 0.6, 7.6, "M", "Il lavoro c'è. Ma prima sistemiamo le carte: viaggio, alloggio, documenti."),
    Cue("IMG_1255", 8.3, 12.7, "M", "Io ho pagato tutto. E quello me lo dovete, no?"),
    Cue("IMG_1256", 0.0, 2.85, "M", "E voi mi dovete questa cifra."),
    Cue("IMG_1258", 1.9, 6.6, "D", "Non ci avete parlato di nessun debito prima di arrivare."),
    Cue("IMG_1261", 0.0, 3.8, "M", "Sono cose che si dicono all'arrivo. Datemi i passaporti."),
    Cue("IMG_1261", 3.9, 9.4, "M", "In questo Paese, donne senza documenti sono un problema."),
    Cue("IMG_1268", 0.0, 2.9, "sfx", "[silenzio]", "S2j"),
    Cue("IMG_1230", 0.3, 4.0, "sfx", "[un'anta si apre]"),
    Cue("IMG_1266", 0.35, 4.8, "M", "Io vi proteggo. Senza di me, siete nessuno."),
    Cue("IMG_1268", 1.4, 2.9, "sfx", "[battito]", "S2n"),
    Cue("IMG_1272", 0.0, 3.2, "sfx", "[il battito si ferma]"),
    Cue("IMG_1272", 3.3, 12.2, "B", "Fermiamoci su due dettagli della ricostruzione: un debito comunicato solo all'arrivo e i passaporti trattenuti \"per custodirli\"."),
    # Il fenomeno
    Cue("IMG_1339", 38.7, 45.3, "B", "Non è un tema solo di oggi: se ne trovano tracce da più di quattromila anni, e non solo in Occidente."),
    Cue("IMG_1339", 45.44, 53.6, "B", "In Mesopotamia i testi cuneiformi usano parole tradotte \"prostituta\", ma gli studiosi discutono quanto la traduzione sia corretta."),
    Cue("IMG_1339", 53.76, 58.24, "B", "Anche la \"prostituzione sacra\" nei templi è messa in dubbio."),
    Cue("IMG_1339", 58.26, 68.54, "B", "In India, l'Arthashastra, un trattato di governo di circa 2300 anni fa, parla di donne che esercitavano e pagavano tasse allo Stato."),
    Cue("IMG_1339", 68.72, 77.5, "B", "In Cina una tradizione attribuisce al ministro Guan Zhong, sette secoli prima di Cristo, un sistema al servizio dello Stato."),
    Cue("IMG_1339", 77.74, 83.76, "B", "Per l'epoca imperiale, la ricerca osserva che le regole cambiavano secondo lo status delle persone."),
    Cue("IMG_1339", 94.28, 100.48, "B", "In società diversissime torna lo stesso schema: soldi, controllo e differenze di status."),
    Cue("IMG_1340", 5.5, 21.64, "B", "Oggi, secondo l'ONU, nel 2022 donne e ragazze erano il 61% delle vittime di tratta individuate; il 60% delle ragazze vittime era trafficato a fini di sfruttamento sessuale. Sono casi individuati: molto resta sommerso."),
    Cue("IMG_1340", 21.64, 40.64, "B", "E non è un problema lontano: nel 2013, a Roma, nel quartiere Parioli, due ragazze di 14 e 15 anni furono sfruttate da adulti, e furono condannati i responsabili, tra cui la madre di una delle due. Quel caso fu chiamato \"baby squillo\", un nome che sposta la colpa sulle ragazze."),
    # Blocco 2 novità
    Cue("IMG_1345", 0.96, 4.58, "I", "Aggiornamento. La polizia ha verificato la casa segnalata."),
    Cue("IMG_1345", 4.72, 15.38, "I", "Nell'immobile sono stati trovati dei fogli con cifre che sembravano un debito che aumentava mese dopo mese, e un telefono che ormai non è più funzionante."),
    Cue("IMG_1345", 17.0, 21.82, "I", "Una cooperante dice che le due donne \"non sembravano libere di decidere\"."),
    Cue("IMG_1345", 22.08, 26.3, "I", "Mostriamo la seconda ricostruzione: i mesi successivi all'arrivo."),
    # Scena 4
    Cue("PHOTO:IMG_1273", 0.0, 3.0, "sfx", "[un orologio ticchetta]"),
    Cue("IMG_1279", 0.38, 3.9, "D", "Questo debito non si finisce mai di pagare."),
    Cue("IMG_1279", 4.48, 8.2, "E", "Mia mamma non sa dove sono. Non posso nemmeno scriverle."),
    Cue("IMG_1280", 0.0, 2.9, "sfx", "[passi, una porta]"),
    Cue("IMG_1285", 3.79, 9.6, "M", "Buongiorno, ragazze. Vi ho portato da mangiare. Vi ho dato una casa, un lavoro."),
    Cue("IMG_1285", 10.2, 13.8, "M", "Qualcuno ha fatto tanto per voi?"),
    Cue("IMG_1288", 0.08, 1.8, "D", "Voglio il mio passaporto."),
    Cue("IMG_1288", 2.44, 5.6, "M", "Quando avrete pagato, lo avrete."),
    Cue("IMG_1288", 6.0, 8.9, "M", "Se uscite senza documenti, vi prende la polizia."),
    Cue("IMG_1288", 9.64, 10.9, "M", "Io vi sto aiutando."),
    Cue("IMG_1291", 0.4, 3.7, "sfx", "[battito]"),
    Cue("IMG_1302", 0.0, 3.2, "sfx", "[il battito sale e si ferma]"),
    Cue("IMG_1304", 0.0, 5.6, "sfx", "[silenzio]"),
    # Il corpo
    Cue("IMG_1347", 21.51, 26.73, "B", "Dottor Rossi, ci siamo fermati su quel battito che sale. Lo spieghiamo con la scienza."),
    Cue("IMG_1347", 45.34, 50.14, "R", "Partiamo da una premessa: la biologia descrive meccanismi, non spiega le persone."),
    Cue("IMG_1347", 51.06, 55.4, "R", "Distingueremo sempre ciò che la ricerca dimostra da ciò che è solo un'ipotesi."),
    Cue("IMG_1347", 65.04, 70.84, "R", "Primo: la risposta rapida. Davanti a una minaccia il cervello attiva il sistema nervoso simpatico,"),
    Cue("IMG_1347", 70.94, 76.18, "R", "la parte del sistema nervoso autonomo che prepara alla \"lotta o fuga\"."),
    Cue("IMG_1347", 77.56, 87.22, "R", "La midollare del surrene libera adrenalina e noradrenalina. Il cuore accelera, la pressione sale, i muscoli ricevono più sangue."),
    Cue("IMG_1347", 88.9, 91.58, "R", "Succede in secondi. È il battito che sentite."),
    Cue("IMG_1347", 92.92, 97.86, "R", "Secondo: la risposta lenta, l'asse ipotalamo–ipofisi–surrene."),
    Cue("IMG_1347", 98.06, 112.04, "R", "L'ipotalamo libera CRH; il CRH stimola l'ipofisi a liberare ACTH; l'ACTH stimola la corticale del surrene a produrre cortisolo."),
    Cue("IMG_1347", 112.28, 123.5, "R", "È una catena di messaggeri chimici che agisce in minuti. Poi il cortisolo stesso frena la catena: questo è il feedback negativo. Il corpo torna all'equilibrio."),
    Cue("IMG_1347", 123.52, 129.48, "R", "Quindi il sistema nervoso e il sistema endocrino lavorano insieme: uno veloce, l'altro più lento."),
    Cue("IMG_1347", 129.8, 132.82, "B", "E se la pressione dura mesi, come nel caso che stiamo seguendo?"),
    Cue("IMG_1347", 144.72, 153.88, "R", "Beh, lo stress cronico è un'altra storia. Si possono descrivere tre fasi: allarme, resistenza ed esaurimento."),
    Cue("IMG_1347", 155.38, 162.52, "R", "Nello stress prolungato l'asse può restare attivo, e il feedback può funzionare meno bene."),
    Cue("IMG_1347", 167.58, 175.88, "R", "Non possiamo dire che cosa accada nel corpo di una persona reale, e il cortisolo da solo non causa una condizione."),
    Cue("IMG_1347", 176.16, 182.14, "B", "Una domanda su desiderio. Alcuni dicono che è tutto chimica."),
    Cue("IMG_1347", 182.42, 186.8, "R", "È proprio l'errore da evitare. Alcune sostanze sono coinvolte:"),
    Cue("IMG_1347", 186.84, 197.5, "R", "la dopamina, neurotrasmettitore del circuito della ricompensa, è associata a motivazione e anticipazione del piacere; l'ossitocina, a legame e fiducia."),
    Cue("IMG_1347", 205.23, 208.5, "R", "Gli ormoni sessuali, come estrogeni e testosterone,"),
    Cue("IMG_1347", 210.29, 212.99, "R", "regolano pubertà e funzioni riproduttive."),
    Cue("IMG_1347", 213.23, 224.39, "R", "Ma \"coinvolto\" non vuol dire \"causa\". Un ormone non equivale a un comportamento, e i risultati cambiano molto da persona a persona e con il contesto."),
    Cue("IMG_1350", 0.9, 4.59, "B", "E quindi una reazione del corpo non dimostra un consenso."),
    Cue("IMG_1350", 5.07, 11.61, "R", "Esatto. Una reazione del corpo non è un consenso. Il consenso è una decisione libera, e non si legge in un ormone."),
    Cue("IMG_1350", 22.13, 25.39, "B", "Invece, cosa sappiamo della salute di chi è vittima di tratta?"),
    Cue("IMG_1350", 25.39, 42.07, "R", "Una revisione di 19 studi ha trovato molta violenza e sofferenza psicologica: ansia, depressione, stress post-traumatico, dolori fisici e infezioni sessualmente trasmesse. Ma l'evidenza è limitata, e mostra associazioni, non cause."),
    Cue("IMG_1351", 3.1, 5.72, "B", "E la salute sessuale? Si sentono tanti miti."),
    Cue("IMG_1351", 5.74, 18.96, "R", "Sì, è vero, esistono tanti miti. Che il preservativo protegge da tutte le malattie, o al contrario che non serve a nulla, o che chi lavora in questo ambito sceglie come proteggersi. Tutti questi sono miti."),
    Cue("IMG_1351", 19.14, 34.74, "R", "Il preservativo usato correttamente riduce molto il rischio di HIV e di molte altre IST, ma contro quelle trasmesse per contatto di pelle o mucose, come herpes, sifilide e HPV,"),
    Cue("IMG_1351", 34.94, 44.12, "R", "protegge solo in parte. E poi, chi vive isolata e controllata ha poco potere di negoziare la propria protezione."),
    # Blocco 3 novità
    Cue("IMG_1353", 0.0, 6.54, "B", "Altra novità. Gli investigatori hanno ricevuto un testo scritto a mano, che sarebbe di una delle due donne."),
    Cue("IMG_1353", 6.88, 15.38, "B", "Descrive un uomo che chiamiamo \"il signor Moro\". Dice che le proteggerà, e che non restituirà i passaporti finché non avranno pagato."),
    Cue("IMG_1353", 15.54, 21.36, "B", "Ecco le frasi che emergono dal testo: \"Io vi proteggo\". \"Quando avrete pagato\". \"Non abbiamo scelta\"."),
    # La psiche
    Cue("IMG_1359", 17.73, 23.79, "B", "Buongiorno. Abbiamo con noi il professor Petrotali, docente di filosofia. Professore, grazie per essere qui."),
    Cue("IMG_1359", 24.75, 35.13, "B", "Gli investigatori hanno trovato un testo con tre frasi: \"Io vi proteggo\", \"Quando avrete pagato\" e \"Non abbiamo scelta\"."),
    Cue("IMG_1359", 35.26, 38.36, "B", "Freud può aiutarci a leggerle?"),
    Cue("IMG_1359", 38.62, 46.46, "P", "Freud può aiutarci a leggerle come strumento di interpretazione filosofica e psicologica, non come spiegazione biologica."),
    Cue("IMG_1359", 46.62, 52.94, "P", "La mente, secondo Freud, è divisa in tre istanze: l'Es, il Super-Io e l'Io."),
    Cue("IMG_1359", 53.24, 61.66, "B", "Se pensiamo alla donna che ha scritto questa lettera: vuole scappare, ma resta. Cosa può accadere nella sua mente?"),
    Cue("IMG_1359", 62.52, 71.9, "P", "Quello che accade è un conflitto psichico. L'impulso è fuggire, ma l'Io valuta la realtà: il debito, il passaporto trattenuto, la paura della polizia."),
    Cue("IMG_1359", 76.2, 81.36, "P", "Il Super-Io si trasforma in vergogna e colpa: \"Se sei qui, è colpa tua\"."),
    Cue("IMG_1359", 81.39, 85.07, "B", "E sull'uomo che scrive \"Io vi proteggo\"?"),
    Cue("IMG_1359", 85.9, 88.4, "P", "Una possibile lettura: la razionalizzazione."),
    Cue("IMG_1359", 93.34, 98.25, "P", "Giustificazioni che permettono di ottenere ciò che si vuole senza sentire la colpa."),
    Cue("IMG_1359", 98.52, 104.72, "P", "Poi, \"Il disagio della civiltà\": la civiltà come Super-Io collettivo. Norme, divieti, tabù."),
    Cue("IMG_1359", 104.82, 110.52, "P", "E lo stigma verso chi è sfruttato può rendere più difficile chiedere aiuto."),
    Cue("IMG_1359", 118.04, 121.3, "B", "Un'ultima domanda: quali sono i limiti di Freud?"),
    Cue("IMG_1359", 122.22, 128.76, "P", "È una teoria interpretativa, discussa e criticata: non va usata come spiegazione biologica, né per giudicare le persone."),
    Cue("IMG_1359", 130.98, 133.58, "B", "Abbiamo l'ultima ricostruzione, relativa all'ultimo mese."),
    # Scena 6
    Cue("IMG_1307", 0.72, 3.2, "D", "Un anno. Non può essere per sempre."),
    Cue("IMG_1307", 4.04, 7.9, "E", "Beh, gli chiediamo i passaporti. E se dice di no…"),
    Cue("IMG_1307", 8.22, 11.65, "D", "Se dice di no, allora scappiamo comunque."),
    Cue("IMG_1312", 0.46, 3.5, "D", "Abbiamo lavorato un anno. Vogliamo i nostri passaporti."),
    Cue("IMG_1314", 2.35, 3.3, "M", "No."),
    Cue("IMG_1311", 6.65, 7.6, "E", "Abbiamo un accordo."),
    Cue("IMG_1311", 8.28, 12.2, "M", "Voi siete qui perché io lo decido."),
    Cue("IMG_1320", 2.6, 8.3, "sfx", "[respiro affannoso, passi]"),
    Cue("IMG_1320", 8.4, 10.6, "sfx", "[la porta si apre, corrono]"),
    Cue("IMG_1320", 10.75, 11.9, "M", "Fermatevi!"),
    Cue("BLACK:S6g", 0.0, 2.9, "sfx", "[battito sempre più veloce]"),
    Cue("BLACK:S6g", 3.0, 4.3, "sfx", "[il battito si ferma]"),
    Cue("BLACK:S6g", 4.4, 5.5, "sfx", "[silenzio]"),
    # Blocco 4 novità
    Cue("IMG_1360", 0.0, 5.54, "I", "Ultima ora. Due donne straniere, scomparse da giorni, sono state ritrovate senza vita."),
    Cue("IMG_1360", 5.98, 10.86, "I", "Secondo i primi elementi, erano trattenute da una rete che aveva sequestrato i loro documenti."),
    Cue("IMG_1360", 11.04, 14.64, "I", "Un uomo è stato fermato per essere ascoltato dagli investigatori."),
    Cue("IMG_1360", 14.74, 27.92, "I", "Non sappiamo ancora se siano Dana ed Eva. Quello che abbiamo ricostruito è uno schema descritto dalle autorità."),
    Cue("IMG_1360", 27.92, 35.46, "I", "Dati precisi sugli omicidi di vittime di tratta sono difficili da avere, perché molti casi restano sommersi."),
    # La società
    Cue("IMG_1361", 0.91, 16.85, "B", "Parliamo di consenso: è valido solo se libero e informato. Se qualcuno ti toglie i documenti, ti isola e ti minaccia, non c'è libertà. Con una minorenne non c'è consenso possibile: la legge italiana punisce la prostituzione minorile e il suo sfruttamento."),
    Cue("IMG_1361", 16.85, 46.05, "B", "Ma non tutto è bianco o nero. Pensiamola come una scala: libertà, scelta, necessità economica, sfruttamento e violenza. Nel caso Parioli, la stampa riporta che le ragazze cercavano denaro per consumi di lusso, e non vivevano in condizioni di povertà estrema. Il condizionamento non è sempre economico, e c'è chi si prostituisce senza essere vittima di tratta. Ecco perché distinguere è importante."),
    Cue("IMG_1362", 126.0, 136.72, "B", "Dignità: nel caso Parioli, una giudice dispose che un cliente risarcisse le ragazze anche comprando libri sul pensiero femminile, per restituire loro la dignità lesa."),
    Cue("IMG_1362", 137.46, 143.14, "B", "Stereotipi: l'etichetta \"baby squillo\" sposta la colpa sulle ragazze, come osserva l'avvocata Manente."),
    # La domanda finale
    Cue("IMG_1363", 61.64, 64.52, "R", "Il corpo reagisce, ma non decide da solo."),
    Cue("IMG_1363", 64.74, 67.38, "B", "La legge protegge, ma non basta se nessuno guarda."),
    Cue("IMG_1363", 67.66, 70.22, "P", "E la mente interiorizza regole che non ha scelto."),
    Cue("IMG_1363", 70.56, 79.24, "T", "Quanto è libera una scelta quando le alternative sono state decise dal bisogno, dal desiderio indotto o dal potere di altri?"),
    Cue("IMG_1363", 79.54, 82.56, "P", "E allora: il nostro corpo determina ciò che siamo…"),
    Cue("IMG_1363", 83.02, 88.8, "P", "…oppure siamo noi, attraverso la psiche e la società, a dare significato al nostro corpo?"),
    # Escena final: Moro cuelga, mira el pasaporte y sonríe
    Cue("IMG_1368", 0.5, 1.7, "M", "Ho già risolto tutto."),
    Cue("IMG_1368", 2.9, 4.4, "sfx", "[riaggancia il telefono]"),
    Cue("IMG_1368", 5.8, 8.8, "sfx", "[silenzio]"),
]


GAP_MAX = 0.75   # silencios más largos que esto dentro de un plano hablado se acortan...
GAP_KEEP = 0.32  # ...a esta duración (corte oculto con reencuadre alternado)


def _words(clip, mic=None, mic_offset=0.0):
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "analisis" / "transcripciones"
    src = mic or clip
    data = json.loads((root / f"{src}.json").read_text(encoding="utf-8"))
    ws = [(w["s"] - (mic_offset if mic else 0), w["e"] - (mic_offset if mic else 0))
          for seg in data for w in seg["words"]]
    return sorted(ws)


def expand(shots=None):
    """Divide los planos hablados del canal en tramos sin silencios largos."""
    shots = shots or SHOTS
    out = []
    for s in shots:
        if s.look not in ("canal", "campo") or not s.clip or s.section == "finale":
            out.append(s)
            continue
        ws = [w for w in _words(s.clip, s.mic, s.mic_offset) if w[1] > s.tin and w[0] < s.tout]
        cuts = []
        for (a0, a1), (b0, b1) in zip(ws, ws[1:]):
            if b0 - a1 > GAP_MAX:
                cuts.append((a1 + GAP_KEEP / 2, b0 - GAP_KEEP / 2))
        if not cuts:
            out.append(s)
            continue
        t = s.tin
        pieces = []
        for c0, c1 in cuts:
            if c0 > t + 0.3:
                pieces.append((t, c0))
            t = max(t, c1)
        pieces.append((t, s.tout))
        from dataclasses import replace
        for i, (p0, p1) in enumerate(pieces):
            alt = s.punch if i % 2 == 0 else (1.0 if s.punch > 1.0 else 1.07)
            out.append(replace(s, id=f"{s.id}.{i}", tin=p0, tout=p1, punch=alt,
                               intro=s.intro if i == 0 else None,
                               fx=s.fx if i == 0 else [f for f in s.fx if f.startswith(("gfx", "map", "stat", "lt", "ticker"))],
                               ))
    return out


FPS = 30
FREEZE_END = 0.6  # segundos de imagen congelada añadidos por fx "freeze_end"


def body_frames(s: Shot) -> int:
    """Cuadros del cuerpo del plano (sin el freeze de presentación)."""
    base = s.dur if s.dur is not None else (s.tout - s.tin) / s.rate
    if "freeze_end" in s.fx:
        base += FREEZE_END
    return int(round(base * FPS))


def shot_len(s: Shot) -> float:
    """Duración cuantizada a cuadros (presentación de personaje = 1 s extra)."""
    return (body_frames(s) + (FPS if s.intro else 0)) / FPS


def timeline():
    """Devuelve [(shot, t_inicio_en_línea)] y la duración total."""
    t = 0.0
    out = []
    for s in expand():
        out.append((s, t))
        t += shot_len(s)
    return out, t


if __name__ == "__main__":
    tl, total = timeline()
    sec = {}
    for s, t0 in tl:
        sec[s.section] = sec.get(s.section, 0) + shot_len(s)
    for k, v in sec.items():
        print(f"{k:10s} {v:6.1f}")
    print(f"TOTAL {total:.1f} s = {int(total // 60)}:{total % 60:04.1f}")
