# Roadmap (Abgabe 15.10.2026)

| Tag | Aufgabe | Output | Wer |
|---|---|---|---|
| **Mo 12.10** | ✅ Messdaten (`extracted/`) ins Repo pushen | Daten im Repo | Nico |
| | ✅ Datencheck: Dateistruktur, fs, Achslage, Phasen (Anfahren/Rollen/Bremsen) in jedem Trial sichtbar? | kurzer Datenreport | Claude |
| | ✅ Pipeline v1: Laden → Filter → g-Entfernung (Gyro) → `a_x` → Bremsfenster | `analysis/` | Claude |
| **Di 13.10** | ✅ Δv-Validierung, Kennwerte für alle 30 Trials, Ausreißer-Review | `results.csv`, `summary.csv` | Claude |
| | ✅ Statistik (Shapiro, ANOVA/Kruskal-Wallis, Post-hoc, Effektstärke) | Statistiktabelle | Claude |
| | ✅ Fig 2–4 posterfertig; offen: Foto/Skizze für Fig 1 liefern | `figures/` | Claude + Nico |
| | ✅ Realismus-Check: v₀ bis Stillstand, Post-hoc korrigiert, Peak als Rumpfwert | `README.md` | Claude |
| | Poster/Template: **nicht Teil dieses Auftrags** (nur Datenauswertung) | – | – |

**Kritischer Pfad:** Daten pushen → Pipeline → Kennwerte. Alles danach ist Text- und Layoutarbeit.
**Umfang:** nur die korrekte Datenauswertung (Kennwerte, Statistik, Abbildungen).
