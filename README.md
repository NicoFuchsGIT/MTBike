# MTBike – Bremsanalyse (Thema 2 „Bremsen“)

KSP-Verzögerung beim Vollbremsen mit dem E-MTB, gemessen mit einem Smartphone (phyphox, Samsung SM-G990B, 412 Hz) am Bauch.
Proband: 1 Person. Positionen: **Vorne / Neutral / Hinten** (sitzend), je 10 Trials.

## Ausführen
```bash
pip install -r requirements.txt
python analysis/run_analysis.py
```
Ausgaben:
- `results/results_trials.csv`: alle Kennwerte pro Trial
- `results/summary.csv`: MW ± SD und Test
- `results/stats.txt`: Details inkl. Shapiro, Levene, Post-hoc, Cohen's d
- `figures/Fig2–4`: 300 dpi

Diagnoseplot mit allen 30 Trials und Bremsfenster:
`python analysis/diag_plot.py <out.png>` (aus `analysis/` heraus).

## Methode (Kurzfassung für das Poster)
1. **Daten:** Acc (inkl. g) und Gyro auf ein gemeinsames Raster legen. Butterworth-Tiefpass 4. Ordnung ohne Phasenverschiebung, 5 Hz für Acc und 10 Hz für Gyro.
2. **Referenz Stillstand:** Das ruhigste 0,4-s-Fenster nach der Bremsung definiert die Lotrichtung.
3. **Drehung ins Weltsystem:** Die Gyro-Integration rückwärts ab dem Stillstand (≤ 6 s) dreht jede Probe ins Weltsystem. Damit wird die Rumpfneigung kompensiert, die sonst die Erdbeschleunigung in die Messachse einstreut.
4. **Längsbeschleunigung:** Die lineare Beschleunigung wird in die Horizontale projiziert. Die Fahrtrichtung ist die Hauptachse (PCA), das Vorzeichen ist so gewählt, dass Bremsen negativ ist.
5. **Bremsfenster:** Die Phase, in der a_x (2-Hz-Signal) unter −1 m/s² liegt, rund um das stärkste 0,5-s-Verzögerungsplateau. Davon wird eine Baseline aus der Rollphase abgezogen.
6. **Kennwerte:**
   - mittlere und maximale Verzögerung, Bremsdauer
   - v₀ = −∫a dt
   - Bremsweg = ∫v dt
   - Rumpf-Nickwinkel über das Gyro um die Querachse
7. **Statistik:**
   - MW ± SD (n = 10), Shapiro-Wilk und Levene
   - ANOVA bzw. Kruskal-Wallis, je nach Normalverteilung
   - Tukey-HSD als Post-hoc, Effektstärken η² und Cohen's d

Alle **30/30 Trials** wurden automatisch erkannt. Die Bremsfenster wurden zusätzlich visuell geprüft.

## Ergebnisse (MW ± SD, n = 10 je Position)
| Kennwert | Vorne | Neutral | Hinten | Test |
|---|---|---|---|---|
| **Mittlere Verzögerung [m/s²]** | 5,01 ± 0,41 | **5,44 ± 0,37** | 5,10 ± 0,34 | Kruskal-Wallis p = 0,034, η² = 0,22; Vorne–Neutral p = 0,037 (d = 1,1) |
| Maximale Verzögerung [m/s²] | 8,86 ± 0,82 | 9,55 ± 0,72 | 9,84 ± 1,33 | ANOVA p = 0,094 (n.s.) |
| Bremsdauer [s] | 1,40 ± 0,20 | 1,21 ± 0,10 | 1,12 ± 0,06 | ANOVA p < 0,001 ⚠ v₀-abhängig |
| Bremsweg [m] | 4,99 ± 0,90 | 4,01 ± 0,40 | 3,60 ± 0,50 | ANOVA p < 0,001 ⚠ v₀-abhängig |
| Anfangsgeschw. v₀ [km/h] | 25,0 ± 1,7 | 23,7 ± 1,1 | 20,6 ± 1,6 | ANOVA p < 0,001 |
| Rumpfneigung nach vorn (max.) [°] | 15 ± 9 | 15 ± 6 | 42 ± 6 | ANOVA p < 0,001 |

### Interpretation / Diskussionspunkte
- **Hauptbefund:** Die mittlere KSP-Verzögerung ist in der **neutralen** Position am größten, rund 8 % mehr als in der vorgebeugten Position. Die Unterschiede sind insgesamt klein (≈ 0,4 m/s²), aber signifikant, mit großem Effekt zwischen Vorne und Neutral.
- **Vorne:** Die Verzögerung baut sich am langsamsten auf (Fig. 3). Ein plausibler Grund ist, dass der KSP weit vorne liegt. Dann wird das Hinterrad früher entlastet, und der Fahrer dosiert die Vorderradbremse vorsichtiger (Überschlaggrenze, vgl. Wilson & Schmidt).
- **Hinten:** Der Rumpf kippt beim Bremsen stark nach vorn (≈ 42°). Die aufgebaute Körperenergie geht also in eine Rumpfrotation statt in einen stabilen Abstützimpuls. Die Bremskurve zeigt einen Einbruch bei ≈ 0,3 s (Fig. 3).
- **Störgröße Anfangsgeschwindigkeit:** Statt der geplanten 20 km/h wurden real ≈ 21–25 km/h gefahren, und zwar systematisch je Position verschieden (die Vorne-Trials kamen zuerst). Bremsdauer und Bremsweg korrelieren stark mit v₀ (r = 0,78 bzw. 0,89). Sie sind deshalb **nicht** als Positionseffekt interpretierbar. Die mittlere Verzögerung korreliert dagegen nicht mit v₀ (r = 0,03) und ist der geeignete Hauptkennwert.
- **Plausibilität:** v₀ aus der Integration (23,1 km/h im Mittel) passt zur Abregelgrenze des E-MTB (25 km/h). Außerdem stimmt ā mit v₀/t_B überein. Der Peak (~1 g) ist durch Körperoszillationen überhöht und weniger robust als ā.
- **Limitationen:**
  - n = 1 Proband; die Trials sind Wiederholungen, keine unabhängige Stichprobe.
  - Das Handy am Bauch misst den Rumpf/Becken-Bereich als KSP-Näherung.
  - Die Fahrgeschwindigkeit wurde nicht kontrolliert.
  - Die Gyro-Integration ist nur über kurze Zeit driftarm.

## Struktur
- `analysis/io_phyphox.py`: robustes CSV-Einlesen (Komma/Tab, Dezimalpunkt/-komma)
- `analysis/brake_pipeline.py`: Signalverarbeitung pro Trial
- `analysis/run_analysis.py`: Batch, Statistik, Abbildungen
- `analysis/diag_plot.py`: Kontrollplot aller Trials
- `codex_legacy/`: alte Codex-Skripte (nicht verwenden, siehe PRD §3)
- `files/`: Rohdaten phyphox
