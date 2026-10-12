"""Hauptskript: alle Trials auswerten, Statistik rechnen, Poster-Abbildungen exportieren.

Aufruf (aus dem Repo-Root):  python analysis/run_analysis.py
Ausgabe:  results/results_trials.csv, results/summary.csv, results/stats.txt,
          figures/Fig2_Methode.png, figures/Fig3_Bremskurven.png, figures/Fig4_Vergleich.png
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brake_pipeline import analyze, V0  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "files")
OUT_RES = os.path.join(ROOT, "results")
OUT_FIG = os.path.join(ROOT, "figures")
POS = ["Vorne", "Neutral", "Hinten"]
LABEL = {"Vorne": "nach vorn gelehnt", "Neutral": "neutral", "Hinten": "nach hinten gelehnt"}
# Kategoriale Farben (validierte Referenzpalette, Slots 1-3, in fester Reihenfolge)
COL = {"Vorne": "#2a78d6", "Neutral": "#eb6834", "Hinten": "#1baf7a"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

METRICS = [
    ("mean", "Mittlere Verzögerung", "m/s²"),
    ("peak", "Maximale Verzögerung", "m/s²"),
    ("dur", "Bremsdauer", "s"),
    ("t_to_peak", "Zeit bis Maximum", "s"),
    ("v0", "Anfangsgeschw. (aus ∫a dt)", "m/s"),
    ("dist", "Bremsweg (aus ∫∫a dt)", "m"),
    ("pitch_max", "Rumpfneigung nach vorn (max.)", "°"),
]


def style():
    plt.rcParams.update({
        "font.size": 14, "axes.titlesize": 15, "axes.labelsize": 14,
        "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 12,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
        "ytick.color": INK2, "text.color": INK, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
        "axes.spines.right": False, "figure.facecolor": "white",
        "axes.facecolor": "white", "savefig.dpi": 300,
    })


def run_all():
    trials = []
    for d in sorted(glob.glob(os.path.join(DATA, "*"))):
        r = analyze(d)
        if r is None:
            print("FEHLT:", os.path.basename(d))
            continue
        trials.append(r)
    return trials


def table(trials):
    rows = [{"Position": r["position"], "Trial": r["name"],
             **{k: r[k] for k, _, _ in METRICS},
             "delta_v": r["dv"], "t_start": r["t_start"], "t_end": r["t_end"]} for r in trials]
    return pd.DataFrame(rows)


def fmt_p(p):
    return "p<0.001" if p < 0.001 else f"p={p:.3f}"


def cohen_d(a, b):
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / sp


def statistics(df):
    lines, summ = [], []
    for key, name, unit in METRICS:
        groups = [df.loc[df.Position == p, key].to_numpy() for p in POS]
        row = {"Kennwert": f"{name} [{unit}]"}
        for p, g in zip(POS, groups):
            row[p] = f"{g.mean():.2f} ± {g.std(ddof=1):.2f}"
        normal = all(stats.shapiro(g).pvalue > 0.05 for g in groups)
        levene = stats.levene(*groups).pvalue
        F, p_anova = stats.f_oneway(*groups)
        H, p_kw = stats.kruskal(*groups)
        allv = np.concatenate(groups)
        ss_b = sum(len(g) * (g.mean() - allv.mean()) ** 2 for g in groups)
        eta2 = ss_b / ((allv - allv.mean()) ** 2).sum()
        if normal:
            row["Test"] = f"ANOVA F(2,{len(allv) - 3})={F:.2f}, {fmt_p(p_anova)}, η²={eta2:.2f}"
            p_main = p_anova
        else:
            row["Test"] = f"Kruskal-Wallis H={H:.2f}, {fmt_p(p_kw)}, η²={eta2:.2f}"
            p_main = p_kw
        summ.append(row)
        lines.append(f"\n== {name} [{unit}] ==")
        for p, g in zip(POS, groups):
            lines.append(f"  {p:8} n={len(g):2d}  MW={g.mean():6.2f}  SD={g.std(ddof=1):5.2f}  "
                         f"CV={100 * g.std(ddof=1) / abs(g.mean()):5.1f}%  Shapiro p={stats.shapiro(g).pvalue:.3f}")
        lines.append(f"  Levene p={levene:.3f} | ANOVA F={F:.2f} p={p_anova:.4f} | "
                     f"Kruskal-Wallis H={H:.2f} p={p_kw:.4f} | eta²={eta2:.3f}")
        if p_main < 0.05:
            tk = stats.tukey_hsd(*groups)
            for i in range(3):
                for j in range(i + 1, 3):
                    lines.append(f"    post-hoc {POS[i]}-{POS[j]}: Tukey p={tk.pvalue[i, j]:.4f}, "
                                 f"Cohen's d={cohen_d(groups[i], groups[j]):.2f}")
    return pd.DataFrame(summ), "\n".join(lines)


def fig_method(trials):
    """Fig 2: Beispiel-Trial – Längsbeschleunigung mit Bremsfenster und Geschwindigkeit."""
    r = next(t for t in trials if t["name"] == "Neutral Trial 15-18-12")
    t = r["t"] - r["t_start"]
    m = (t > -3) & (t < 2.5)
    fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax[0].axvspan(0, r["dur"], color="#f0efec", zorder=0)
    ax[0].plot(t[m], r["a_x"][m], color=COL["Neutral"], lw=2)
    ax[0].axhline(0, color=INK2, lw=0.8)
    ax[0].axhline(-r["mean"], color=INK, lw=1, ls="--")
    ax[0].annotate(f"ā = {r['mean']:.1f} m/s²", (r["dur"] / 2, -r["mean"]), xytext=(0, 8),
                   textcoords="offset points", ha="center", fontsize=13)
    ax[0].text(-2.9, 2.6, "Treten / Rollen", color=INK2, fontsize=13)
    ax[0].text(0.05, 2.6, "Bremsphase", color=INK, fontsize=13)
    ax[0].set_ylabel("a$_x$ KSP [m/s²]")
    ax[0].set_ylim(-11, 4)
    # Geschwindigkeit: rückwärts ab Stillstand integriert
    a = r["a_x"][m]
    v = np.cumsum(a[::-1])[::-1] / r["fs"] * -1
    v = np.clip(v, 0, None)
    ax[1].plot(t[m], v * 3.6, color=INK, lw=2)
    ax[1].axhline(V0 * 3.6, color=INK2, lw=1, ls=":")
    ax[1].text(-2.9, V0 * 3.6 + 1, "Soll 20 km/h", color=INK2, fontsize=12)
    ax[1].set_ylabel("v [km/h]")
    ax[1].set_xlabel("Zeit relativ zum Bremsbeginn [s]")
    ax[1].set_ylim(0, 30)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_FIG, "Fig2_Methode.png"))
    plt.close(fig)


def fig_curves(trials):
    """Fig 3: mittlere Verzögerungskurve ± SD je Position, ausgerichtet auf Bremsbeginn."""
    grid = np.arange(-0.5, 2.0, 0.005)
    fig, ax = plt.subplots(figsize=(10, 6))
    for p in POS:
        M = []
        for r in (x for x in trials if x["position"] == p):
            tr = r["t"] - r["t_start"]
            y = np.interp(grid, tr, r["a_x"], left=np.nan, right=np.nan)
            y[grid > r["dur"] + 0.05] = np.nan   # nach Stillstand ausblenden
            M.append(y)
        M = np.array(M)
        ok = np.sum(~np.isnan(M), 0) == len(M)   # nur solange alle Trials noch bremsen
        with np.errstate(all="ignore"):
            mu, sd = np.nanmean(M, 0), np.nanstd(M, 0, ddof=1)
        ax.fill_between(grid[ok], (mu - sd)[ok], (mu + sd)[ok], color=COL[p], alpha=0.15, lw=0)
        ax.plot(grid[ok], mu[ok], color=COL[p], lw=2.5, label=f"{LABEL[p]} (n={len(M)})")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(0, color=INK2, lw=0.8, ls=":")
    ax.set_xlim(-0.5, 1.2)
    ax.set_xlabel("Zeit relativ zum Bremsbeginn [s]")
    ax.set_ylabel("Längsbeschleunigung KSP [m/s²]")
    ax.legend(loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_FIG, "Fig3_Bremskurven.png"))
    plt.close(fig)


def fig_compare(df):
    """Fig 4: Einzelwerte + MW ± SD je Position: Verzögerung (Ziel) und v0 (Störgröße)."""
    keys = [("mean", "Mittlere Verzögerung [m/s²]"), ("peak", "Maximale Verzögerung [m/s²]"),
            ("v0", "Anfangsgeschwindigkeit [m/s]")]
    fig, axs = plt.subplots(1, 3, figsize=(14, 5.5))
    rng = np.random.default_rng(1)
    for ax, (k, lab) in zip(axs, keys):
        for i, p in enumerate(POS):
            v = df.loc[df.Position == p, k].to_numpy()
            ax.scatter(i + rng.uniform(-0.12, 0.12, len(v)), v, s=46, color=COL[p], alpha=0.75,
                       edgecolor="white", linewidth=1, zorder=3)
            ax.errorbar(i + 0.28, v.mean(), yerr=v.std(ddof=1), fmt="o", color=INK, ms=7,
                        capsize=6, lw=1.8, zorder=4)
        ax.set_xticks(range(3), ["vorn", "neutral", "hinten"])
        ax.set_xlim(-0.5, 2.6)
        ax.set_title(lab, fontsize=14)
        ax.grid(axis="x", visible=False)
        if k == "v0":
            ax.axhline(V0, color=INK2, lw=1, ls=":")
            ax.text(-0.45, V0 - 0.05, "Soll 20 km/h", color=INK2, fontsize=11, va="top")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_FIG, "Fig4_Vergleich.png"))
    plt.close(fig)


def main():
    os.makedirs(OUT_RES, exist_ok=True)
    os.makedirs(OUT_FIG, exist_ok=True)
    style()
    trials = run_all()
    df = table(trials)
    df.to_csv(os.path.join(OUT_RES, "results_trials.csv"), index=False, float_format="%.3f")
    summ, txt = statistics(df)
    summ.to_csv(os.path.join(OUT_RES, "summary.csv"), index=False)
    dv_ok = (df.v0.between(0.8 * V0, 1.2 * V0)).mean()
    head = (f"Trials ausgewertet: {len(df)} / 30\n"
            f"Validierung: v0 aus ∫a dt = {df.v0.mean():.2f} ± {df.v0.std(ddof=1):.2f} m/s "
            f"({df.v0.mean() * 3.6:.1f} km/h, Soll {V0 * 3.6:.0f} km/h); "
            f"{100 * dv_ok:.0f} % der Trials innerhalb ±20 %\n")
    with open(os.path.join(OUT_RES, "stats.txt"), "w", encoding="utf-8") as f:
        f.write(head + txt + "\n")
    print(head + txt)
    print("\n", summ.to_string(index=False))
    fig_method(trials)
    fig_curves(trials)
    fig_compare(df)


if __name__ == "__main__":
    main()
