# PRD – Thema 2 „Bremsen“: Einfluss der Körperhaltung auf die KSP-Verzögerung beim E-MTB

**Abgabe:** 15.10.2026 · **Ergebnis:** Poster (FH-Word-Template, Deutsch, IMRAD, ≤ 4 Abbildungen)
**Stand:** 12.10.2026

## 1. Ziel
1. Die negative Beschleunigung (Verzögerung) des Körperschwerpunkts (KSP) beim Bremsen bestimmen (Smartphone + phyphox).
2. Drei Sitzpositionen vergleichen: **Vorne** (nach vorn gelehnt), **Neutral**, **Hinten** (nach hinten gelehnt).

**Forschungsfrage:** Unterscheidet sich die mittlere und maximale KSP-Verzögerung bei einer Vollbremsung aus 20 km/h zwischen den drei Rumpfpositionen?
**Hypothese H1:** Mit nach hinten verlagertem KSP (Hinten) ist eine höhere Verzögerung möglich, weil die Überschlaggrenze (Abheben des Hinterrads) später erreicht wird (vgl. Wilson & Schmidt, 2020).

## 2. Versuchsdesign (fix, so gemessen)
| Parameter | Wert |
|---|---|
| Proband*innen | 1 (Einzelfallanalyse) |
| Bedingungen | 3 Positionen, alle sitzend |
| Wiederholungen | 10 Trials pro Position → N = 30 |
| Bike | modernes E-MTB |
| Ablauf | Beschleunigen auf 20 km/h (≈ 5,56 m/s) → 6 m Rollphase → Vollbremsung bis Stillstand |
| Sensor | Smartphone am Bauch (nahe KSP), phyphox: Accelerometer, Gyroscope, Magnetometer |
| Daten | `extracted/<Position>_<n>/Accelerometer.csv`, `Gyroscope.csv`, `Magnetometer.csv` |

## 3. Was am Codex-Code falsch ist (Gründe für eine Neuauswertung)
| Problem | Folge |
|---|---|
| Kennzahl ist der Betrag `|a_lin|` aller drei Achsen | Ein Betrag hat kein Vorzeichen und mischt vertikale Stöße (Trail, Sattel) in die Messung. Die „Verzögerung“ ist deshalb oft gar keine Bremsung, sondern eine Erschütterung, die dafür gehalten wird. |
| Hochpass 0,5 Hz zum Entfernen der Gravitation | Eine Bremsung dauert etwa 1–1,5 s und ist fast ein Plateau. Der Hochpass schneidet genau dieses Plateau ab, und die mittlere Verzögerung fällt zu niedrig aus. |
| Rumpfneigung wird nicht berücksichtigt | Beim Bremsen kippt der Oberkörper nach vorn. Schon 10° Neigungsänderung lassen ≈ 1,7 m/s² Gravitation in die Längsachse durchsickern. Das betrifft die Positionen systematisch unterschiedlich und ist ein Bias. |
| Kopfzeile sagt 25 km/h, `Bremsphase_Auto.m` setzt fs = 400 Hz fest und zieht g vom Betrag ab | Die Bedingungen sind inkonsistent, die Zeitachse kann falsch sein, und der Betrag minus g hat kein physikalisches Vorzeichen. |
| Keine Plausibilitätsprüfung | Bisher wird nicht geprüft, ob ∫a dt ≈ −5,56 m/s ergibt. |

Brauchbar und daher übernommen: robustes CSV-Einlesen (Dezimalkomma), Resampling auf ein gleichmäßiges Zeitraster, `filtfilt` (ohne Phasenverschiebung), das Ignorieren des Abschalt-Artefakts am Ende und die Idee aus `diag_phases.py`, die Fahrtrichtung aus der Anfahrphase zu bestimmen.

## 4. Auswertemethode (neu, MATLAB oder Python)
1. **Einlesen und Synchronisieren:** Acc (inkl. g), Gyro und Magnetometer auf ein gemeinsames Raster resamplen (fs aus den Zeitstempeln, nicht fest).
2. **Tiefpass:** Butterworth 4. Ordnung, zero-lag, fc ≈ 5 Hz. Begründung: Die KSP-Bewegung ist niederfrequent, Rahmen- und Trailvibrationen liegen höher. Optional mit einer Residualanalyse nach Winter (2009) absichern.
3. **Gravitation entfernen:** Den g-Vektor im Sensorsystem in der Rollphase vor der Bremsung bestimmen (Mittelwert, quasi-statisch). Danach seine Orientierung per Gyro-Integration nachführen. Über ≈ 2 s ist die Drift vernachlässigbar. Ergebnis: `a_lin = a − g(t)`.
4. **Fahrtrichtung:** Horizontaler Anteil von `a_lin` in der Anfahrphase (positiv = vorwärts). Rückfallebene: PCA der horizontalen Beschleunigung während der Bremsung. Das Vorzeichen so wählen, dass Bremsen negativ ist.
5. **Längsbeschleunigung:** `a_x(t) = a_lin · ê_fwd`, mit Vorzeichen, Bremsen < 0.
6. **Bremsfenster:**
   - Beginn: `a_x` fällt nach der Rollphase dauerhaft unter −1 m/s².
   - Ende: `a_x` steigt wieder über −0,5 m/s², bzw. die integrierte Geschwindigkeit erreicht ≈ 0.
7. **Kennwerte pro Trial:**
   - **Primär:** mittlere Verzögerung ā im Bremsfenster [m/s²]
   - **Sekundär:** Spitzenverzögerung a_max [m/s²]; Bremsdauer t_B [s]
   - Bremsweg s_B = v₀·t_B/2 bzw. aus ∫∫a [m]
   - Rumpf-Pitch Δθ aus dem Gyro [°] als Erklärvariable
8. **Validierung:** Δv = ∫a_x dt muss ≈ −5,56 m/s ergeben, Toleranz ±20 %. Trials außerhalb werden markiert und im Poster berichtet. Ausschluss nur mit einem dokumentierten Grund.
9. **Statistik (gemäß BHF3 BIOLB):**
   - Pro Position MW ± SD (n = 10), Stichprobenumfang immer angeben, sinnvolle Nachkommastellen.
   - Normalverteilung mit Shapiro-Wilk prüfen.
   - Einfaktorielle ANOVA, bei verletzter Annahme Kruskal-Wallis.
   - Post-hoc Bonferroni, Effektstärke η² bzw. Cohen's d.
   - Limitation nennen: 1 Proband, Trials sind keine unabhängigen Personen. Die Aussage gilt nur für diesen Fahrer.

## 5. Poster-Abbildungen (max. 4)
| # | Inhalt | Zweck |
|---|---|---|
| 1 | Setup: Foto/Skizze der 3 Positionen, Handy-Lage, Achsen, Ablauf 20 km/h → 6 m → Bremsung | Methode |
| 2 | Beispiel-Trial: roh vs. gefiltert `a_x(t)`, Bremsfenster markiert, Δv-Kurve | Methode/Validierung |
| 3 | Mittlere Bremskurve ± SD-Band je Position, ausgerichtet auf den Bremsbeginn | Ergebnis |
| 4 | Boxplot + Einzelpunkte: ā (und a_max) je Position, Signifikanz-Markierung | Ergebnis |

Jede Abbildung bekommt eine aussagekräftige Bildunterschrift. Die Schrift muss auf A0 lesbar sein (≥ 14 pt im Export). Plots in MATLAB mit `theme('light')`, Export als 300-dpi-PNG.

## 6. Liefergegenstände
- `analysis/` – Auswerteskript (ein Einstiegspunkt) + `results.csv` (Trial-Ebene) + `summary.csv`
- `figures/` – Fig2–Fig4 als PNG
- `poster/` – Texte nach IMRAD (DE) + ausgefülltes Word-Template
- Literaturverzeichnis (APA). Kandidaten, vor Verwendung prüfen:
  - Staacks, S., Hütz, S., Heinke, H. & Stampfer, C. (2018). Advanced tools for smartphone-based experiments: phyphox. *Physics Education, 53*(4), 045009.
  - Wilson, D. G. & Schmidt, T. (2020). *Bicycling Science* (4th ed.). MIT Press.
  - Winter, D. A. (2009). *Biomechanics and Motor Control of Human Movement* (4th ed.). Wiley.
  - 1–2 Paper zu Bremsverhalten/Fahrerposition beim (Mountain-)Bike, noch zu recherchieren

## 7. Akzeptanzkriterien
- [ ] Alle 30 Trials laufen automatisch durch, und jeder Ausschluss ist begründet.
- [ ] Δv-Check liegt für ≥ 80 % der Trials innerhalb ±20 % von 5,56 m/s.
- [ ] Die Kennwerte sind physikalisch plausibel (ā typ. 3–7 m/s², < 1 g).
- [ ] Tabelle mit MW ± SD, n und Testergebnis.
- [ ] Poster: IMRAD, ≤ 4 Abbildungen mit Bildunterschrift, Literatur referenziert, FH-Template.

## 8. Risiken
| Risiko | Gegenmaßnahme |
|---|---|
| Daten „blurry“ (Handy wackelt am Bauch) | Tiefpass, Kennwert auf ā statt Peak stützen, Δv-Validierung |
| Keine Anfahrphase in der Aufnahme | PCA-Fallback für die Fahrtrichtung |
| Gyro/Acc unterschiedlich abgetastet | gemeinsames Resampling |
| Zeitdruck (3 Tage) | Figure 1 als Skizze/Foto statt aufwendiger Grafik; Statistik minimal halten |

## 9. Out of Scope
Mehrere Proband*innen, stehende Positionen, Sensorfusion mit Magnetometer (nur falls der Gyro allein nicht reicht), Bremsweg-Messung per Maßband.
