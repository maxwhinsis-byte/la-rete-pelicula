"""Genera la composición HyperFrames (composiciones/index.html) y los subtítulos .srt.

La imagen base (work/base.mp4) y la mezcla (work/mix.wav) se colocan como medios;
encima van los gráficos: apertura, título, interfaz DOSSIER, lower thirds, presentaciones de
personajes, infografías, carteles de la historia, transiciones, subtítulos, créditos.
Uso: .venv/Scripts/python scripts/build_hf.py
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import edl  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HF = ROOT / "composiciones"
TL = json.loads((ROOT / "work" / "timeline.json").read_text())
SHOTS = TL["shots"]
TOTAL = round(TL["total"], 3)
VOX = json.loads((ROOT / "work" / "audio" / "voces.json").read_text(encoding="utf-8"))
TR = ROOT / "analisis" / "transcripciones"
STORY_LOOKS = {"open", "s2", "s4", "s6", "post", "photo"}

E = html.escape
els: list[str] = []   # HTML de elementos temporizados
js: list[str] = []    # animaciones GSAP
_uid = [0]


def uid(p):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


def clip(cls, t, d, inner, track, style="", extra=""):
    i = uid(cls[:3])
    els.append(f'<div id="{i}" class="clip {cls}" data-start="{t:.3f}" data-duration="{d:.3f}" '
               f'data-track-index="{track}" style="{style}" {extra}>{inner}</div>')
    return i


def shot(id_):
    return next(s for s in SHOTS if s["id"] == id_)


def shots_of(prefix):
    return [s for s in SHOTS if s["id"] == prefix or s["id"].startswith(prefix + ".")]


# ------------------------------------------------------------------ mapeo de tiempo

def _cands(clip_name, sid=""):
    return [s for s in SHOTS if s["clip"] == clip_name and s["clip"] is not None
            and (not sid or s["id"] == sid or s["id"].startswith(sid + "."))]


def map_src(clip_name, t, sid=""):
    """Tiempo de fuente -> tiempo en la línea (None si ese instante fue cortado)."""
    best = None
    for s in _cands(clip_name, sid):
        if s["tin"] - 1e-3 <= t <= s["tout"] + 1e-3:
            return s["body_start"] + (t - s["tin"]) / s["rate"]
        if t < s["tin"] and (best is None or s["tin"] < best[0]):
            best = (s["tin"], s["body_start"])
    return None


def map_src_snap(clip_name, t, direction, sid=""):
    v = map_src(clip_name, t, sid)
    if v is not None:
        return v
    # si cae en un hueco cortado, se pega al borde del tramo más cercano
    cands = []
    for s in _cands(clip_name, sid):
        if direction > 0 and s["tin"] >= t:
            cands.append((s["tin"] - t, s["body_start"]))
        if direction < 0 and s["tout"] <= t:
            cands.append((t - s["tout"], s["body_start"] + (s["tout"] - s["tin"]) / s["rate"]))
    if not cands:
        return None
    d, v = min(cands)
    return v if d < 1.5 else None


def words_for(clip_name, s, e):
    f = TR / f"{clip_name}.json"
    if not f.exists():
        return []
    data = json.loads(f.read_text(encoding="utf-8"))
    return [(w["s"], w["e"], w["w"]) for seg in data for w in seg["words"] if s - 0.05 <= w["s"] < e + 0.05]


def chunk_text(text, maxc=80):
    """Divide en k trozos parecidos (k mínimo para no pasar de maxc), cortando en puntuación si se puede."""
    import math
    words = text.split()
    k = max(1, math.ceil(len(text) / maxc))
    while True:
        target = len(text) / k
        chunks, cur = [], []
        for i, w in enumerate(words):
            cur.append(w)
            cl = len(" ".join(cur))
            rest_words = len(words) - i - 1
            if len(chunks) < k - 1 and rest_words > 0:
                punct = re.search(r"[,.;:?!…]$", w)
                if (cl >= target * 0.8 and punct) or cl >= target * 1.12:
                    chunks.append(" ".join(cur))
                    cur = []
        if cur:
            chunks.append(" ".join(cur))
        if max(len(c) for c in chunks) <= maxc + 6 or k > 8:
            return chunks
        k += 1


def two_lines(t, maxl=42):
    if len(t) <= maxl:
        return [t]
    words = t.split()
    best, bi = 1e9, 1
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) > maxl + 4 or len(b) > maxl + 4:
            continue
        score = abs(len(a) - len(b)) - (8 if re.search(r"[,.;:?!]$", a) else 0)
        if score < best:
            best, bi = score, i
    return [" ".join(words[:bi]), " ".join(words[bi:])]


def shot_at(t):
    for s in SHOTS:
        if s["start"] - 1e-6 <= t < s["end"]:
            return s
    return SHOTS[-1]


SUBS = []  # (t0, t1, who, lines)


def build_subs():
    last_scene_who = set()
    cur_section = None
    for c in edl.CUES:
        if c.clip.startswith("BLACK:"):
            s = shot(c.clip[6:])
            spans = [(c.s, c.e, s["start"] + c.s, s["start"] + c.e)]
            chunks = [c.text]
        elif c.clip.startswith("PHOTO:"):
            s = next((x for x in SHOTS if x["clip"] == c.clip), None)
            if not s:
                continue
            spans = [(c.s, c.e, s["start"] + c.s, s["start"] + c.e)]
            chunks = [c.text]
        else:
            chunks = chunk_text(c.text) if c.who != "sfx" else [c.text]
            ws = words_for(c.clip, c.s, c.e)
            total_chars = sum(len(x) for x in chunks)
            bounds = [c.s]
            acc = 0
            for ch in chunks[:-1]:
                acc += len(ch)
                tb = c.s + acc / total_chars * (c.e - c.s)
                near = [w[0] for w in ws if abs(w[0] - tb) < 0.7]
                bounds.append(min(near, key=lambda x: abs(x - tb)) if near else tb)
            bounds.append(c.e)
            spans = []
            for a, b in zip(bounds, bounds[1:]):
                t0 = map_src_snap(c.clip, a, +1, c.sid)
                t1 = map_src_snap(c.clip, b, -1, c.sid)
                if t0 is not None and t1 is not None and t1 - t0 > (b - a) / 0.9 + 2.0:
                    t1 = None  # el final cayó en otra aparición del clip: se descarta
                spans.append((a, b, t0, t1))
        for ch, (a, b, t0, t1) in zip(chunks, spans):
            if t0 is None or t1 is None or t1 - t0 < 0.25:
                continue
            sh = shot_at(t0 + 0.01)
            sec = sh["section"]
            if sec != cur_section:
                cur_section, last_scene_who = sec, set()
            label = None
            if c.who in ("D", "E", "M") and c.who not in last_scene_who:
                label = edl.SPEAKERS[c.who][0]
                last_scene_who.add(c.who)
            SUBS.append(dict(t0=t0, t1=t1, who=c.who, label=label, text=ch, look=sh["look"]))
    SUBS.sort(key=lambda x: x["t0"])
    # sin solapes y con duración mínima legible
    for a, b in zip(SUBS, SUBS[1:]):
        if a["t1"] > b["t0"] - 0.04:
            a["t1"] = b["t0"] - 0.04
    for x in SUBS:
        x["t1"] = max(x["t1"], x["t0"] + 0.7)
    for a, b in zip(SUBS, SUBS[1:]):
        if a["t1"] > b["t0"] - 0.04:
            a["t1"] = b["t0"] - 0.04


def place_subs():
    for x in SUBS:
        story = x["look"] in STORY_LOOKS
        black = x["look"] == "black"
        lines = two_lines(x["text"])
        color = edl.SPEAKERS.get(x["who"], ("", "#ffffff"))[1] if x["who"] not in ("", "sfx") else "#ffffff"
        cls = "sub " + ("sub-story" if story else "sub-black" if black else "sub-tv") + (" sub-sfx" if x["who"] == "sfx" else "")
        lab = f'<span class="who" style="color:{color}">{E(x["label"])}</span>' if x["label"] else ""
        inner = lab + "".join(f'<span class="ln" style="color:{color}">{E(l)}</span>' for l in lines)
        clip(cls, x["t0"], x["t1"] - x["t0"], f'<div class="sub-in">{inner}</div>', 40)


def write_srt():
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out = []
    allsubs = sorted(SUBS + OPEN_SUBS, key=lambda x: x["t0"])
    for i, x in enumerate(allsubs, 1):
        txt = "\n".join(two_lines(x["text"]))
        if x.get("label"):
            txt = f"{x['label']}: " + txt
        out.append(f"{i}\n{ts(x['t0'])} --> {ts(x['t1'])}\n{txt}\n")
    (ROOT / "subtitulos").mkdir(exist_ok=True)
    (ROOT / "subtitulos" / "La_rete.srt").write_text("\n".join(out), encoding="utf-8")


# ------------------------------------------------------------------ apertura

OPEN_SUBS = []
LANG_NAME = dict(it="it", es="es", fr="fr", en="en", de="de", pt="pt", ru="ru", ar="ar", zh="zh", ja="ja", tl="tl", hi="hi")


def opening():
    a2 = shot("A2")
    t0 = a2["start"]
    # palabras sincronizadas con cada golpe
    seen = 0
    for ev in VOX["events"]:
        t = t0 + ev["t"]
        if t >= t0 + VOX["impact"]:
            continue
        d = (t0 + VOX["impact"]) - t
        size = ev["size"] if seen >= 4 else 120
        font = {"ar": "NotoArabic", "hi": "NotoDeva", "zh": "NotoSC", "ja": "NotoJP"}.get(ev["lang"], "Inter")
        yy = 0.10 + (ev["y"] - 0.12) / 0.76 * 0.64 if seen >= 4 else ev["y"]  # deja libre la zona de subtítulos
        style = (f"left:{ev['x'] * 100:.1f}%;top:{yy * 100:.1f}%;font-size:{size:.0f}px;font-family:'{font}'")
        i = clip("vw", t, d, f'<span class="vw-in">{E(ev["word"])}</span>', 20, style,
                 'data-layout-allow-overlap="true"')
        js.append(f'tl.fromTo("#{i} .vw-in",{{opacity:0,scale:1.35}},{{opacity:{0.95 if seen < 12 else 0.75},scale:1,duration:0.16,ease:"power4.out"}},{t:.3f});')
        if seen < 4:  # los primeros golpes, lentos: una palabra por vez
            js.append(f'tl.to("#{i} .vw-in",{{opacity:0,duration:0.6}},{t + 0.7:.3f});')
        else:
            js.append(f'tl.to("#{i} .vw-in",{{opacity:{0.55 if seen < 12 else 0.4},duration:0.5}},{t + 0.25:.3f});')
        seen += 1
        if seen <= 12:
            OPEN_SUBS.append(dict(t0=t, t1=t + 0.9, who="", label=None, look="black",
                                  text=f"«{ev['word']}» ({LANG_NAME[ev['lang']]})"))
    # subtítulo descriptivo de la parte densa
    first_dense = t0 + VOX["beats"][12]
    OPEN_SUBS.append(dict(t0=first_dense, t1=t0 + VOX["impact"], who="sfx", label=None, look="black",
                          text="[voci sovrapposte: «prostituzione» in tante lingue, battito sempre più veloce]"))
    # el retroceso: al impacto todas las palabras se van hacia atrás
    imp = t0 + VOX["impact"]
    js.append(f'tl.to(".vw",{{scale:0.05,opacity:0,filter:"blur(6px)",duration:1.1,ease:"expo.in",stagger:{{each:0.002,from:"center"}}}},{imp - 0.1:.3f});')
    # luz roja tenue que tiembla
    i = clip("redflick", t0, a2["end"] - t0, "", 19)
    js.append(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:0.5,duration:2}},{t0:.3f});')
    for k in range(7, int((a2["end"] - t0) * 3)):
        tt = t0 + k / 3
        js.append(f'tl.to("#{i}",{{opacity:{0.25 + ((k * 37) % 10) / 25:.2f},duration:0.1}},{tt:.3f});')
    # título
    a3 = shot("A3")
    T = a3["start"]
    inner = ('<div class="ttl-sweep"></div><div class="ttl-wrap"><div class="ttl-main">LA RETE</div>'
             '<div class="ttl-sub">Essere “femmine” nella prostituzione</div></div>')
    i = clip("ttl", T, a3["end"] - T, inner, 21)
    js.append(f'tl.fromTo("#{i} .ttl-main",{{opacity:0,scale:2.6,scaleX:3.4,filter:"blur(14px)"}},'
              f'{{opacity:1,scale:1,scaleX:1,filter:"blur(0px)",duration:1.0,ease:"expo.out"}},{T + 0.35:.3f});')
    js.append(f'tl.fromTo("#{i} .ttl-sweep",{{xPercent:-120,opacity:0}},{{xPercent:120,opacity:0.9,duration:1.6,ease:"power2.inOut"}},{T + 0.45:.3f});')
    js.append(f'tl.fromTo("#{i} .ttl-sub",{{opacity:0,y:18}},{{opacity:0.85,y:0,duration:0.9,ease:"power3.out"}},{T + 1.4:.3f});')
    js.append(f'tl.fromTo("#{i} .ttl-wrap",{{scale:1}},{{scale:1.04,duration:{a3["end"] - T - 1:.2f},ease:"none"}},{T + 1.0:.3f});')
    js.append(f'tl.to("#{i} .ttl-wrap",{{opacity:0,duration:1.4,ease:"power2.in"}},{a3["end"] - 1.6:.3f});')
    OPEN_SUBS.append(dict(t0=T + 0.3, t1=T + 2.2, who="sfx", label=None, look="black", text="[impatto]"))
    OPEN_SUBS.append(dict(t0=T + 2.4, t1=a3["end"] - 0.3, who="", label=None, look="black",
                          text="LA RETE — Essere “femmine” nella prostituzione"))
    # pasaportes: subtítulos ya están en CUES; fundido desde negro
    a1 = shot("A1")
    i = clip("fadeblack", a1["start"], 1.6, "", 30)
    js.append(f'tl.fromTo("#{i}",{{opacity:1}},{{opacity:0,duration:1.5}},{a1["start"]:.3f});')
    # Lara: del negro a la luz blanca del estudio
    a4 = shot("A4")
    i = clip("fadewhite", a4["start"], 1.2, "", 30)
    js.append(f'tl.fromTo("#{i}",{{opacity:1}},{{opacity:0,duration:1.1,ease:"power2.out"}},{a4["start"]:.3f});')


# ------------------------------------------------------------------ interfaz DOSSIER

TICKER = {
    "b1": "Segnalazione anonima: due giovani donne straniere trattenute in un appartamento  ·  Le autorità non confermano",
    "b2": "La polizia verifica l'appartamento: trovati fogli con un debito che cresce mese dopo mese  ·  Un telefono non funzionante",
    "b3": "Gli investigatori ricevono un testo scritto a mano: «Io vi proteggo»  ·  «Quando avrete pagato»",
    "b4": "ULTIMA ORA — Ritrovate senza vita due donne straniere  ·  Un uomo fermato dagli investigatori",
}
BLOCK_OF = {"apertura": "b1", "b1": "b1", "t1": "b1", "fen": "b1", "b2": "b2", "t2": "b2", "corpo": "b2",
            "b3": "b3", "psiche": "b3", "b4": "b4", "soc": "b4", "finale": "b4"}


def tv_intervals():
    iv = []
    for s in SHOTS:
        tv = s["look"] in ("canal", "campo") or (s["look"] == "transform")
        if not tv:
            continue
        a = s["start"] + (s["end"] - s["start"]) * 0.75 if s["look"] == "transform" else s["start"]
        if s["intro"]:
            a = s["body_start"]
        blk = BLOCK_OF.get(s["section"], "b1")
        if iv and abs(iv[-1][1] - a) < 0.05 and iv[-1][2] == blk:
            iv[-1][1] = s["end"]
        elif iv and abs(iv[-1][1] - s["start"]) < 0.05 and iv[-1][2] == blk:
            iv[-1][1] = s["end"]
        else:
            iv.append([a, s["end"], blk])
    return iv


def dossier_ui():
    for a, b, blk in tv_intervals():
        d = b - a
        if d < 1.0:
            continue
        clk = uid("clk")
        live = blk != "b4" or True
        inner = ('<div class="bug"><span class="bug-logo">DOSSIER</span>'
                 '<span class="bug-live"><i class="dot"></i>IN DIRETTA</span></div>'
                 f'<div class="clock"><span id="{clk}">21:04</span></div>')
        i = clip("tvui", a, d, inner, 31)
        js.append(f'tl.fromTo("#{i} .bug",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:0.5,ease:"power3.out"}},{a + 0.15:.3f});')
        js.append(f'tl.fromTo("#{i} .clock",{{opacity:0}},{{opacity:1,duration:0.5}},{a + 0.25:.3f});')
        js.append(f'clockSpan("#{clk}",{a:.3f},{d:.3f});')
        js.append(f'tl.fromTo("#{i} .dot",{{opacity:1}},{{opacity:0.25,duration:0.6,repeat:{max(0, int(d / 1.2) - 1)},yoyo:true,ease:"sine.inOut"}},{a:.3f});')
        if blk and d > 6 and not (blk == "b4" and False):
            text = TICKER[blk]
            inner = (f'<div class="tk-label">{"ULTIM&#39;ORA" if blk == "b4" else "IL CASO"}</div>'
                     f'<div class="tk-track"><span class="tk-text">{E(text)}   ·   {E(text)}   ·   {E(text)}</span></div>')
            j = clip("ticker", a, d, inner, 32)
            js.append(f'tl.fromTo("#{j}",{{y:60}},{{y:0,duration:0.5,ease:"power3.out"}},{a + 0.3:.3f});')
            js.append(f'tl.fromTo("#{j} .tk-text",{{x:0}},{{x:{-min(2600, 90 * d):.0f},duration:{d:.2f},ease:"none"}},{a:.3f});')


def lower_third(t, name, role, d=5.5):
    inner = f'<div class="lt-box"><div class="lt-rule"></div><div class="lt-name">{E(name)}</div><div class="lt-role">{E(role)}</div></div>'
    i = clip("lt", t, d, inner, 33)
    js.append(f'tl.fromTo("#{i} .lt-rule",{{scaleX:0}},{{scaleX:1,duration:0.45,ease:"power3.out"}},{t:.3f});')
    js.append(f'tl.fromTo("#{i} .lt-name",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{t + 0.12:.3f});')
    js.append(f'tl.fromTo("#{i} .lt-role",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{t + 0.22:.3f});')
    js.append(f'tl.to("#{i} .lt-box",{{opacity:0,x:-20,duration:0.35,ease:"power2.in"}},{t + d - 0.4:.3f});')


LT = {
    "inviato": ("In collegamento", "Inviato di Dossier · sul posto"),
    "bianchi_campo": ("Giulia Bianchi", "Inviata · Educazione civica"),
    "rossi": ("Dr. Rossi", "Chimica e Biologia"),
    "petrotali": ("Prof. Petrotali", "Filosofia"),
}


def source_tag(t, d, refs):
    inner = "".join(f'<span class="src">[{r}]</span>' for r in refs)
    i = clip("srctag", t, d, f'<div class="src-in">{inner}</div>', 34)
    js.append(f'tl.fromTo("#{i} .src-in",{{opacity:0,y:-8}},{{opacity:1,y:0,duration:0.35}},{t:.3f});')


# fuentes que acompañan a cada afirmación (clip, inicio del subtítulo de fuente) -> [n]
SOURCES = {
    ("IMG_1339", 45.44): [1], ("IMG_1339", 58.26): [2], ("IMG_1339", 94.28): [1, 2, 3],
    ("IMG_1340", 0.24): [7], ("IMG_1340", 21.64): [4, 5],
    ("IMG_1347", 98.06): [10], ("IMG_1347", 112.28): [10],
    ("IMG_1350", 25.39): [11], ("IMG_1351", 19.14): [12],
    ("IMG_1359", 46.62): [13, 14], ("IMG_1359", 98.52): [13, 14],
    ("IMG_1361", 0.91): [9], ("IMG_1361", 16.85): [5], ("IMG_1362", 137.46): [5],
    ("IMG_1360", 27.92): [7],
}


def place_sources():
    for (c, s), refs in SOURCES.items():
        cue = next((x for x in edl.CUES if x.clip == c and abs(x.s - s) < 0.01), None)
        if not cue:
            continue
        t0 = map_src_snap(c, cue.s, +1)
        t1 = map_src_snap(c, cue.e, -1)
        if t0 is None or t1 is None:
            continue
        source_tag(t0 + 0.2, max(2.5, t1 - t0), refs)


# ------------------------------------------------------------------ presentación de personajes

def intros():
    for s in SHOTS:
        it = s["intro"]
        if not it:
            continue
        t = s["start"]
        name, actor, desc = edl.INTRO_TEXT[it["who"]]
        story = it["kind"] == "storia"
        tx, ty = it["x"] * 1920, it["y"] * 1080
        left = tx > 960
        # tarjeta del lado contrario al personaje, a media altura
        cx = 150 if left else 1920 - 150 - 620
        cy = 560 if story else 520
        ax0 = cx + (620 if left else 0)
        ay0 = cy + 60
        ax1 = tx + (-90 if left else 90)
        ay1 = ty + 170
        mx, my = (ax0 + ax1) / 2, min(ay0, ay1) - 60
        path = f"M{ax0:.0f},{ay0:.0f} Q{mx:.0f},{my:.0f} {ax1:.0f},{ay1:.0f}"
        ang = 0
        cls = "intro-story" if story else "intro-tv"
        inner = (f'<svg class="arrow" viewBox="0 0 1920 1080" width="1920" height="1080">'
                 f'<path class="arr-p" d="{path}" pathLength="1"/>'
                 f'<circle class="arr-dot" cx="{ax1:.0f}" cy="{ay1:.0f}" r="7"/></svg>'
                 f'<div class="card" style="left:{cx}px;top:{cy}px">'
                 f'<div class="c-name">{E(name)}</div><div class="c-actor">{E(actor)}</div>'
                 f'<div class="c-desc">«{E(desc)}»</div></div>')
        i = clip(cls, t, 1.0, inner, 35)
        js.append(f'tl.fromTo("#{i} .arr-p",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.3,ease:"power2.out"}},{t + 0.05:.3f});')
        js.append(f'tl.fromTo("#{i} .arr-dot",{{opacity:0,scale:0.3}},{{opacity:1,scale:1,duration:0.2,transformOrigin:"50% 50%"}},{t + 0.3:.3f});')
        js.append(f'tl.fromTo("#{i} .card",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.25,ease:"power3.out"}},{t + 0.08:.3f});')
        js.append(f'tl.to("#{i}",{{opacity:0,duration:0.12}},{t + 0.87:.3f});')


# ------------------------------------------------------------------ historia: carteles

def story_cards():
    labels = {"S2a": ("Ricostruzione", "Il giorno dell'arrivo"),
              "S4a": ("Ricostruzione", "I mesi successivi"),
              "S6a": ("Ricostruzione", "L'ultimo mese")}
    for sid, (a, b) in labels.items():
        s = shot(sid)
        t = s["start"]
        inner = f'<div class="rc-a">{E(a)}</div><div class="rc-b">{E(b)}</div>'
        i = clip("recon", t, 3.6, inner, 36)
        js.append(f'tl.fromTo("#{i} .rc-a",{{opacity:0,x:-18}},{{opacity:0.85,x:0,duration:1.2,ease:"power2.out"}},{t + 0.2:.3f});')
        js.append(f'tl.fromTo("#{i} .rc-b",{{opacity:0,y:8}},{{opacity:1,y:0,duration:1.0,ease:"power2.out"}},{t + 0.5:.3f});')
        js.append(f'tl.to("#{i}",{{opacity:0,duration:0.6}},{t + 2.9:.3f});')
    for s in SHOTS:
        for f in s["fx"]:
            if f.startswith("card:Mese"):
                t = s["start"]
                d = s["end"] - t
                txt = f[5:]
                i = clip("mese", t, d, f'<div class="mese-in">{E(txt)}</div>', 37)
                js.append(f'tl.fromTo("#{i} .mese-in",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.8,ease:"power2.out"}},{t + 0.15:.3f});')
                js.append(f'tl.to("#{i} .mese-in",{{opacity:0,duration:0.5}},{t + d - 0.6:.3f});')


def glitches():
    """Estática de señal en los pasajes canal <-> historia."""
    pts = []
    for a, b in zip(SHOTS, SHOTS[1:]):
        ta = a["look"] in ("canal", "campo")
        sb = b["look"] in STORY_LOOKS
        sa = a["look"] in STORY_LOOKS
        tb = b["look"] in ("canal", "campo")
        if (ta and sb) or (sa and tb and b["section"] != "post"):
            pts.append(b["start"])
    pts.append(shot("S6a")["start"])  # canal -> cartel "Mese 12" (negro de la historia)
    for t in pts:
        bars = "".join(f'<i style="top:{(k * 137) % 1000}px;height:{8 + (k * 53) % 40}px"></i>' for k in range(9))
        i = clip("glitch", t - 0.2, 0.42, f'<div class="gl-noise"></div><div class="gl-bars">{bars}</div>', 38)
        js.append(f'tl.fromTo("#{i} .gl-bars i",{{x:-60,opacity:0.9}},{{x:60,opacity:0.2,duration:0.07,repeat:5,yoyo:true,stagger:0.01}},{t - 0.2:.3f});')
        js.append(f'tl.fromTo("#{i} .gl-noise",{{opacity:0.55}},{{opacity:0,duration:0.42,ease:"power2.in"}},{t - 0.2:.3f});')
    return pts


# ------------------------------------------------------------------ infografías

def panel(t, d, inner, cls="pnl-right", track=39):
    i = clip("pnl " + cls, t, d, f'<div class="pnl-in">{inner}</div>', track)
    js.append(f'tl.fromTo("#{i} .pnl-in",{{opacity:0,x:40}},{{opacity:1,x:0,duration:0.55,ease:"power3.out"}},{t:.3f});')
    js.append(f'tl.fromTo("#{i} .pi",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.45,stagger:0.35,ease:"power2.out"}},{t + 0.35:.3f});')
    js.append(f'tl.to("#{i} .pnl-in",{{opacity:0,x:30,duration:0.4,ease:"power2.in"}},{t + d - 0.45:.3f});')
    return i


def at_cue(c, s):
    cue = next(x for x in edl.CUES if x.clip == c and abs(x.s - s) < 0.01)
    t0 = map_src_snap(c, cue.s, +1)
    t1 = map_src_snap(c, cue.e, -1)
    return t0, t1


def infographics():
    # --- Il fenomeno: la red de la historia antigua
    t0, _ = at_cue("IMG_1339", 45.44)
    _, t1 = at_cue("IMG_1339", 95.28)
    nodes = [("MESOPOTAMIA", "testi cuneiformi · traduzioni discusse", "[1]", 300, 150),
             ("INDIA", "Arthashastra · circa 2300 anni fa · tasse allo Stato", "[2]", 470, 330),
             ("CINA", "regole diverse secondo lo status", "[3]", 160, 470)]
    svg = ('<svg class="net" viewBox="0 0 620 600" width="620" height="600">'
           '<path class="ln1" d="M300,150 L470,330" pathLength="1"/><path class="ln2" d="M470,330 L160,470" pathLength="1"/>'
           '<path class="ln3" d="M160,470 L300,150" pathLength="1"/></svg>')
    nhtml = "".join(f'<div class="node n{k}" style="left:{x}px;top:{y}px"><i></i><b>{n}</b><span>{E(dsc)} <em>{r}</em></span></div>'
                    for k, (n, dsc, r, x, y) in enumerate(nodes))
    inner = f'<div class="pi pnl-h">Più di 4000 anni · non solo in Occidente</div><div class="netwrap">{svg}{nhtml}</div>'
    i = clip("pnl pnl-right pnl-map", t0, t1 - t0 + 0.5, f'<div class="pnl-in">{inner}</div>', 39)
    js.append(f'tl.fromTo("#{i} .pnl-in",{{opacity:0,x:40}},{{opacity:1,x:0,duration:0.55,ease:"power3.out"}},{t0:.3f});')
    js.append(f'tl.fromTo("#{i} .pnl-h",{{opacity:0}},{{opacity:1,duration:0.5}},{t0 + 0.3:.3f});')
    ti, _ = at_cue("IMG_1339", 58.6)
    tf, _ = at_cue("IMG_1339", 95.28)
    for k, tt in enumerate([t0 + 0.4, ti, tf]):
        js.append(f'tl.fromTo("#{i} .n{k}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.5,ease:"back.out(1.6)"}},{tt:.3f});')
    js.append(f'tl.fromTo("#{i} .ln1",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8}},{ti + 0.2:.3f});')
    js.append(f'tl.fromTo("#{i} .ln2",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8}},{tf + 0.2:.3f});')
    js.append(f'tl.fromTo("#{i} .ln3",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8}},{tf + 0.6:.3f});')
    js.append(f'tl.to("#{i} .pnl-in",{{opacity:0,duration:0.4}},{t1 + 0.05:.3f});')

    # --- ONU
    t0, t1 = at_cue("IMG_1340", 5.5)
    panel(t0 + 0.8, t1 - t0 - 0.6,
          '<div class="pi pnl-h">UNODC · Rapporto globale 2024 <em>[7]</em></div>'
          '<div class="pi big">61<small>%</small></div><div class="pi cap">delle vittime di tratta individuate nel 2022: donne e ragazze</div>'
          '<div class="pi big">60<small>%</small></div><div class="pi cap">delle ragazze vittime: sfruttamento sessuale</div>'
          '<div class="pi note">Sono casi individuati: molto resta sommerso.</div>')
    t0, t1 = at_cue("IMG_1340", 21.64)
    panel(t0 + 0.6, t1 - t0 - 0.4,
          '<div class="pi pnl-h">Roma · quartiere Parioli · 2013 <em>[4]</em></div>'
          '<div class="pi cap">Due ragazze di 14 e 15 anni sfruttate da adulti. Condannati i responsabili.</div>'
          '<div class="pi quote">“baby squillo”</div><div class="pi cap">un nome che sposta la colpa sulle ragazze <em>[5]</em></div>')

    # --- Il corpo
    t0, t1 = at_cue("IMG_1347", 45.34)
    i = clip("words3", t0, t1 - t0 + 0.4, '<div class="w3"><span>STRESS</span><i>·</i><span>DESIDERIO / RICOMPENSA</span><i>·</i><span>SALUTE</span></div>', 39)
    js.append(f'tl.fromTo("#{i} .w3 span, #{i} .w3 i",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.4,stagger:0.18}},{t0 + 0.2:.3f});')
    js.append(f'tl.to("#{i} .w3",{{opacity:0,duration:0.4}},{t1:.3f});')
    t0, _ = at_cue("IMG_1347", 65.45)
    _, t1 = at_cue("IMG_1347", 88.9)
    panel(t0 + 0.3, t1 - t0 - 0.1,
          '<div class="pi pnl-h">Risposta rapida · secondi</div>'
          '<div class="pi chain"><b>minaccia</b><i>→</i><b>sistema nervoso simpatico</b></div>'
          '<div class="pi chain"><i>→</i><b>midollare del surrene</b><i>→</i><b>adrenalina · noradrenalina</b></div>'
          '<div class="pi chain up"><span>cuore ↑</span><span>pressione ↑</span><span>sangue ai muscoli ↑</span></div>'
          '<div class="pi note">“lotta o fuga”</div>')
    t0, _ = at_cue("IMG_1347", 92.92)
    _, t1 = at_cue("IMG_1347", 123.52)
    i = panel(t0 + 0.2, t1 - t0 + 0.3,
              '<div class="pi pnl-h">Risposta lenta · minuti <em>[10]</em></div>'
              '<div class="hpa"><div class="pi h-n">IPOTALAMO</div><div class="pi h-a">CRH ↓</div>'
              '<div class="pi h-n">IPOFISI</div><div class="pi h-a">ACTH ↓</div>'
              '<div class="pi h-n">CORTICALE DEL SURRENE</div><div class="pi h-a">↓</div>'
              '<div class="pi h-n h-c">CORTISOLO</div>'
              '<div class="pi h-fb">feedback negativo: il cortisolo frena la catena</div></div>')
    t0, t1 = at_cue("IMG_1347", 155.38)
    panel(t0 + 0.2, t1 - t0,
          '<div class="pi pnl-h">Stress cronico</div><div class="pi cap">L&#39;asse può restare attivo.</div>'
          '<div class="pi cap">Il feedback può funzionare meno bene.</div><div class="pi note">quadri generali, non casi individuali</div>')
    t0, _ = at_cue("IMG_1347", 186.84)
    _, t1 = at_cue("IMG_1347", 186.84)
    panel(t0 + 0.2, t1 - t0 + 0.2,
          '<div class="pi pnl-h">Coinvolte, non “cause”</div>'
          '<div class="pi pair"><b>DOPAMINA</b><span>ricompensa · motivazione · anticipazione del piacere</span></div>'
          '<div class="pi pair"><b>OSSITOCINA</b><span>legame · fiducia</span></div>')
    t0, t1 = at_cue("IMG_1347", 213.92)
    i = clip("fullcard", t0 + 0.6, t1 - t0 - 0.5, '<div class="fc-in"><div class="fc-l">Ipotesi ≠ dimostrazione.</div><div class="fc-l">Associazione ≠ causa.</div></div>', 39)
    js.append(f'tl.fromTo("#{i} .fc-l",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.6,stagger:0.6,ease:"power3.out"}},{t0 + 0.7:.3f});')
    js.append(f'tl.fromTo("#{i}",{{backgroundColor:"rgba(8,12,20,0)"}},{{backgroundColor:"rgba(8,12,20,0.55)",duration:0.5}},{t0 + 0.6:.3f});')
    js.append(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{t1 - 0.2:.3f});')
    t0, t1 = at_cue("IMG_1350", 5.07)
    panel(t0 + 0.3, t1 - t0 + 0.4, '<div class="pi big-t">Una reazione del corpo <u>non</u> è un consenso.</div>'
          '<div class="pi cap">Il consenso è una decisione libera.</div>')
    t0, t1 = at_cue("IMG_1350", 25.39)
    panel(t0 + 0.4, t1 - t0,
          '<div class="pi pnl-h">Revisione di 19 studi <em>[11]</em></div>'
          '<div class="pi tags"><span>ansia</span><span>depressione</span><span>stress post-traumatico</span><span>dolori fisici</span><span>IST</span></div>'
          '<div class="pi note">Evidenza limitata: associazioni, non cause.</div>')
    t0, _ = at_cue("IMG_1351", 19.38)
    _, t1 = at_cue("IMG_1351", 34.94)
    panel(t0 + 0.2, t1 - t0,
          '<div class="pi pnl-h">Mito e realtà <em>[12]</em></div>'
          '<div class="pi myth"><s>“Il preservativo protegge da tutto”</s></div>'
          '<div class="pi cap">Riduce molto il rischio di HIV e di molte IST; contro herpes, sifilide e HPV protegge solo in parte.</div>'
          '<div class="pi myth"><s>“Chi lavora in questo ambito sceglie come proteggersi”</s></div>'
          '<div class="pi cap">Chi vive isolata e controllata ha poco potere di negoziare.</div>')
    # --- Blocco 3: le frasi
    t0, t1 = at_cue("IMG_1353", 15.54)
    i = clip("pnl pnl-right", t0 + 1.0, t1 - t0 + 1.2,
             '<div class="pnl-in paper"><div class="pi pnl-h">Il testo scritto a mano</div>'
             '<div class="pi hand">«Io vi proteggo.»</div><div class="pi hand">«Quando avrete pagato.»</div>'
             '<div class="pi hand">«Non abbiamo scelta.»</div></div>', 39)
    js.append(f'tl.fromTo("#{i} .pnl-in",{{opacity:0,x:40}},{{opacity:1,x:0,duration:0.5}},{t0 + 1.0:.3f});')
    js.append(f'tl.fromTo("#{i} .pi",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.5,stagger:1.3}},{t0 + 1.2:.3f});')
    # --- La psiche
    t0, _ = at_cue("IMG_1359", 46.62)
    _, t1 = at_cue("IMG_1359", 76.2)
    i = clip("pillars", t0 + 0.6, t1 - t0 + 0.2,
             '<div class="pl-in"><div class="pl p-es"><b>ES</b><span>principio di piacere</span><em>«scappare»</em></div>'
             '<div class="pl p-io"><b>IO</b><span>principio di realtà</span><em>debito · passaporto · polizia</em></div>'
             '<div class="pl p-si"><b>SUPER-IO</b><span>morale interiorizzata</span><em>vergogna e colpa</em></div>'
             '<div class="pl-src">Freud <em>[13] [14]</em></div></div>', 39)
    js.append(f'tl.fromTo("#{i} .pl",{{opacity:0,y:-20}},{{opacity:1,y:0,duration:0.5,stagger:0.3,ease:"power3.out"}},{t0 + 0.6:.3f});')
    js.append(f'tl.fromTo("#{i} .pl-src",{{opacity:0}},{{opacity:1,duration:0.4}},{t0 + 1.6:.3f});')
    tq, _ = at_cue("IMG_1359", 62.52)
    tz, _ = at_cue("IMG_1359", 76.2)
    js.append(f'tl.fromTo("#{i} .pl em",{{opacity:0}},{{opacity:1,duration:0.4,stagger:0.5}},{tq + 1.5:.3f});')
    js.append(f'tl.to("#{i} .p-io",{{borderColor:"rgba(215,38,61,0.9)",duration:0.4}},{tq + 2.5:.3f});')
    js.append(f'tl.to("#{i} .p-io",{{borderColor:"rgba(143,163,191,0.35)",duration:0.4}},{tz:.3f});')
    js.append(f'tl.to("#{i} .p-si",{{borderColor:"rgba(215,38,61,0.9)",duration:0.4}},{tz + 0.2:.3f});')
    js.append(f'tl.to("#{i} .pl-in",{{opacity:0,duration:0.4}},{t1 + 0.1:.3f});')
    t0, _ = at_cue("IMG_1359", 85.9)
    _, t1 = at_cue("IMG_1359", 104.82)
    i = clip("pillars", t0 + 0.3, t1 - t0 - 0.2,
             '<div class="pl-in"><div class="pl wide"><b>RAZIONALIZZAZIONE</b><span>«Io vi proteggo» · «vi ho dato tutto»</span></div>'
             '<div class="pl wide"><b>SUPER-IO COLLETTIVO</b><span>norme · divieti · tabù — Il disagio della civiltà <em>[13] [14]</em></span></div></div>', 39)
    js.append(f'tl.fromTo("#{i} .pl",{{opacity:0,y:-20}},{{opacity:1,y:0,duration:0.5,stagger:0.25}},{t0 + 0.3:.3f});')
    tz, _ = at_cue("IMG_1359", 98.52)
    js.append(f'tl.set("#{i} .pl:nth-child(2)",{{opacity:0}},{t0 + 0.31:.3f});')
    js.append(f'tl.fromTo("#{i} .pl:nth-child(2)",{{opacity:0,y:-20}},{{opacity:1,y:0,duration:0.5}},{tz:.3f});')
    t0, t1 = at_cue("IMG_1359", 104.82)
    i = clip("fullcard", t0 + 0.4, t1 - t0 - 0.3,
             '<div class="fc-in"><div class="fc-l small">Freud è uno strumento filosofico,</div>'
             '<div class="fc-l small">non una spiegazione biologica.</div><div class="fc-l tiny">E ha anche delle critiche.</div></div>', 39)
    js.append(f'tl.fromTo("#{i} .fc-l",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.5,stagger:0.5}},{t0 + 0.5:.3f});')
    js.append(f'tl.fromTo("#{i}",{{backgroundColor:"rgba(8,12,20,0)"}},{{backgroundColor:"rgba(8,12,20,0.5)",duration:0.5}},{t0 + 0.4:.3f});')
    js.append(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{t1 - 0.2:.3f});')
    # --- La società
    t0, t1 = at_cue("IMG_1361", 0.91)
    panel(t0 + 0.4, t1 - t0,
          '<div class="pi pnl-h">Consenso <em>[9]</em></div><div class="pi big-t">libero + informato</div>'
          '<div class="pi tags"><span>documenti tolti</span><span>isolamento</span><span>minacce</span></div>'
          '<div class="pi cap">→ non c&#39;è libertà</div><div class="pi note">Con una minorenne: nessun consenso possibile.</div>')
    t0, t1 = at_cue("IMG_1361", 18.0)
    steps = ["libertà", "scelta", "necessità economica", "sfruttamento", "violenza"]
    inner = '<div class="pi pnl-h">Una scala, non bianco o nero</div><div class="scale">' + "".join(
        f'<div class="pi st st{k}"><i>{k + 1}</i><b>{s}</b></div>' for k, s in enumerate(steps)) + \
        '</div><div class="pi note">Il condizionamento non è sempre economico.</div>'
    i = panel(t0 + 0.4, t1 - t0 + 0.2, inner)
    words = words_for("IMG_1361", 16.85, 46.05)
    for k, s in enumerate(steps):
        w = next((x for x in words if s.split()[0][:5].lower() in x[2].lower()), None)
        if w:
            tt = map_src("IMG_1361", w[0])
            if tt:
                js.append(f'tl.to("#{i} .st{k}",{{backgroundColor:"rgba(215,38,61,{0.15 + 0.17 * k:.2f})",duration:0.3}},{tt:.3f});')
    t0, t1 = at_cue("IMG_1362", 137.46)
    if t0 is not None:  # plano de "Stereotipi" (SO3), hoy fuera del corte por duración
        panel(t0 + 0.3, t1 - t0 + 0.3, '<div class="pi pnl-h">Stereotipi <em>[5]</em></div><div class="pi quote">“baby squillo”</div>'
              '<div class="pi cap">sposta la colpa sulle ragazze</div>')


# ------------------------------------------------------------------ lower thirds y créditos

def lower_thirds():
    a4 = shot("A4")
    lower_third(a4["body_start"] + 0.6, "Giulia Bianchi", "Inviata · Educazione civica")
    for s in SHOTS:
        for f in s["fx"]:
            if f.startswith("lt:") and s["id"].split(".")[0] == s["id"] or (f.startswith("lt:") and s["id"].endswith(".0")):
                name, role = LT[f[3:]]
                lower_third(s["body_start"] + 0.8, name, role)


CREDITS_FONTI = [
    "[1] Courtesans of the Ancient World, Historiae 4 (2007)",
    "[2] D. Ray, Social, Political & Economic Landscapes in Kautilya’s Arthashastra (World History Encyclopedia)",
    "[3] M. Boittin, The Regulation of Prostitution in China, cap. 2 (Cambridge University Press, 2024)",
    "[4] Fanpage, condanne caso Parioli",
    "[5] Fanpage, Parlano due ex baby squillo…",
    "[6] Movieplayer, polemica su Baby",
    "[7] UNODC, Global Report on Trafficking in Persons 2024",
    "[8] Ley 17.515 (Uruguay)",
    "[9] Annecchiarico, La disciplina della prostituzione in Italia (Astrid)",
    "[10] Clínica Universidad de Navarra, Eje hipotálamo-hipofiso-adrenal",
    "[11] Oram et al. (2012), PLOS Medicine",
    "[12] OMS, Condoms",
    "[13] Sapere.it, Sigmund Freud",
    "[14] Sololibri, Sigmund Freud: 5 cose da sapere",
]


def credits():
    cr = shot("CR")
    T, D = cr["start"], cr["end"] - cr["start"]
    pages = [
        (0.0, 6.0, '<div class="cr-k">un lavoro di</div><div class="cr-names">Luciano Moreno · Alessandro Vanzini · Lara Sasson</div>'
                   '<div class="cr-k">Classe IVS · 2026 · Scuola Italiana di Montevideo</div>'
                   '<div class="cr-small">Filosofia · Chimica e Biologia · Educazione civica</div>'
                   '<div class="cr-small">Ricerca, testi, regia e interpretazione: tutti e tre gli autori</div>'),
        (6.0, 6.8, '<div class="cr-k">Dichiarazione di onestà</div><div class="cr-p">I sottoscritti dichiarano di essere gli unici autori dei testi presentati in questo lavoro e di non aver commesso alcun plagio nella loro elaborazione.</div>'
                   '<div class="cr-k sp">Avvertenza</div><div class="cr-p">Storia di finzione. Personaggi e fatti inventati. Il video tratta di sfruttamento e violenza.</div>'),
        (12.8, 8.2, '<div class="cr-k">Se tu o qualcuno che conosci è in una situazione di sfruttamento</div>'
                    '<div class="help"><div><b>Italia</b><span>Numero Verde Antitratta <strong>800 290 290</strong> (gratuito)</span></div>'
                    '<div><b>Uruguay</b><span>Servizio di Attenzione a Donne in Situazione di Tratta (MIDES / INMUJERES): <strong>2400 0302</strong>, interni <strong>5506</strong> o <strong>5510</strong> — lun–ven, orario d&#39;ufficio, maggiori di 18 anni</span></div>'
                    '<div><b></b><span>Linea di Orientamento sulla Violenza di Genere: <strong>0800 4141</strong> o <strong>*4141</strong> da cellulare (gratuita e confidenziale)</span></div>'
                    '<div><b></b><span>Línea Azul (INAU), se la vittima è minorenne: <strong>0800 5050</strong> o <strong>*5050</strong> da cellulare (gratuita, anonima)</span></div></div>'),
        (21.0, D - 21.0, '<div class="cr-k">Fonti</div><div class="fonti">' + "".join(f"<div>{E(f)}</div>" for f in CREDITS_FONTI) + "</div>"),
    ]
    for a, d, inner in pages:
        i = clip("credits", T + a, d, f'<div class="cr-in">{inner}</div>', 41)
        js.append(f'tl.fromTo("#{i} .cr-in",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.8,ease:"power2.out"}},{T + a + 0.1:.3f});')
        js.append(f'tl.to("#{i} .cr-in",{{opacity:0,duration:0.6}},{T + a + d - 0.7:.3f});')
    OPEN_SUBS.append(dict(t0=T + 0.3, t1=T + D - 0.3, who="sfx", label=None, look="black", text="[musica sommessa]"))


CSS = r"""
@font-face{font-family:'Inter';src:url('assets/fonts/Inter.ttf');font-weight:100 900;}
@font-face{font-family:'Bebas';src:url('assets/fonts/BebasNeue.ttf');}
@font-face{font-family:'Cormorant';src:url('assets/fonts/CormorantGaramond.ttf');font-weight:300 700;}
@font-face{font-family:'CormorantI';src:url('assets/fonts/CormorantGaramond-Italic.ttf');font-weight:300 700;}
@font-face{font-family:'Mono';src:url('assets/fonts/JetBrainsMono.ttf');font-weight:100 800;}
@font-face{font-family:'NotoArabic';src:url('assets/fonts/NotoSansArabic.ttf');font-weight:100 900;}
@font-face{font-family:'NotoDeva';src:url('assets/fonts/NotoSansDevanagari.ttf');font-weight:100 900;}
@font-face{font-family:'NotoSC';src:url('assets/fonts/NotoSansSC-sub.ttf');}
@font-face{font-family:'NotoJP';src:url('assets/fonts/NotoSansJP-sub.ttf');}
:root{--ink:#f2f4f7;--navy:rgba(12,20,34,0.86);--navy-solid:#0c1422;--red:#d7263d;--steel:#8fa3bf;--bone:#e9e2d6;--amber:#c8893b;}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1920px;height:1080px;overflow:hidden;background:#05070a;}
#root{position:relative;width:100%;height:100%;overflow:hidden;font-family:'Inter';color:var(--ink);}
#base{position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover;}
.clip{position:absolute;inset:0;pointer-events:none;}
/* subtítulos */
.sub{display:flex;align-items:flex-end;justify-content:center;}
.sub-in{display:flex;flex-direction:column;align-items:center;gap:2px;max-width:1500px;text-align:center;}
.sub .ln{font-family:'Inter','NotoArabic','NotoDeva','NotoSC','NotoJP';font-weight:600;font-size:38px;line-height:1.22;letter-spacing:0.005em;color:#fff;
  -webkit-text-stroke:6px rgba(0,0,0,0.62);paint-order:stroke fill;text-shadow:0 2px 6px rgba(0,0,0,0.75);}
.sub .who{font-weight:700;font-size:19px;letter-spacing:0.28em;margin-bottom:4px;-webkit-text-stroke:4px rgba(0,0,0,0.6);paint-order:stroke fill;}
.sub-story{padding-bottom:20px;}
.sub-story .ln{font-size:33px;line-height:1.16;}
.sub-tv{padding-bottom:84px;}
.sub-black{padding-bottom:70px;}
.sub-sfx .ln{font-style:italic;font-weight:400;font-size:28px;opacity:0.82;letter-spacing:0.03em;}
.sub-story.sub-sfx .ln{font-size:26px;}
/* apertura */
.vw{inset:auto;}
.vw-in{position:absolute;display:block;transform-origin:50% 50%;white-space:nowrap;font-weight:700;color:#f4f1ec;
  translate:-50% -50%;letter-spacing:-0.01em;}
.redflick{background:radial-gradient(ellipse at 50% 55%,rgba(120,8,18,0.55),rgba(30,0,4,0.2) 55%,rgba(0,0,0,0) 75%);}
.ttl{display:flex;align-items:center;justify-content:center;background:radial-gradient(ellipse at 50% 50%,#0d131d 0%,#030406 70%);}
.ttl-wrap{display:flex;flex-direction:column;align-items:center;gap:26px;}
.ttl-main{font-family:'Bebas';font-size:300px;line-height:0.9;color:#e8ecf1;letter-spacing:0.08em;
  text-shadow:0 0 60px rgba(160,190,230,0.25);}
.ttl-sub{font-family:'CormorantI';font-size:46px;color:#c9d2de;letter-spacing:0.04em;}
.ttl-sweep{position:absolute;top:0;bottom:0;left:30%;width:40%;background:linear-gradient(100deg,rgba(255,255,255,0) 0%,rgba(190,215,255,0.22) 50%,rgba(255,255,255,0) 100%);mix-blend-mode:screen;}
.fadeblack{background:#000;}
.fadewhite{background:#eef3f8;}
/* interfaz DOSSIER */
.bug{position:absolute;left:72px;top:54px;display:flex;align-items:center;gap:18px;}
.bug-logo{font-family:'Bebas';font-size:52px;letter-spacing:0.14em;color:#f2f4f7;text-shadow:0 2px 10px rgba(0,0,0,0.5);}
.bug-live{display:flex;align-items:center;gap:10px;background:var(--red);color:#fff;font-weight:800;font-size:17px;letter-spacing:0.16em;padding:7px 14px 6px;}
.bug-live .dot{display:block;width:10px;height:10px;border-radius:50%;background:#fff;}
.clock{position:absolute;right:72px;top:62px;font-family:'Mono';font-weight:500;font-size:28px;color:#f2f4f7;background:rgba(12,20,34,0.7);padding:6px 14px;}
.ticker{inset:auto 0 0 0;height:54px;top:auto;display:flex;background:var(--navy-solid);border-top:1px solid rgba(143,163,191,0.35);overflow:hidden;}
.tk-label{flex:0 0 auto;background:var(--red);color:#fff;font-weight:800;font-size:19px;letter-spacing:0.14em;padding:0 22px;display:flex;align-items:center;}
.tk-track{flex:1;overflow:hidden;position:relative;}
.tk-text{position:absolute;left:30px;top:12px;white-space:nowrap;font-weight:500;font-size:24px;color:#e7ecf2;}
.lt{display:flex;align-items:flex-end;}
.lt-box{position:absolute;left:96px;bottom:212px;background:var(--navy);padding:16px 30px 18px 26px;min-width:520px;}
.lt-rule{position:absolute;left:0;top:0;width:100%;height:4px;background:var(--red);transform-origin:0 50%;}
.lt-name{font-weight:700;font-size:40px;letter-spacing:0.01em;}
.lt-role{font-weight:400;font-size:23px;color:#b9c6d8;margin-top:4px;letter-spacing:0.04em;}
.srctag .src-in{position:absolute;right:72px;top:118px;display:flex;gap:8px;}
.src{font-family:'Mono';font-size:20px;font-weight:600;color:#fff;background:rgba(12,20,34,0.78);border:1px solid rgba(143,163,191,0.5);padding:3px 9px;}
/* presentaciones */
.arrow{position:absolute;inset:0;overflow:visible;}
.arr-p{fill:none;stroke-width:4;stroke-dasharray:1;stroke-dashoffset:1;stroke-linecap:round;}
.intro-tv .arr-p{stroke:#ffffff;} .intro-tv .arr-dot{fill:var(--red);}
.intro-story .arr-p{stroke:var(--amber);} .intro-story .arr-dot{fill:var(--amber);}
.card{position:absolute;width:620px;padding:22px 28px;}
.intro-tv .card{background:var(--navy);border-top:4px solid var(--red);}
.intro-story .card{background:linear-gradient(90deg,rgba(0,0,0,0.78),rgba(0,0,0,0.45));}
.c-name{font-weight:800;font-size:50px;letter-spacing:0.01em;}
.intro-story .c-name{font-family:'Cormorant';font-weight:600;font-size:62px;color:var(--bone);}
.c-actor{font-weight:500;font-size:22px;letter-spacing:0.12em;text-transform:uppercase;color:#b9c6d8;margin-top:6px;}
.intro-story .c-actor{color:#c7b79c;}
.c-desc{font-size:27px;margin-top:12px;color:#e9edf2;}
.intro-story .c-desc{font-family:'CormorantI';font-size:34px;color:var(--bone);}
/* historia */
.recon{display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;padding:176px 0 0 120px;}
.rc-a{font-weight:600;font-size:18px;letter-spacing:0.35em;text-transform:uppercase;color:#c7b79c;}
.rc-b{font-family:'CormorantI';font-size:48px;color:var(--bone);margin-top:6px;}
.mese{display:flex;align-items:flex-end;justify-content:flex-end;padding:0 120px 176px 0;}
.mese-in{font-family:'Cormorant';font-weight:500;font-size:66px;letter-spacing:0.22em;text-transform:uppercase;color:var(--bone);text-shadow:0 2px 20px rgba(0,0,0,0.7);}
.glitch .gl-noise{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,0.18) 0 2px,rgba(0,0,0,0.35) 2px 4px);mix-blend-mode:screen;}
.glitch .gl-bars i{position:absolute;left:-5%;width:110%;display:block;background:rgba(220,230,255,0.35);mix-blend-mode:difference;}
/* infografías */
.pnl-right .pnl-in{position:absolute;right:72px;top:180px;width:640px;background:var(--navy);padding:30px 34px 34px;border-top:3px solid var(--red);}
.pnl-h{font-weight:700;font-size:21px;letter-spacing:0.16em;text-transform:uppercase;color:#b9c6d8;margin-bottom:18px;}
.pnl-h em,.cap em,.pl-src em,.pl span em{font-style:normal;font-family:'Mono';font-size:0.85em;color:#fff;}
.big{font-weight:800;font-size:110px;line-height:1;letter-spacing:-0.02em;}
.big small{font-size:56px;margin-left:4px;color:#b9c6d8;}
.big-t{font-weight:700;font-size:44px;line-height:1.15;margin-bottom:12px;}
.big-t u{text-decoration-color:var(--red);text-decoration-thickness:5px;}
.cap{font-size:27px;line-height:1.3;color:#e3e8ee;margin:6px 0 14px;}
.note{font-size:22px;color:#9fb0c6;font-style:italic;margin-top:10px;}
.quote{font-family:'CormorantI';font-size:64px;color:#fff;margin-top:8px;}
.chain{display:flex;flex-wrap:wrap;align-items:center;gap:10px;font-size:26px;margin:10px 0;}
.chain b{font-weight:600;background:rgba(143,163,191,0.16);padding:6px 12px;}
.chain i{font-style:normal;color:var(--red);font-weight:800;}
.chain.up span{font-weight:700;color:#fff;border-bottom:3px solid var(--red);padding-bottom:2px;margin-right:12px;}
.hpa{display:flex;flex-direction:column;align-items:center;gap:6px;}
.h-n{font-weight:700;font-size:28px;letter-spacing:0.06em;background:rgba(143,163,191,0.18);padding:8px 18px;width:100%;text-align:center;}
.h-c{background:rgba(215,38,61,0.35);}
.h-a{font-family:'Mono';font-size:24px;color:#b9c6d8;}
.h-fb{margin-top:12px;font-size:23px;font-style:italic;color:#9fb0c6;border-top:1px dashed rgba(143,163,191,0.5);padding-top:10px;width:100%;text-align:center;}
.pair{margin:12px 0;} .pair b{display:block;font-weight:800;font-size:34px;letter-spacing:0.06em;} .pair span{font-size:25px;color:#cbd5e1;}
.tags{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 12px;} .tags span{font-size:24px;font-weight:600;border:1px solid rgba(143,163,191,0.6);padding:6px 12px;}
.myth{font-size:26px;color:#9fb0c6;margin-top:10px;} .myth s{text-decoration-color:var(--red);text-decoration-thickness:3px;}
.paper{background:rgba(236,230,218,0.95)!important;border-top-color:#7b1e2a!important;}
.paper .pnl-h{color:#5b4f44;} .hand{font-family:'CormorantI';font-size:48px;color:#2a2018;margin:10px 0;}
.pnl-map .pnl-in{height:700px;}
.netwrap{position:relative;width:620px;height:600px;margin-left:-14px;}
.net{position:absolute;inset:0;} .net path{fill:none;stroke:rgba(215,38,61,0.75);stroke-width:2.5;stroke-dasharray:1;stroke-dashoffset:1;}
.node{position:absolute;width:250px;} .node i{position:absolute;left:-9px;top:-9px;width:18px;height:18px;border-radius:50%;background:var(--red);box-shadow:0 0 0 6px rgba(215,38,61,0.25);}
.node b{display:block;margin:14px 0 0 14px;font-weight:800;font-size:26px;letter-spacing:0.1em;}
.node span{display:block;margin-left:14px;font-size:20px;color:#cbd5e1;line-height:1.3;}
.node em{font-style:normal;font-family:'Mono';color:#fff;}
.words3{display:flex;align-items:flex-start;justify-content:center;padding-top:150px;}
.w3{display:flex;gap:26px;align-items:center;background:var(--navy);padding:18px 34px;font-weight:800;font-size:34px;letter-spacing:0.14em;}
.w3 i{font-style:normal;color:var(--red);}
.fullcard{display:flex;align-items:center;justify-content:center;}
.fc-in{display:flex;flex-direction:column;align-items:center;gap:14px;background:rgba(12,20,34,0.82);padding:44px 70px;border-top:4px solid var(--red);}
.fc-l{font-weight:800;font-size:76px;letter-spacing:-0.01em;}
.fc-l.small{font-size:52px;font-weight:700;} .fc-l.tiny{font-size:34px;font-weight:400;font-style:italic;color:#b9c6d8;}
.pillars .pl-in{position:absolute;left:0;right:0;top:118px;display:flex;justify-content:center;gap:22px;flex-wrap:wrap;}
.pl{width:420px;background:var(--navy);border:2px solid rgba(143,163,191,0.35);padding:18px 24px;}
.pl.wide{width:820px;}
.pl b{display:block;font-weight:800;font-size:40px;letter-spacing:0.08em;} .pl span{display:block;font-size:24px;color:#cbd5e1;}
.pl em{display:block;font-family:'CormorantI';font-style:normal;font-size:30px;color:#fff;margin-top:6px;}
.pl-src{width:100%;text-align:center;font-size:20px;color:#b9c6d8;}
.scale{display:flex;flex-direction:column;gap:8px;margin:6px 0 10px;}
.st{display:flex;align-items:center;gap:16px;background:rgba(143,163,191,0.1);padding:9px 14px;}
.st i{font-style:normal;font-family:'Mono';font-size:22px;color:#b9c6d8;} .st b{font-weight:700;font-size:30px;}
/* créditos */
.credits{display:flex;align-items:center;justify-content:center;}
.cr-in{display:flex;flex-direction:column;align-items:center;gap:18px;max-width:1500px;text-align:center;}
.cr-k{font-weight:600;font-size:24px;letter-spacing:0.22em;text-transform:uppercase;color:#a9b6c8;}
.cr-k.sp{margin-top:26px;}
.cr-names{font-family:'Cormorant';font-weight:600;font-size:68px;color:#f0ede7;}
.cr-small{font-size:28px;color:#d6dce4;}
.cr-p{font-size:33px;line-height:1.4;color:#eef1f4;max-width:1320px;}
.help{display:flex;flex-direction:column;gap:16px;text-align:left;max-width:1500px;margin-top:10px;}
.help div{display:flex;gap:26px;} .help b{flex:0 0 150px;font-weight:800;font-size:30px;color:#fff;}
.help span{font-size:28px;line-height:1.35;color:#e3e8ee;} .help strong{color:#fff;font-family:'Mono';font-weight:700;}
.fonti{columns:2;column-gap:60px;text-align:left;font-size:24px;line-height:1.45;color:#dfe5ec;max-width:1640px;}
.fonti div{break-inside:avoid;margin-bottom:6px;}
.smoke{mix-blend-mode:screen;}
.sm{position:absolute;display:block;width:900px;height:700px;left:620px;top:260px;border-radius:50%;
  background:radial-gradient(ellipse at 50% 50%,rgba(210,200,190,0.55),rgba(160,150,140,0.18) 40%,rgba(0,0,0,0) 70%);filter:blur(30px);}
.sm.s1{left:500px;top:340px;width:700px;} .sm.s2{left:760px;top:200px;width:800px;} .sm.s3{left:560px;top:120px;height:500px;} .sm.s4{left:820px;top:380px;}
"""


def main():
    edl_total = edl.timeline()[1]
    assert abs(edl_total - TOTAL) < 0.01, (edl_total, TOTAL)
    build_subs()
    opening()
    dossier_ui()
    lower_thirds()
    intros()
    story_cards()
    gl = glitches()
    infographics()
    place_sources()
    credits()
    # los subtítulos de apertura y créditos también van en pantalla, sin solaparse
    OPEN_SUBS.sort(key=lambda x: x["t0"])
    for x, y in zip(OPEN_SUBS, OPEN_SUBS[1:]):
        if x["t1"] > y["t0"] - 0.04:
            x["t1"] = y["t0"] - 0.04
    SUBS.extend(x for x in OPEN_SUBS if x["t1"] - x["t0"] > 0.2)
    SUBS.sort(key=lambda x: x["t0"])
    OPEN_SUBS.clear()
    place_subs()
    write_srt()
    (HF / "assets").mkdir(exist_ok=True)
    body = "\n      ".join(els)
    script = "\n      ".join(js)
    doc = f"""<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>La rete</title>
    <script src="assets/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1920" data-height="1080" data-fps="30">
      <video id="base" src="assets/base.mp4" muted playsinline data-start="0" data-duration="{TOTAL:.3f}" data-track-index="0"></video>
      <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="1" data-volume="1"></audio>
      {body}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      function clockSpan(sel, t0, d) {{
        const el = document.querySelector(sel);
        const o = {{ v: 0 }};
        tl.fromTo(o, {{ v: 0 }}, {{ v: d, duration: d, ease: "none", onUpdate: () => {{
          const m = 21 * 60 + 4 + Math.floor((t0 + o.v) / 60);
          el.textContent = String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
        }} }}, t0);
      }}
      {script}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    (HF / "index.html").write_text(doc, encoding="utf-8")
    print("elementos:", len(els), "subtítulos:", len(SUBS) + len(OPEN_SUBS), "glitches:", len(gl), "total", TOTAL)


if __name__ == "__main__":
    main()
