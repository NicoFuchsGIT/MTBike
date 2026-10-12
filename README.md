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
   - v₀ = −∫a dt vom Bremsbeginn bis zum Stillstand (inkl. Rückschwung)
   - Bremsweg = ∫v dt bis v = 0
   - Rumpf-Nickwinkel über das Gyro um die Querachse, bezogen auf die Rollphase (1,0–0,6 s vor Bremsbeginn)
7. **Statistik:**
   - MW ± SD (n = 10), Shapiro-Wilk und Levene
   - ANOVA bzw. Kruskal-Wallis, je nach Normalverteilung
   - Post-hoc: Tukey-HSD nach ANOVA, Mann-Whitney mit Bonferroni nach Kruskal-Wallis
   - Effektstärken η² bzw. η²_H und Cohen's d

Alle **30/30 Trials** wurden automatisch erkannt. Die Bremsfenster wurden zusätzlich visuell geprüft.

## Ergebnisse (MW ± SD, n = 10 je Position)
| Kennwert | Vorne | Neutral | Hinten | Test |
|---|---|---|---|---|
| **Mittlere Verzögerung ā [m/s²]** | 5,01 ± 0,41 | **5,44 ± 0,37** | 5,10 ± 0,34 | Kruskal-Wallis H = 6,77, p = 0,034, η²_H = 0,18 (ANOVA p = 0,035) |
| Spitzenverzögerung Rumpf [m/s²] | 8,86 ± 0,82 | 9,55 ± 0,72 | 9,84 ± 1,33 | ANOVA p = 0,094 (n.s.) |
| Bremsdauer [s] | 1,40 ± 0,20 | 1,21 ± 0,10 | 1,12 ± 0,06 | ANOVA p < 0,001 ⚠ v₀-abhängig |
| Bremsweg [m] | 4,48 ± 0,90 | 3,46 ± 0,48 | 3,65 ± 0,53 | ANOVA p = 0,004 ⚠ v₀-abhängig |
| Anfangsgeschw. v₀ [km/h] | 23,5 ± 2,0 | 21,9 ± 1,5 | 20,4 ± 1,4 | ANOVA p = 0,001 |
| Rumpfneigung nach vorn (max., ggü. Rollphase) [°] | 38 ± 8 | 16 ± 7 | 44 ± 5 | ANOVA p < 0,001, η² = 0,77; Tukey: vorn–neutral und neutral–hinten p < 0,001, vorn–hinten p = 0,18 (n.s.) |

Post-hoc ā (Hinten nicht normalverteilt, Shapiro p = 0,010):
- Vorne–Neutral: Mann-Whitney mit Bonferroni p = 0,063, Tukey p = 0,037, d = 1,1
- die übrigen Paare n.s.

Sensitivitätsanalyse: Mit ā' = v₀ / Zeit bis Stillstand bleibt die Reihenfolge gleich (Neutral 5,80 ± 0,44 > Vorne 5,15 ± 0,47 > Hinten 4,78 ± 0,86 m/s²; ANOVA p = 0,004).

### Realismus-Check
| Größe | gemessen | physikalisch erwartbar | Bewertung |
|---|---|---|---|
| ā (≈ 0,51–0,55 g) | 5,0–5,4 m/s² | Überschlaggrenze sitzend ≈ g·b/h ≈ 0,55–0,65 g (b ≈ 0,7 m KSP–Vorderradaufstand, h ≈ 1,1–1,2 m); Fahrrad-Vollbremsung typ. ≈ 0,5–0,6 g | ✅ realistisch, knapp unter der Überschlaggrenze |
| Spitzenwert (0,8–1,2 g) | 7,8–12 m/s² | Das System Rad + Fahrer kann nicht stärker verzögern als μ·g (≈ 0,7–0,8 g) und die Überschlaggrenze erlauben | ⚠ **kein KSP-Wert**: Rumpfsegment, das von den Armen abgefangen wird und schwingt (≈ 3–4 Hz). Nur als Rumpfbelastung interpretieren. |
| v₀ | 21,9 ± 2,1 km/h | Soll 20 km/h, E-MTB-Unterstützung bis 25 km/h | ✅ 83 % innerhalb ±20 % (Kriterium ≥ 80 % erfüllt) |
| Konsistenz | ā·t_B = Δv im Fenster; v₀²/(2ā) = 3,65 m vs. Bremsweg 3,86 m | – | ✅ in sich stimmig (Rest: Anfangs- und Endrampe) |
| Rollphase | v vor der Bremsung konstant (Schwankung ≈ ±0,3 m/s, Fig. 2) | konstant, leicht abnehmend | ✅ Schwerkraftkompensation funktioniert |
| Rückschwung | v kurz ≈ −0,7 m/s nach dem Stopp (Fig. 2) | Rumpf schwingt nach dem Stopp zurück | ✅ plausibel; deshalb wird v₀ bis zum Stillstand integriert, nicht nur im Fenster (sonst +0,3 m/s) |
| Rumpfneigung | vorn 38°, neutral 16°, hinten 44° (ggü. Rollphase) | Rumpf kippt beim Bremsen nach vorn, bis die Arme ihn abfangen | ⚠ plausibel. Bei **vorn** passieren ≈ 22° davon schon 0,3 s **vor** dem Bremsfenster, in der weichen Anbremsphase (a_x ≈ −0,5 m/s²). Mit Bezug auf den Bremsbeginn (alte Auswertung: 15°) war das unterschlagen. Das Handy am Bauch kann zusätzlich mit dem Weichteilgewebe (Bauchfalte beim Vorbeugen) kippen. |
| Gyro-Lotrichtung | Fehler der Vertikalen in der Rollphase 1,5–2,3° (max. 4,8°) | Gyro-Integration über ≤ 6 s ohne nennenswerte Drift | ✅ entspricht ≤ 0,4 m/s² Einstreuung, die der Baseline-Abzug (−0,02 bis −0,15 m/s²) auffängt |

### Interpretation / Diskussionspunkte
- **Hauptbefund:** In der **neutralen** Position ist die mittlere Verzögerung am größten (≈ +8 % gegenüber Vorne). Der Gesamttest ist signifikant (p = 0,034), der Paarvergleich Vorne–Neutral nur grenzwertig (p = 0,037–0,063, je nach Verfahren). Formulierung fürs Poster: „Tendenz, großer Effekt (d = 1,1)“, nicht „eindeutig“.
- **Hypothese H1 nicht bestätigt:** Die Hinten-Position erreicht keine höhere ā. Nach hinten verlagert, steigt zwar die theoretische Überschlaggrenze. Da ā aber in allen Positionen bei ≈ 0,5 g und damit unter dieser Grenze liegt, begrenzt eher die Bremsdosierung des Fahrers als die Physik.
- **Vorne:** Die Verzögerung baut sich am langsamsten auf (Fig. 3). Plausibel ist eine vorsichtigere Dosierung der Vorderradbremse, weil der KSP nahe an der Überschlaggrenze liegt (vgl. Wilson & Schmidt).
- **Rumpfneigung:** Vorn (38°) und hinten (44°) kippt der Rumpf ähnlich stark nach vorn (n.s.), neutral nur ≈ 16°. Vorn beginnt die Bewegung schon vor dem eigentlichen Bremsfenster, hinten erst währenddessen.
- **Hinten:** Der Rumpf kippt beim Bremsen um ≈ 44° nach vorn. Bei ≈ 0,3 s bewegt er sich relativ zum Rad nach vorn, deshalb sinkt die gemessene Verzögerung kurz ab (Einbruch in Fig. 3). Danach fangen die Arme den Rumpf ab, und es folgt ein Spitzenwert. Über den gesamten Stopp gleicht sich das aus (gleicher Impuls).
- **Störgrößen:**
  - (1) v₀ war nicht konstant (20–24 km/h). Bremsdauer und Bremsweg hängen stark davon ab (r = 0,76 bzw. 0,89) und sind deshalb **nicht** als Positionseffekt interpretierbar. ā korreliert kaum mit v₀ (r = −0,18).
  - (2) Die Positionen wurden **geblockt** aufgenommen (Vorne 14:51–15:05 → Neutral → Hinten 15:23–15:33). Übungs- und Ermüdungseffekte lassen sich daher nicht von der Position trennen. Das Vorne-v₀ ist am höchsten, weil diese Trials zuerst gefahren wurden.
- **Limitationen:**
  - n = 1 Proband; die Trials sind Wiederholungen, keine unabhängige Stichprobe.
  - Das Handy am Bauch misst den Rumpf und ist damit nur eine Näherung des KSP.
  - Die Geschwindigkeit wurde nicht kontrolliert, die Reihenfolge nicht randomisiert.
  - Die Gyro-Integration ist nur über wenige Sekunden driftarm.

## Zusatzabbildungen (ergänzen Fig 2–4)
`python analysis/extra_figures.py`. Fig 2–4 bleiben unverändert.

| Datei | Inhalt | Lesehilfe |
|---|---|---|
| `Fig5_Raincloud_Schaetzung.png` | ā je Position als Dichte, Box und Einzelwerte; dazu die Differenz zu „vorn“ mit 95-%-KI nach Welch (ein Perzentil-Bootstrap wäre bei n = 10 zu schmal) | neutral − vorn = +0,44 m/s² [+0,07; +0,80], hinten − vorn = +0,09 [−0,26; +0,44]. Das KI ist **nicht** für Mehrfachvergleiche korrigiert, entspricht also Tukey (p = 0,037) und nicht Mann-Whitney mit Bonferroni (p = 0,063). |
| `Fig6_Heatmap_Trials.png` | alle 30 a_x(t)-Verläufe, nach Uhrzeit sortiert; Strich = Ende Bremsfenster, Raute = v_Rumpf = 0 | Der Einbruch bei hinten (≈ 0,3–0,5 s) ist in praktisch allen Trials sichtbar. In 26/30 Trials erreicht v_Rumpf = 0 im Mittel 0,06 s vor dem Fensterende (vorn/neutral: v ≈ −0,4 bis −0,5 m/s am Fensterende). Das Fensterende enthält also schon den Rückschwung des Rumpfs; die Sensitivitätsanalyse ā' = v₀/t_Stopp bestätigt trotzdem dieselbe Reihenfolge. Farbflecken nach dem Stopp sind Rumpfschwingungen, keine Bremsung. |
| `Fig7_Phasenportraet.png` | Verzögerung über der Geschwindigkeit (v₀ → 0), Einzeltrials und Mittel in 1-km/h-Klassen (nur Klassen mit ≥ 5 Trials) | Die Wellen sind die Rumpfschwingung (≈ 3–4 Hz). Unter ≈ 3 km/h wird das Signal unruhig (Stillstand, Abstützen). |
| `Fig8_gg_Diagramm.png` | Quer- gegen Längsbeschleunigung im Bremsfenster [g], mit Reifenhaftkreis (0,7–0,8 g) und Überschlaggrenze (0,55–0,65 g) | Die Trial-Mittel (ā = 0,42–0,59 g) liegen knapp unterhalb bzw. am unteren Rand der Überschlaggrenze. Das Band ist für alle Positionen gleich; eine Verschiebung der Rumpfmasse ändert die Grenze nur um ≈ ±0,03 g. Anteil der Rumpf-Samples über μg: 16 % (vorn), 30 % (neutral), 26 % (hinten). Die Spitzen des Rumpfsignals reichen über beide Grenzen hinaus, sind also kein KSP-Wert. Die Querbeschleunigung ist ≈ 0, wie bei einer geraden Bremsung zu erwarten. |
| `Fig9_Rumpf_Animation.gif` (+ Standbild) | Mittel je Position: Rumpfneigung und a_x, Zeitlupe 0,5× | **Die Haltung in der Rollphase ist schematisch** (vorn 30°, neutral 15°, hinten −15° zur Senkrechten). Gemessen ist nur die Neigungsänderung Δθ gegenüber der Rollphase. Nur zur Veranschaulichung, nicht für Kennwerte verwenden. **Stoppie:** Das Handy am Bauch misst Rumpf- und Radnicken zusammen, ein Stoppie ist aus den Daten allein nicht eindeutig erkennbar. Die vertikalen Stöße > 1 g (`stoss_nach_g` in `results_trials.csv`, 11/30 Trials) liegen 0,3–1,0 s **nach** dem Stillstand, also nach dem Rumpfmaximum. Der Bereich nach Stillstand ist in der Animation grau bzw. blass markiert. Ein abhebendes Hinterrad (10–30 cm bei ≈ 1,2 m Radstand) würde das Handy um ≈ 5–14° zusätzlich kippen. Trials mit Stoß > 1 g haben aber praktisch die gleiche max. Rumpfneigung (vorn 38 vs. 38°, hinten 44 vs. 44°). Bekannte Stoppie-Trials in `STOPPIE` (`analysis/run_analysis.py`) eintragen: Sie werden dann in Fig 9 ausgeschlossen, und `stats.txt` enthält eine Sensitivitätsanalyse. |

## Struktur
- `analysis/io_phyphox.py`: robustes CSV-Einlesen (Komma/Tab, Dezimalpunkt/-komma)
- `analysis/brake_pipeline.py`: Signalverarbeitung pro Trial
- `analysis/run_analysis.py`: Batch, Statistik, Abbildungen
- `analysis/diag_plot.py`: Kontrollplot aller Trials
- `analysis/extra_figures.py`: Zusatzabbildungen Fig 5–9
- `codex_legacy/`: alte Codex-Skripte (nicht verwenden, siehe PRD §3)
- `files/`: Rohdaten phyphox
