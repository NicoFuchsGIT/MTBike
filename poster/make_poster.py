"""Poster (IMRAD, Vorlage STPAA, A3 hoch -> Druck A1) als editierbare SVG erzeugen.

Aufruf (aus dem Repo-Root):  python poster/make_poster.py
Ausgabe:  poster/Poster_MTB_Bremsen.svg   (Text = echter SVG-Text, Abbildungen = Vektor-Gruppen)
          poster/fig/Abb*.svg            (Poster-Abbildungen einzeln)

Text, Zahlen und Tabelle kommen direkt aus der Auswertung (analysis/run_analysis.py),
die Abbildungen sind Poster-Varianten von Fig 2-4 (gleiche Daten, Größe/Schrift fürs Poster);
figures/ wird nicht verändert.
"""
import base64
import io
import os
import re
import sys

import numpy as np
from PIL import ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis"))
from run_analysis import POS, LABEL, COL, INK, INK2, GRID, run_all, table, statistics  # noqa: E402
from brake_pipeline import V0  # noqa: E402

OUT_SVG = os.path.join(HERE, "Poster_MTB_Bremsen.svg")
OUT_FIG = os.path.join(HERE, "fig")
BG_PNG = os.path.join(HERE, "assets", "Vorlage_Hintergrund.png")   # Logo + Fußzeile aus der Vorlage

# ---------------------------------------------------------------- Seite (aus der Word-Vorlage)
W, H = 297.0, 420.0                    # mm, A3 hoch (Vorlage), Druck skaliert auf A1
ML, MR, MT, MB = 20.0, 20.0, 52.5, 22.5
GAP = 12.5                              # Spaltenabstand
COLW = (W - ML - MR - GAP) / 2
PT = 25.4 / 72                          # 1 pt in mm
BLUE, GREY, TXT = "#00659C", "#626B71", "#000000"
FONT = "Arial, 'Liberation Sans', Helvetica, sans-serif"
FS = {"h1": 34, "sub": 20, "team": 18, "course": 16, "h2": 16, "body": 12, "cap": 10, "ref": 10}

AUTHORS = "Kilian Chalmers, Nico Fuchs, Vincent Pflug, Luisa Przibylla"
COURSE = "Sportgerätepraxis: Theorie, Anwendung, Analyse – BHF 5"
TITLE = "Körperhaltung beim Bremsen am E-MTB"
SUBTITLE = "Smartphone-Messung der Verzögerung des Körperschwerpunkts in drei Sitzpositionen"

_FDIR = "/usr/share/fonts/truetype/liberation/"     # metrisch identisch zu Arial
_FFILE = {"r": "LiberationSans-Regular.ttf", "b": "LiberationSans-Bold.ttf",
          "i": "LiberationSans-Italic.ttf", "bi": "LiberationSans-BoldItalic.ttf"}
_FCACHE = {}


def text_w(s, pt, st="r"):
    """Textbreite in mm (Arial-Metrik)."""
    f = _FCACHE.setdefault(st, ImageFont.truetype(_FDIR + _FFILE[st], 200))
    return f.getlength(s) / 200 * pt * PT


def de(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")


NB = "\u00a0"


def nbsp(md):
    """Geschützte Leerzeichen: kein Umbruch in „p = 0,03“, „20 km/h“, „Abb. 1“ usw."""
    md = re.sub(r"(?<=\S) ([=≈<>±]) (?=\S)", NB + r"\1" + NB, md)
    md = re.sub(r"(?<=[≈<>]) (?=[\d−])", NB, md)
    md = re.sub(r"(?<=\d) (?=(m/s²|km/h|Hz|s|g|m|%|Versuche)\b)", NB, md)
    md = re.sub(r"\b(Abb|Tab|Gl|v)\. (?=[\da])", r"\1." + NB, md)
    return md


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- Poster-Abbildungen (Vektor)
def poster_style():
    plt.rcParams.update({
        "svg.fonttype": "none", "svg.hashsalt": "mtbike",
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
        "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8.5,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
        "ytick.color": INK2, "text.color": INK, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.5, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "none", "axes.facecolor": "none", "savefig.facecolor": "none",
    })


_comma = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))


def mm(w, h):
    return (w / 25.4, h / 25.4)


def save(fig, name, xcomma=True):
    os.makedirs(OUT_FIG, exist_ok=True)
    for ax in fig.axes:
        ax.yaxis.set_major_formatter(_comma)
        if xcomma:
            ax.xaxis.set_major_formatter(_comma)
    p = os.path.join(OUT_FIG, name)
    fig.savefig(p)
    plt.close(fig)
    return p


def abb1(trials, w, h):
    """Beispielversuch: a_x mit Bremsfenster + Geschwindigkeit (wie Fig 2)."""
    r = next(t for t in trials if t["name"] == "Neutral Trial 15-18-12")
    t = r["t"] - r["t_start"]
    m = (t > -3) & (t < 2.5)
    fig, ax = plt.subplots(2, 1, figsize=mm(w, h), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax[0].axvspan(0, r["dur"], color="#f0efec", zorder=0, lw=0)
    ax[0].plot(t[m], r["a_x"][m], color=COL["Neutral"], lw=1.4)
    ax[0].axhline(0, color=INK2, lw=0.6)
    ax[0].axhline(-r["mean"], color=INK, lw=0.8, ls="--")
    ax[0].annotate(f"ā = {de(r['mean'], 1)} m/s²", (r["dur"] / 2, -r["mean"]), xytext=(0, 4),
                   textcoords="offset points", ha="center")
    ax[0].text(-2.9, 2.4, "Treten / Rollen", color=INK2)
    ax[0].text(0.05, 2.4, "Bremsphase", color=INK)
    ax[0].set_ylabel("a$_x$ KSP [m/s²]")
    ax[0].set_ylim(-11, 4)
    ax[1].plot(t[m], r["v"][m] * 3.6, color=INK, lw=1.4)
    ax[1].axhline(V0 * 3.6, color=INK2, lw=0.8, ls=":")
    ax[1].text(-2.9, V0 * 3.6 + 1.5, "Soll 20 km/h", color=INK2)
    ax[1].axhline(0, color=INK2, lw=0.6)
    ax[1].set_ylim(-3, 30)
    ax[1].set_ylabel("v [km/h]")
    ax[1].set_xlabel("Zeit relativ zum Bremsbeginn [s]")
    fig.align_ylabels(ax)
    fig.tight_layout(pad=0.3, h_pad=0.6)
    return save(fig, "Abb1_Methode.svg")


def abb2(trials, w, h):
    """Mittlere Bremskurve ± SD je Position (wie Fig 3)."""
    grid = np.arange(-0.5, 2.0, 0.005)
    fig, ax = plt.subplots(figsize=mm(w, h))
    for p in POS:
        M = []
        for r in (x for x in trials if x["position"] == p):
            y = np.interp(grid, r["t"] - r["t_start"], r["a_x"], left=np.nan, right=np.nan)
            y[grid > r["dur"] + 0.05] = np.nan
            M.append(y)
        M = np.array(M)
        ok = np.sum(~np.isnan(M), 0) == len(M)
        with np.errstate(all="ignore"):
            mu, sd = np.nanmean(M, 0), np.nanstd(M, 0, ddof=1)
        ax.fill_between(grid[ok], (mu - sd)[ok], (mu + sd)[ok], color=COL[p], alpha=0.15, lw=0)
        ax.plot(grid[ok], mu[ok], color=COL[p], lw=1.6, label=LABEL[p])
    ax.axhline(0, color=INK2, lw=0.6)
    ax.axvline(0, color=INK2, lw=0.6, ls=":")
    ax.set_xlim(-0.5, 1.2)
    ax.set_ylim(-13.5, 1.5)
    ax.set_xlabel("Zeit relativ zum Bremsbeginn [s]")
    ax.set_ylabel("a$_x$ KSP [m/s²]")
    ax.legend(loc="lower center", ncol=3, frameon=False, handlelength=1.4, columnspacing=1.2,
              borderaxespad=0.1)
    fig.tight_layout(pad=0.3)
    return save(fig, "Abb2_Bremskurven.svg")


def abb3(df, w, h):
    """Einzelwerte + MW ± SD (wie Fig 4, ohne Spitzenwert -> Tab. 1); v0 in km/h wie in Tab. 1."""
    keys = [("mean", "Mittlere Verzögerung ā [m/s²]", 1),
            ("v0", "Anfangsgeschwindigkeit v$_0$ [km/h]", 3.6)]
    fig, axs = plt.subplots(1, len(keys), figsize=mm(w, h))
    rng = np.random.default_rng(1)
    for ax, (k, lab, f) in zip(axs, keys):
        for i, p in enumerate(POS):
            v = df.loc[df.Position == p, k].to_numpy() * f
            ax.scatter(i + rng.uniform(-0.12, 0.12, len(v)), v, s=16, color=COL[p], alpha=0.8,
                       edgecolor="white", linewidth=0.5, zorder=3)
            ax.errorbar(i + 0.28, v.mean(), yerr=v.std(ddof=1), fmt="o", color=INK, ms=3.5,
                        capsize=3, lw=1.0, capthick=1.0, zorder=4)
        ax.set_xticks(range(3), ["vorn", "neutral", "hinten"])
        ax.set_xlim(-0.5, 2.6)
        ax.set_title(lab)
        ax.grid(axis="x", visible=False)
        if k == "v0":
            ax.axhline(V0 * 3.6, color=INK2, lw=0.8, ls=":")
            ax.text(-0.45, V0 * 3.6 - 0.2, "Soll 20 km/h", color=INK2, va="top", fontsize=8)
    fig.tight_layout(pad=0.3, w_pad=2.0)
    return save(fig, "Abb3_Vergleich.svg", xcomma=False)


def inline_svg(path, x, y, w, h, pref):
    """Matplotlib-SVG als verschachteltes <svg> (Vektor, Text editierbar) einbetten."""
    s = open(path, encoding="utf-8").read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    body = s[s.index(">", s.index("<svg")) + 1: s.rindex("</svg>")]
    body = re.sub(r"<metadata>.*?</metadata>", "", body, flags=re.S)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.S)
    body = re.sub(r'id="([^"]+)"', lambda m: f'id="{pref}{m.group(1)}"', body)
    body = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{pref}{m.group(1)})", body)
    body = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{pref}{m.group(1)}"', body)
    body = body.replace('stroke-linecap="butt"', 'stroke-linecap="butt" stroke-linejoin="round"')
    return (f'<svg x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" viewBox="{vb}" '
            f'overflow="visible">{body}</svg>')


# ---------------------------------------------------------------- Textsatz
def runs(md):
    """Mini-Markup: **fett**, *kursiv*, _{tief}, ^{hoch} -> [(text, stil, shift)]."""
    out, st = [], {"b": False, "i": False}
    for tok in re.split(r"(\*\*|\*|_\{[^}]*\}|\^\{[^}]*\})", md):
        if tok == "**":
            st["b"] = not st["b"]
        elif tok == "*":
            st["i"] = not st["i"]
        elif tok.startswith("_{") or tok.startswith("^{"):
            out.append((tok[2:-1], ("b" if st["b"] else "") + ("i" if st["i"] else "") or "r",
                        "sub" if tok[0] == "_" else "super"))
        elif tok:
            out.append((tok, ("b" if st["b"] else "") + ("i" if st["i"] else "") or "r", None))
    return out


def wrap(md, width, pt):
    """Zeilenumbruch nach echter Schriftbreite. Liefert Liste von Zeilen = Liste von Runs."""
    words = []                      # Wort = Liste von Runs, zwischen Wörtern Leerzeichen
    cur = []
    for txt, st, sh in runs(md):
        parts = txt.split(" ") if sh is None else [txt]
        for k, p in enumerate(parts):
            if k > 0:
                words.append(cur)
                cur = []
            if p:
                cur.append((p, st, sh))
    words.append(cur)
    words = [w for w in words if w]

    def wlen(wd):
        return sum(text_w(t, pt * (0.7 if sh else 1), st) for t, st, sh in wd)

    lines, line, lw = [], [], 0.0
    sp = text_w(" ", pt)
    for wd in words:
        L = wlen(wd)
        if line and lw + sp + L > width:
            lines.append(line)
            line, lw = [], 0.0
        line.append(wd)
        lw += (sp if len(line) > 1 else 0) + L
    if line:
        lines.append(line)
    return lines


def tspans(line, pt):
    out = []
    for k, wd in enumerate(line):
        for j, (t, st, sh) in enumerate(wd):
            t = (" " if k > 0 and j == 0 else "") + t
            a = []
            if "b" in st:
                a.append('font-weight="bold"')
            if "i" in st:
                a.append('font-style="italic"')
            if sh:
                a.append(f'baseline-shift="{sh}" font-size="{pt * 0.7 * PT:.3f}"')
            out.append(f"<tspan {' '.join(a)}>{esc(t)}</tspan>" if a else esc(t))
    return "".join(out)


class Flow:
    """Setzt Blöcke untereinander in eine Spalte (x, Breite) ab y."""

    def __init__(self, x, y, w, name):
        self.x, self.y, self.w, self.name, self.svg = x, y, w, name, []

    def gap(self, d):
        self.y += d

    def heading(self, s, pt=FS["h2"]):
        self.y += 2.0 + pt * PT
        self.svg.append(f'<text x="{self.x:.2f}" y="{self.y:.2f}" font-size="{pt * PT:.3f}" '
                        f'fill="{BLUE}">{esc(s)}</text>')
        self.y += 2.6

    def para(self, md, pt=FS["body"], indent=0.0, bullet=None, lead=1.22, color=TXT, after=1.6):
        lh = pt * PT * lead
        lines = wrap(nbsp(md), self.w - indent, pt)
        y0 = self.y + pt * PT * 0.95
        g = [f'<text font-size="{pt * PT:.3f}" fill="{color}">']
        for k, ln in enumerate(lines):
            g.append(f'<tspan x="{self.x + indent:.2f}" y="{y0 + k * lh:.2f}">{tspans(ln, pt)}</tspan>')
        g.append("</text>")
        if bullet:
            g.append(f'<text x="{self.x + 0.6:.2f}" y="{y0:.2f}" font-size="{pt * PT:.3f}" '
                     f'fill="{BLUE}">{bullet}</text>')
        self.svg.append("".join(g))
        self.y += (len(lines) - 1) * lh + pt * PT * 1.25 + after

    def bullets(self, items, pt=FS["body"]):
        for it in items:
            self.para(it, pt=pt, indent=4.2, bullet="•", after=0.7)
        self.y += 0.9

    def figure(self, path, h, cap, pref, w=None):
        w = w or self.w
        self.svg.append(f'<g id="{pref}">' + inline_svg(path, self.x, self.y, w, h, pref) + "</g>")
        self.y += h + 1.2
        self.para(cap, pt=FS["cap"], lead=1.18, after=2.0)

    def raw(self, s, h):
        self.svg.append(s)
        self.y += h


def equation(x, y, w, pt=FS["body"]):
    """Gl. (1): ā = −1/T_B · ∫ a_x(t) dt über das Bremsfenster."""
    f = pt * PT
    cx = x + w / 2 - 22
    s = [f'<g id="gleichung1" font-size="{f:.3f}">',
         f'<text x="{cx:.2f}" y="{y + 6.2:.2f}">ā = −</text>',
         f'<text x="{cx + 12.6:.2f}" y="{y + 3.4:.2f}" text-anchor="middle">1</text>',
         f'<line x1="{cx + 10.4:.2f}" y1="{y + 5.0:.2f}" x2="{cx + 15.4:.2f}" y2="{y + 5.0:.2f}" '
         f'stroke="{TXT}" stroke-width="0.25"/>',
         f'<text x="{cx + 12.9:.2f}" y="{y + 9.2:.2f}" text-anchor="middle">T<tspan baseline-shift="sub" '
         f'font-size="{f * 0.7:.3f}">B</tspan></text>',
         f'<text x="{cx + 16.4:.2f}" y="{y + 7.4:.2f}" font-size="{f * 1.9:.3f}">∫</text>',
         f'<text x="{cx + 20.4:.2f}" y="{y + 1.3:.2f}" font-size="{f * 0.62:.3f}">t<tspan '
         f'baseline-shift="sub" font-size="{f * 0.45:.3f}">B</tspan> + T<tspan baseline-shift="sub" '
         f'font-size="{f * 0.45:.3f}">B</tspan></text>',
         f'<text x="{cx + 19.4:.2f}" y="{y + 10.3:.2f}" font-size="{f * 0.62:.3f}">t<tspan '
         f'baseline-shift="sub" font-size="{f * 0.45:.3f}">B</tspan></text>',
         f'<text x="{cx + 24.2:.2f}" y="{y + 6.2:.2f}">a<tspan baseline-shift="sub" font-size="{f * 0.7:.3f}">x'
         f'</tspan>(t) dt</text>',
         f'<text x="{x + w:.2f}" y="{y + 6.2:.2f}" text-anchor="end">(1)</text>',
         "</g>"]
    return "".join(s)


def table_svg(x, y, w, rows, head):
    """Tab. 1 als SVG-Text mit Linien (Kopf- und Fußlinie wie im Laborbericht)."""
    pt = FS["cap"] + 0.5
    f = pt * PT
    c0 = (max(text_w(r[0].replace("_{0}", "0"), pt) for r in rows) + 2.5) / w
    cw = [c0] + [(1 - c0 - 0.10) / 3] * 3 + [0.10]
    xs = np.cumsum([0] + cw[:-1]) * w + x
    rh = 6.0
    s = [f'<g id="tabelle1" font-size="{f:.3f}">',
         f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{x + w:.2f}" y2="{y:.2f}" stroke="{TXT}" stroke-width="0.35"/>']
    for k, cell in enumerate(head):
        anc, xx = ("start", xs[k]) if k == 0 else ("middle", xs[k] + cw[k] * w / 2)
        s.append(f'<text x="{xx:.2f}" y="{y + 4.2:.2f}" text-anchor="{anc}" font-weight="bold">'
                 f'{tspans(wrap(cell, 999, pt)[0], pt)}</text>')
    s.append(f'<line x1="{x:.2f}" y1="{y + rh:.2f}" x2="{x + w:.2f}" y2="{y + rh:.2f}" stroke="{TXT}" '
             f'stroke-width="0.2"/>')
    for i, row in enumerate(rows):
        yy = y + rh * (i + 1)
        if i % 2 == 0:
            s.append(f'<rect x="{x:.2f}" y="{yy:.2f}" width="{w:.2f}" height="{rh:.2f}" fill="#eef4f8"/>')
        for k, cell in enumerate(row):
            anc, xx = ("start", xs[k] + 0.8) if k == 0 else ("middle", xs[k] + cw[k] * w / 2)
            s.append(f'<text x="{xx:.2f}" y="{yy + 4.2:.2f}" text-anchor="{anc}">'
                     f'{tspans(wrap(cell, 999, pt)[0], pt)}</text>')
    yb = y + rh * (len(rows) + 1)
    s.append(f'<line x1="{x:.2f}" y1="{yb:.2f}" x2="{x + w:.2f}" y2="{yb:.2f}" stroke="{TXT}" '
             f'stroke-width="0.35"/></g>')
    return "".join(s), yb - y


# ---------------------------------------------------------------- Inhalt
def numbers(df, summ):
    g = {p: df[df.Position == p] for p in POS}
    m = {p: g[p]["mean"].mean() for p in POS}
    pv = {}
    for _, r in summ.iterrows():
        mt = re.search(r"p([<=])(\d\.\d+)", r["Test"].replace(" ", ""))
        pv[r["Kennwert"]] = ("< " if mt.group(1) == "<" else "") + mt.group(2).replace(".", ",")
    return g, m, pv


def build():
    trials = run_all()
    df = table(trials)
    summ, txt = statistics(df)
    g, m, pv = numbers(df, summ)
    kw = re.search(r"Kruskal-Wallis H=([\d.]+) p=([\d.]+)", txt.split("== Spitzen")[0])
    ph = re.search(r"Vorne-Neutral: Mann-Whitney p_Bonf=([\d.]+), Cohen's d=(-?[\d.]+)", txt)
    eta_h = re.search(r"η²_H=([\d.]+)", summ.iloc[0]["Test"]).group(1)
    r_v0 = df.v0.corr(df["mean"])
    r_dist = df.v0.corr(df.dist)
    gmin, gmax = min(m.values()) / 9.81, max(m.values()) / 9.81
    best = max(m, key=m.get)
    assert best == "Neutral", "Text unten geht von neutral = größte Verzögerung aus"
    diff = m["Neutral"] - m["Vorne"]

    poster_style()
    H1, H2, H3 = 61, 50, 44               # Abbildungshöhen [mm] bei Spaltenbreite
    f1 = abb1(trials, COLW, H1)
    f2 = abb2(trials, COLW, H2)
    f3 = abb3(df, COLW, H3)

    # ---- Kopf
    y = MT + FS["h1"] * PT * 0.8
    tpt = FS["h1"]
    while text_w(TITLE, tpt) > W - ML - MR:
        tpt -= 1
    head = [f'<text x="{W / 2:.2f}" y="{y:.2f}" text-anchor="middle" font-size="{tpt * PT:.3f}" '
            f'fill="{BLUE}">{esc(TITLE)}</text>']
    y += FS["sub"] * PT * 1.35
    spt = FS["sub"]
    while text_w(SUBTITLE, spt) > W - ML - MR:
        spt -= 0.5
    head.append(f'<text x="{W / 2:.2f}" y="{y:.2f}" text-anchor="middle" font-size="{spt * PT:.3f}" '
                f'fill="{BLUE}">{esc(SUBTITLE)}</text>')
    y += FS["team"] * PT * 1.55
    head.append(f'<text x="{W / 2:.2f}" y="{y:.2f}" text-anchor="middle" font-size="{FS["team"] * PT:.3f}" '
                f'fill="{GREY}">{esc(AUTHORS)}</text>')
    y += FS["course"] * PT * 1.45
    head.append(f'<text x="{W / 2:.2f}" y="{y:.2f}" text-anchor="middle" font-size="{FS["course"] * PT:.3f}" '
                f'fill="{GREY}">{esc(COURSE)}</text>')
    top = y + 6.0

    # ---- Inhalt als Blöcke; jeder Block = Funktion(Flow). Überschrift bleibt beim ersten Absatz.
    rows = []
    spec = [("mean", "Mittl. Verzögerung ā [m/s²]", 1, 2, "Mittlere Verzögerung [m/s²]"),
            ("peak", "Spitzenverzögerung [m/s²]", 1, 2, "Spitzenverzögerung Rumpf [m/s²]"),
            ("v0", "Anfangsgeschw. v_{0} [km/h]", 3.6, 1, "Anfangsgeschw. (∫a dt bis Stillstand) [m/s]"),
            ("dist", "Bremsweg [m]", 1, 2, "Bremsweg (∫v dt) [m]")]
    for k, lab, f, nd, key in spec:
        rows.append([lab] + [f"{de(g[p][k].mean() * f, nd)} ± {de(g[p][k].std(ddof=1) * f, nd)}"
                             for p in POS] + [pv[key]])

    def tab(F):
        F.para("**Tab. 1:** Kennwerte (MW ± SD, n = 10 je Position) und p-Wert des "
               "Gruppenvergleichs (ANOVA bzw. Kruskal-Wallis).", pt=FS["cap"], lead=1.18, after=1.2)
        ts, th = table_svg(F.x, F.y, F.w, rows, ["Kennwert", "vorn", "neutral", "hinten", "p"])
        F.raw(ts, th + 3.5)

    refs = [
        "Staacks, S., Hütz, S., Heinke, H., & Stampfer, C. (2018). Advanced tools for "
        "smartphone-based experiments: phyphox. *Physics Education, 53*(4), 045009. "
        "https://doi.org/10.1088/1361-6552/aac05e",
        "Wilson, D. G., & Papadopoulos, J. (2004). *Bicycling science* (3rd ed.). MIT Press.",
        "Winter, D. A. (2009). *Biomechanics and motor control of human movement* (4th ed.). Wiley.",
    ]

    S = {}   # Abschnitt -> Blöcke
    S["Einleitung"] = [
        lambda F: (F.heading("Einleitung"), F.para(
            "Beim Bremsen verlagert sich die Last auf das Vorderrad. Die erreichbare Verzögerung "
            "eines Fahrrads ist deshalb meist nicht durch die Reifenhaftung, sondern durch das "
            "Überschlagen nach vorn auf rund 0,5–0,6 g begrenzt (Wilson & Papadopoulos, 2004). "
            "Die Körperhaltung verschiebt den Körperschwerpunkt (KSP) und damit diese Grenze. "
            "Smartphone-Sensoren mit phyphox ermöglichen solche Messungen im Feld "
            "(Staacks et al., 2018).")),
        lambda F: F.para("**Fragestellung:** Bei welcher Sitzposition – nach vorn gelehnt, neutral "
                         "oder nach hinten gelehnt – ist die mittlere Verzögerung des KSP am größten?"),
    ]
    S["Methoden"] = [
        lambda F: (F.heading("Methoden"), F.para(
            f"Ein Fahrer bremste ein E-MTB aus 20 km/h (Soll) bis zum Stillstand, je "
            f"10 Versuche pro Position (n = {len(df)}). Ein Smartphone am Bauch (nahe KSP) "
            "zeichnete mit phyphox Beschleunigung und Drehrate auf. Auswertung in Python:")),
        lambda F: F.bullets([
            "Butterworth-Tiefpass 4. Ordnung ohne Phasenverschiebung, 5 Hz (Acc) bzw. 10 Hz "
            "(Gyro) (Winter, 2009)",
            "Gyro-Integration rückwärts ab Stillstand → Lage im Raum; Schwerkraft abziehen, "
            "Fahrtrichtung per Hauptkomponente → Längsbeschleunigung a_{x} (Abb. 1)",
            "Bremsfenster a_{x} < −1 m/s²; Kennwerte: mittlere Verzögerung ā (Gl. 1), "
            "Spitzenverzögerung, v_{0} = −∫a_{x} dt",
            "Statistik: ANOVA bzw. Kruskal-Wallis, post hoc Tukey bzw. Mann-Whitney "
            "(Bonferroni), α = 0,05",
        ]),
        lambda F: (F.raw(equation(F.x, F.y, F.w), 12.5), F.gap(2.0)),
        lambda F: F.figure(f1, H1, "**Abb. 1:** Beispielversuch (neutral). Oben: Längsbeschleunigung "
                           "a_{x} des KSP mit Bremsphase (grau) und mittlerer Verzögerung ā; unten: "
                           "daraus integrierte Geschwindigkeit.", "abb1"),
    ]
    S["Ergebnisse"] = [
        lambda F: (F.heading("Ergebnisse"), F.para(
            f"Alle {len(df)} Versuche wurden automatisch ausgewertet. Die Verzögerung baut sich in "
            "≈ 0,2 s auf und erreicht Spitzen von 8–10 m/s² (Abb. 2). Die mittlere Verzögerung "
            f"war in neutraler Position am größten (Tab. 1, Abb. 3; Kruskal-Wallis "
            f"p = {de(float(kw.group(2)), 3)}, η²_{{H}} = {de(float(eta_h))}). Paarweise blieb der "
            f"Unterschied nach Bonferroni-Korrektur knapp nicht signifikant (neutral vs. vorn "
            f"p = {de(float(ph.group(1)), 3)}, d = {de(abs(float(ph.group(2))))}).")),
        lambda F: F.figure(f2, H2, "**Abb. 2:** Mittlere Längsbeschleunigung ± SD je Position, "
                           "ausgerichtet auf den Bremsbeginn; dargestellt, solange alle 10 Versuche "
                           "noch bremsen.", "abb2"),
        tab,
        lambda F: F.figure(f3, H3, "**Abb. 3:** Einzelversuche (Punkte) und MW ± SD (schwarz) je "
                           "Position: mittlere Verzögerung ā und Anfangsgeschwindigkeit v_{0} "
                           "(Störgröße, Soll 20 km/h).", "abb3"),
    ]
    S["Diskussion"] = [
        lambda F: (F.heading("Diskussion"), F.para(
            f"Mit ā = {de(gmin)}–{de(gmax)} g liegen alle Positionen am unteren Rand der "
            "Überschlaggrenze und klar unter der Haftgrenze der Reifen (μ ≈ 0,7–0,8); begrenzend "
            "war vermutlich das Überschlagrisiko. Neutral erreichte im Mittel "
            f"{de(diff)} m/s² ({diff / m['Vorne'] * 100:.0f} %) mehr als vorn – ein großer Effekt, "
            "aber ohne signifikanten Paarvergleich. Der längere Bremsweg „vorn“ folgt v. a. aus "
            f"der höheren Anfangsgeschwindigkeit (r = {de(r_dist)}), ā hängt dagegen kaum von "
            f"v_{{0}} ab (r = {de(r_v0)}).")),
        lambda F: F.para("**Limitationen:** ein Fahrer, geblockte Reihenfolge (Übungseffekt "
                         "möglich), Smartphone misst den Rumpf statt exakt den KSP, vereinzelte "
                         "Stoppies nicht ausschließbar."),
        lambda F: F.para("**Fazit:** Neutrales Sitzen liefert tendenziell die größte Verzögerung, "
                         "starkes Vor- oder Zurücklehnen brachte keinen Vorteil. Randomisierte "
                         "Messungen mit mehreren Fahrer:innen sollten dies absichern."),
    ]
    S["Literatur"] = [
        lambda F: (F.heading("Literaturverzeichnis", pt=14),
                   [F.para(r, pt=FS["ref"], lead=1.15, after=1.0) for r in refs]),
    ]

    def height(blk):
        t = Flow(0, 0, COLW, "mess")
        blk(t)
        return t.y

    limit = H - MB - 6.0                  # Abstand zur Fußzeile der Vorlage
    cols = [Flow(ML, top, COLW, "links"), Flow(ML + COLW + GAP, top, COLW, "rechts")]
    ci, groups = 0, []
    for sec, blks in S.items():
        for j, blk in enumerate(blks):
            h = height(blk)
            if cols[ci].y + h > limit + 0.01 and ci == 0:
                ci = 1
            F = cols[ci]
            n0 = len(F.svg)
            blk(F)
            groups.append((sec, ci, F.svg[n0:]))
    print(f"Spalten: links bis {cols[0].y:.1f}, rechts bis {cols[1].y:.1f} mm (Grenze {limit:.1f} mm)")
    if cols[1].y > limit:
        print(f"WARNUNG: rechte Spalte {cols[1].y - limit:.1f} mm zu lang")
    sections = {}
    for sec, ci, parts in groups:
        sections.setdefault(sec, []).extend(parts)

    # ---- SVG zusammensetzen
    bg = ""
    if os.path.exists(BG_PNG):
        b64 = base64.b64encode(open(BG_PNG, "rb").read()).decode()
        bg = (f'<image x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none" '
              f'xlink:href="data:image/png;base64,{b64}"/>')

    def layer(i, name, content, lock=False):
        return (f'<g id="{i}" inkscape:groupmode="layer" inkscape:label="{name}"'
                f'{" sodipodi:insensitive=\"true\"" if lock else ""}>{content}</g>')

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
           f'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" '
           f'width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f"<title>{esc(TITLE)}</title>",
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           layer("vorlage", "Vorlage (Logo, Fußzeile)", bg, lock=True),
           layer("kopf", "Titel und Autor:innen", "".join(head)),
           *[layer(f"sec_{k.lower()}", k, "".join(v)) for k, v in sections.items()],
           "</svg>"]
    with open(OUT_SVG, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("geschrieben:", os.path.relpath(OUT_SVG, ROOT))


if __name__ == "__main__":
    build()
