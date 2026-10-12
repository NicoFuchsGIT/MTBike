"""Zusatzabbildungen (ergänzen Fig 2-4, ersetzen keine davon).

Aufruf (aus dem Repo-Root):  python analysis/extra_figures.py
Ausgabe:  figures/Fig5_Raincloud_Schaetzung.png  (ā: Verteilung + Differenzen mit Welch-KI)
          figures/Fig6_Heatmap_Trials.png        (alle 30 Trials, nach Aufnahmezeit)
          figures/Fig7_Phasenportraet.png         (Verzögerung über Geschwindigkeit)
          figures/Fig8_gg_Diagramm.png            (Längs-/Querbeschl. mit physikalischen Grenzen)
          figures/Fig9_Rumpf_Animation.gif        (Rumpfneigung + Verzögerung, Mittel je Position)
"""
import os
import sys
import warnings

import numpy as np
from scipy.stats import gaussian_kde, t as t_dist
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brake_pipeline import G  # noqa: E402
from run_analysis import POS, LABEL, COL, INK, INK2, GRID, OUT_FIG, STOPPIE, style, run_all, table  # noqa: E402

SHORT = {"Vorne": "vorn", "Neutral": "neutral", "Hinten": "hinten"}
# Sequentielle Rampe (ein Farbton, hell -> dunkel) aus der Referenzpalette
SEQ = LinearSegmentedColormap.from_list("seq", ["#f7f9fc", "#cde2fb", "#86b6ef", "#3987e5",
                                                "#256abf", "#184f95", "#0d366b"])
# Physikalische Referenzgrenzen (Schätzwerte, siehe README Realismus-Check)
PITCH_LIM = (0.55, 0.65)   # g, Überschlaggrenze sitzend ≈ g·b/h
MU_LIM = (0.70, 0.80)      # g, Reifenhaftung trocken


def clock(r):
    """Aufnahmezeit aus dem Ordnernamen 'Position Trial HH-MM-SS' in Sekunden."""
    h, m, s = map(int, r["name"].split()[-1].split("-"))
    return 3600 * h + 60 * m + s


def on_grid(r, key, grid):
    return np.interp(grid, r["t"] - r["t_start"], r[key], left=np.nan, right=np.nan)


# --------------------------------------------------------------------------- Fig 5
def fig_raincloud(df):
    """Raincloud (Dichte + Box + Einzelwerte) und Schätzplot der Mittelwertsdifferenz
    zu 'Vorne' mit 95-%-KI nach Welch (unabhängige Gruppen). Ein Perzentil-Bootstrap
    wäre bei n = 10 systematisch zu schmal."""
    rng = np.random.default_rng(7)
    g = {p: df.loc[df.Position == p, "mean"].to_numpy() for p in POS}
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.6, 1]})
    lo, hi = min(map(min, g.values())) - 0.6, max(map(max, g.values())) + 0.6
    yy = np.linspace(lo, hi, 300)
    for i, p in enumerate(POS):
        v = g[p]
        dens = gaussian_kde(v)(yy)
        dens = 0.38 * dens / dens.max()
        k = dens > 0.01 * dens.max()   # Ausläufer abschneiden
        ax.fill_betweenx(yy[k], i - 0.08, i - 0.08 - dens[k], color=COL[p], alpha=0.35, lw=0)
        ax.plot(i - 0.08 - dens[k], yy[k], color=COL[p], lw=1.5)
        q1, med, q3 = np.percentile(v, [25, 50, 75])
        ax.add_patch(plt.Rectangle((i - 0.05, q1), 0.1, q3 - q1, fc="white", ec=INK2, lw=1.2, zorder=3))
        ax.plot([i - 0.05, i + 0.05], [med, med], color=INK, lw=2, zorder=4)
        ax.vlines(i, v.min(), q1, color=INK2, lw=1.2, zorder=2)
        ax.vlines(i, q3, v.max(), color=INK2, lw=1.2, zorder=2)
        ax.scatter(i + 0.14 + rng.uniform(0, 0.16, len(v)), v, s=60, color=COL[p],
                   edgecolor="white", lw=1.2, zorder=5)
    ax.set_xticks(range(3), [f"{SHORT[p]}\n(n={len(g[p])})" for p in POS])
    ax.set_xlim(-0.6, 2.45)
    ax.set_ylabel("Mittlere Verzögerung ā [m/s²]")
    ax.set_title("Verteilung je Position")
    ax.grid(axis="x", visible=False)

    ref = g["Vorne"]
    for j, p in enumerate(["Neutral", "Hinten"]):
        diff = g[p].mean() - ref.mean()
        va, vb = g[p].var(ddof=1) / len(g[p]), ref.var(ddof=1) / len(ref)
        se = np.sqrt(va + vb)
        dof = (va + vb) ** 2 / (va ** 2 / (len(g[p]) - 1) + vb ** 2 / (len(ref) - 1))
        ci = diff + np.array([-1, 1]) * t_dist.ppf(0.975, dof) * se
        yy2 = diff + np.linspace(-4, 4, 300) * se   # Stichprobenverteilung der Differenz
        dens = t_dist.pdf((yy2 - diff) / se, dof)
        dens = 0.35 * dens / dens.max()
        ax2.fill_betweenx(yy2, j, j + dens, color=COL[p], alpha=0.3, lw=0)
        ax2.vlines(j, *ci, color=INK, lw=2.5)
        ax2.scatter(j, diff, s=90, color=INK, zorder=4)
        ax2.annotate(f"{diff:+.2f} m/s²\nKI [{ci[0]:+.2f}; {ci[1]:+.2f}]", (j, diff), xytext=(-12, 0),
                     textcoords="offset points", ha="right", va="center", fontsize=12, color=INK)
    ax2.axhline(0, color=INK2, lw=1, ls="--")
    ax2.set_xticks([0, 1], ["neutral − vorn", "hinten − vorn"])
    ax2.set_xlim(-0.9, 1.5)
    ax2.set_ylabel("Differenz ā [m/s²]")
    ax2.set_title("Differenz zu vorn (95-%-KI Welch, unkorrigiert)", fontsize=14)
    ax2.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_FIG, "Fig5_Raincloud_Schaetzung.png"))
    plt.close(fig)


# --------------------------------------------------------------------------- Fig 6
def fig_heatmap(trials):
    """Jede Zeile = ein Trial (Aufnahmereihenfolge), Farbe = Verzögerung -a_x."""
    grid = np.arange(-0.5, 1.9, 0.005)
    order = sorted(trials, key=clock)
    M = np.array([-on_grid(r, "a_x", grid) for r in order])
    M = np.clip(M, 0, None)   # Beschleunigung (>0) als "keine Verzögerung"
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(M, aspect="auto", cmap=SEQ, vmin=0, vmax=10, interpolation="nearest",
                   extent=[grid[0], grid[-1], len(order) - 0.5, -0.5])
    ax.grid(False)
    for i, r in enumerate(order):   # Bremsende markieren
        ax.plot([r["dur"]] * 2, [i - 0.45, i + 0.45], color=INK, lw=1.5)
        ax.scatter(r["t_stop"], i, marker="D", s=28, color="white", edgecolor=INK, lw=1, zorder=4)
    ax.axvline(0, color=INK, lw=1, ls=":")
    pos_seq = [r["position"] for r in order]
    for i in range(1, len(order)):
        if pos_seq[i] != pos_seq[i - 1]:
            ax.axhline(i - 0.5, color="white", lw=3)
    labels = [r["name"].split()[-1].replace("-", ":") for r in order]
    ax.set_yticks(range(len(order)), labels, fontsize=9)
    for p in POS:   # Positionsname mittig am Block
        idx = [i for i, q in enumerate(pos_seq) if q == p]
        ax.text(grid[-1] + 0.04, np.mean(idx), f"{SHORT[p]}\n(n={len(idx)})", va="center",
                fontsize=13, color=INK)
    ax.set_xlabel("Zeit relativ zum Bremsbeginn [s]")
    ax.set_ylabel("Trial (Uhrzeit der Aufnahme)")
    cb = fig.colorbar(im, ax=ax, pad=0.14, extend="max")
    cb.set_label("Verzögerung −a$_x$ [m/s²]")
    cb.outline.set_visible(False)
    ax.set_title("Alle 30 Bremsungen · Strich = Ende Bremsfenster · Raute = v (Rumpf) = 0", fontsize=14)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_FIG, "Fig6_Heatmap_Trials.png"))
    plt.close(fig)


# --------------------------------------------------------------------------- Fig 7
def fig_phase(trials):
    """Verzögerung über der Geschwindigkeit, Bremsbeginn bis Stillstand (v = 0).
    Mittelkurve: pro Trial in 1-km/h-Klassen gemittelt, dann über Trials."""
    edges = np.arange(0, 28, 1.0)
    mids = edges[:-1] + 0.5
    curves = {}
    for p in POS:
        rows = []
        for r in (x for x in trials if x["position"] == p):
            st = int(np.argmin(np.abs(r["t"] - r["t_start"])))
            ks = st + int(round(r["t_stop"] * r["fs"]))
            v, d = r["v"][st:ks + 1] * 3.6, -r["a_x"][st:ks + 1]
            idx = np.digitize(v, edges) - 1
            rows.append([d[idx == k].mean() if np.any(idx == k) else np.nan for k in range(len(mids))])
        R = np.array(rows)
        n = np.sum(~np.isnan(R), 0)
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mu = np.nanmean(R, 0)
        mu[n < 5] = np.nan   # nur Klassen, die mind. die Hälfte der Trials durchfährt
        curves[p] = mu
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.5), sharey=True)
    for ax, p in zip(axs, POS):
        for q in POS:
            if q != p:
                ax.plot(mids, curves[q], color=GRID, lw=2.5, zorder=1)
        tr = [x for x in trials if x["position"] == p]
        for r in tr:
            st = int(np.argmin(np.abs(r["t"] - r["t_start"])))
            ks = st + int(round(r["t_stop"] * r["fs"]))
            ax.plot(r["v"][st:ks + 1] * 3.6, -r["a_x"][st:ks + 1], color=COL[p], lw=1, alpha=0.35, zorder=2)
            ax.scatter(r["v0"] * 3.6, -r["a_x"][st], s=36, color=COL[p], edgecolor="white", lw=1, zorder=3)
        ax.plot(mids, curves[p], color=COL[p], lw=3.5, zorder=4)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xlim(27, 0)   # Bremsung läuft von links (v0) nach rechts (Stillstand)
        ax.set_title(f"{LABEL[p]} (n={len(tr)})", fontsize=14)
        ax.set_xlabel("Geschwindigkeit v [km/h]  →  Stillstand")
    axs[0].set_ylabel("Verzögerung −a$_x$ [m/s²]")
    axs[0].set_ylim(-4, 14)
    fig.text(0.99, 0.01, "dünn: Einzeltrials · Punkt: Bremsbeginn (v₀) · dick: Mittel · grau: andere Positionen",
             ha="right", fontsize=11, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT_FIG, "Fig7_Phasenportraet.png"))
    plt.close(fig)


# --------------------------------------------------------------------------- Fig 8
def fig_gg(trials):
    """g-g-Diagramm: Quer- vs. Längsbeschleunigung im Bremsfenster (in g),
    mit Reifenhaftkreis μg und Überschlaggrenze als Referenzbänder."""
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.8), sharex=True, sharey=True)
    th = np.linspace(0, 2 * np.pi, 400)
    for ax, p in zip(axs, POS):
        ax.fill(np.r_[MU_LIM[1] * np.cos(th), MU_LIM[0] * np.cos(th[::-1])],
                np.r_[MU_LIM[1] * np.sin(th), MU_LIM[0] * np.sin(th[::-1])], color="#f0efec", lw=0)
        ax.axhspan(-PITCH_LIM[1], -PITCH_LIM[0], color="#e4e3df", lw=0)
        tr = [x for x in trials if x["position"] == p]
        for r in tr:
            w = (r["t"] >= r["t_start"]) & (r["t"] <= r["t_end"])
            ax.plot(r["a_y"][w] / G, r["a_x"][w] / G, color=COL[p], lw=1, alpha=0.4)
            ax.scatter(r["a_y"][w].mean() / G, -r["mean"] / G, s=40, color=COL[p],
                       edgecolor="white", lw=1, zorder=4)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_aspect("equal")
        ax.set_title(f"{LABEL[p]} (n={len(tr)})", fontsize=14)
        ax.set_xlabel("Querbeschleunigung [g]")
    axs[0].set_ylabel("Längsbeschleunigung [g]  (Bremsen < 0)")
    axs[0].set_xlim(-0.8, 0.8)
    axs[0].set_xticks([-0.6, -0.3, 0, 0.3, 0.6])
    axs[0].set_ylim(-1.3, 0.3)
    axs[0].text(-0.78, -PITCH_LIM[1] - 0.02, "Überschlaggrenze\n≈ 0,55–0,65 g", fontsize=11,
                color=INK2, va="top")
    axs[0].text(-0.78, 0.18, "Reifenhaftung μg ≈ 0,7–0,8 g", fontsize=11, color=INK2)
    fig.text(0.99, 0.01, "Linie: Rumpf-Signal im Bremsfenster · Punkt: Mittel je Trial (ā) · "
             "Grenzen = Schätzwerte für das Gesamtsystem Rad + Fahrer",
             ha="right", fontsize=11, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT_FIG, "Fig8_gg_Diagramm.png"))
    plt.close(fig)


# --------------------------------------------------------------------------- Fig 9
# Ausgangshaltung des Rumpfs (Grad aus der Senkrechten, + = nach vorn) ist NICHT gemessen,
# nur schematisch; animiert wird die gemessene Neigungsänderung ggü. der Rollphase.
START_LEAN = {"Vorne": 30.0, "Neutral": 15.0, "Hinten": -15.0}   # Haltung in der Rollphase
TRUNK, ARM = 0.60, 0.55   # m, schematische Segmentlängen


def fig_animation(trials, fps=20, slow=0.5):
    dt = slow / fps   # Zeitlupe: 'slow' s Realzeit pro s Video
    grid = np.arange(-0.5, 1.9, dt)
    mean, n, t_stop = {}, {}, {}
    for p in POS:
        # Stoppie-Trials ausschließen: Handy-Neigung = Rumpf + Radnicken
        tr = [x for x in trials if x["position"] == p and x["name"] not in STOPPIE]
        n[p] = len(tr)
        t_stop[p] = np.median([r["t_stop"] for r in tr])
        mean[p] = (np.nanmean([on_grid(r, "a_x", grid) for r in tr], 0),
                   np.nanmean([on_grid(r, "pitch", grid) for r in tr], 0))
    fig = plt.figure(figsize=(13, 7.5))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.5, 1])
    bike_axes, rider, arrows, txt = [], {}, {}, {}
    hip, bar = np.array([0.0, 0.95]), np.array([0.55, 1.05])
    for i, p in enumerate(POS):
        ax = fig.add_subplot(gs[0, i])
        ax.set_xlim(-0.9, 1.2)
        ax.set_ylim(0, 1.9)
        ax.set_aspect("equal")
        ax.axis("off")
        for cx in (-0.35, 0.75):   # Räder
            ax.add_patch(plt.Circle((cx, 0.36), 0.36, fill=False, ec=INK2, lw=2))
        ax.plot([-0.35, 0.05, 0.75], [0.36, 0.95, 0.36], color=INK2, lw=2.5)   # Rahmen schematisch
        ax.plot([0.05, bar[0]], [0.95, bar[1]], color=INK2, lw=2.5)
        ax.plot([-1, 1.3], [0, 0], color=INK2, lw=1)
        trunk, = ax.plot([], [], color=COL[p], lw=7, solid_capstyle="round")
        arm, = ax.plot([], [], color=COL[p], lw=4, solid_capstyle="round")
        head = plt.Circle((0, 0), 0.11, color=COL[p])
        ax.add_patch(head)
        rider[p] = (trunk, arm, head)
        arrows[p] = ax.annotate("", xy=(0, 0), xytext=(0, 0),
                                arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.5, mutation_scale=22))
        txt[p] = ax.text(0.15, 1.82, "", ha="center", fontsize=13, color=INK)
        ax.set_title(f"{LABEL[p]} (n={n[p]})", fontsize=15, color=INK)
        bike_axes.append(ax)
    axc = fig.add_subplot(gs[1, :])
    for p in POS:
        axc.plot(grid, mean[p][0], color=COL[p], lw=2.5, label=LABEL[p])
    axc.axhline(0, color=INK2, lw=0.8)
    t_after = min(t_stop.values())
    axc.axvspan(t_after, grid[-1], color="#f0efec", zorder=0)
    axc.text(t_after + 0.02, -7.5, "nach Stillstand: Landung Hinterrad / Fuß absetzen\n"
             "→ Rumpf + Rad nicht trennbar, nicht interpretieren", fontsize=10, color=INK2)
    cursor = axc.axvline(grid[0], color=INK, lw=1.5)
    axc.set_xlim(grid[0], grid[-1])
    axc.set_xlabel("Zeit relativ zum Bremsbeginn [s]")
    axc.set_ylabel("a$_x$ [m/s²]")
    axc.legend(loc="upper left", frameon=False, ncol=3, fontsize=11)
    fig.text(0.01, 0.01, f"Mittel je Position{' (ohne Stoppie-Trials)' if STOPPIE else ''} · Zeitlupe {slow:g}× · Pfeil = Verzögerung · "
             "Haltung in der Rollphase schematisch, Neigungsänderung Δθ ggü. Rollphase gemessen (Gyro)",
             fontsize=10, color=INK2)
    clock_txt = fig.text(0.99, 0.96, "", ha="right", fontsize=14, color=INK)

    def update(k):
        for p in POS:
            a, pitch = mean[p][0][k], mean[p][1][k]
            lean = np.radians(START_LEAN[p] + pitch)
            sh = hip + TRUNK * np.array([np.sin(lean), np.cos(lean)])
            trunk, arm, head = rider[p]
            trunk.set_data([hip[0], sh[0]], [hip[1], sh[1]])
            arm.set_data([sh[0], bar[0]], [sh[1], bar[1]])
            head.center = tuple(sh + 0.17 * np.array([np.sin(lean), np.cos(lean)]))
            ksp = hip + 0.3 * TRUNK * np.array([np.sin(lean), np.cos(lean)])
            arrows[p].xy = tuple(ksp + np.array([0.06 * a, 0]))   # a < 0 -> Pfeil nach hinten
            arrows[p].set_position(tuple(ksp))
            after = grid[k] > t_stop[p]   # nach Stillstand: Figur blass
            for art in (trunk, arm, head):
                art.set_alpha(0.3 if after else 1.0)
            txt[p].set_text(f"a = {a:+.1f} m/s²   Δθ = {pitch:+.0f}°" + ("  (Stillstand)" if after else ""))
        cursor.set_xdata([grid[k]] * 2)
        clock_txt.set_text(f"t = {grid[k]:+.2f} s")
        return []

    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    anim = FuncAnimation(fig, update, frames=len(grid), blit=False)
    anim.save(os.path.join(OUT_FIG, "Fig9_Rumpf_Animation.gif"), writer=PillowWriter(fps=fps), dpi=90)
    update(int(np.argmin(np.abs(grid - 0.6))))   # Standbild für Dokumentation
    fig.savefig(os.path.join(OUT_FIG, "Fig9_Rumpf_Standbild.png"), dpi=150)
    plt.close(fig)


def make_all(trials, df):
    fig_raincloud(df)
    fig_heatmap(trials)
    fig_phase(trials)
    fig_gg(trials)
    fig_animation(trials)


if __name__ == "__main__":
    style()
    os.makedirs(OUT_FIG, exist_ok=True)
    tr = run_all()
    make_all(tr, table(tr))
