"""Bremsanalyse MTB: KSP-Längsverzögerung aus phyphox-IMU (Acc + Gyro).

Methode
1. Acc und Gyro auf gemeinsames Raster, Butterworth-Tiefpass (zero-lag).
2. Stillstand nach der Bremsung finden (ruhigstes 0,4-s-Fenster) -> Gravitationsvektor
   g_end im Sensorsystem (kein Gyro-Bias-Abzug, siehe to_stop_frame).
3. Orientierung per Gyro-Integration rückwärts ab Stillstand -> jede Probe ins
   'Stillstands-Weltsystem' drehen; dort ist die Vertikale bekannt.
4. Lineare Beschleunigung = a_welt - g; horizontale Hauptrichtung (PCA) in den
   Sekunden vor dem Stillstand = Fahrtrichtung; Vorzeichen: Bremsen < 0.
5. Bremsfenster: a_x (2 Hz) < -1 m/s² um das stärkste 0,5-s-Plateau; Baseline aus der
   Rollphase abgezogen. ā = Mittel im Fenster, Peak = Minimum im Fenster.
   v0 = Integral a_x dt von Bremsbeginn bis Stillstand. Validierung: v0 ~ 5,56 m/s (20 km/h).
"""
import glob
import os
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.spatial.transform import Rotation as Rot

from io_phyphox import read_phyphox

G = 9.81
V0 = 20 / 3.6
FC_ACC = 5.0       # Hz, KSP-Bewegung
FC_GYR = 10.0      # Hz
TAIL_CUT = 1.0     # s, Handy-Entnahme am Ende ignorieren
STILL_WIN = 0.4    # s, Fensterlänge Stillstandserkennung


def lowpass(x, fc, fs, order=4):
    b, a = butter(order, fc / (fs / 2))
    return filtfilt(b, a, x, axis=0)


def moving_std(x, n):
    k = np.ones(n) / n
    m = np.convolve(x, k, "same")
    return np.sqrt(np.maximum(np.convolve(x**2, k, "same") - m**2, 0))


def load(folder):
    ta, a = read_phyphox(os.path.join(folder, "Accelerometer.csv"))
    tg, w = read_phyphox(os.path.join(folder, "Gyroscope.csv"))
    dt = np.median(np.diff(ta))
    t = np.arange(max(ta[0], tg[0]), min(ta[-1], tg[-1]), dt)
    a = np.column_stack([np.interp(t, ta, a[:, i]) for i in range(3)])
    w = np.column_stack([np.interp(t, tg, w[:, i]) for i in range(3)])
    return t, a, w, 1 / dt


def coarse_brake_candidates(t, a, fs, n_max=4, min_sep=1.5):
    """Kandidaten für die Bremsung: lokale Maxima der niederfrequenten Abweichung
    der Beschleunigung von der mittleren Gravitationsrichtung während der Fahrt."""
    T = t[-1]
    g_pre = np.median(a[t < t[0] + 0.6 * (T - t[0])], axis=0)
    d = np.linalg.norm(lowpass(a, 1.0, fs) - g_pre, axis=1)
    cand = np.flatnonzero((t > t[0] + 0.3 * (T - t[0])) & (t < T - TAIL_CUT))
    out = []
    for i in cand[np.argsort(d[cand])[::-1]]:
        if all(abs(t[i] - t[j]) > min_sep for j in out):
            out.append(i)
        if len(out) == n_max:
            break
    return out


def quiet_window(t, a_f, w_f, fs, t_from, t_to):
    """Ruhigstes STILL_WIN-Fenster (Fahrer steht, Handy noch am Bauch)."""
    n = int(STILL_WIN * fs)
    cost = moving_std(np.linalg.norm(a_f, axis=1), n) + \
        np.convolve(np.linalg.norm(w_f, axis=1), np.ones(n) / n, "same")
    rng = np.flatnonzero((t > t_from) & (t < min(t_to, t[-1] - TAIL_CUT - STILL_WIN / 2)))
    if rng.size == 0:
        return None
    c = rng[np.argmin(cost[rng])]
    return c - n // 2, c + n // 2


def to_stop_frame(a_f, w_f, i0, i1, fs, n_back):
    """Dreht Proben [i0-n_back, i0] ins Sensorsystem zum Stillstandszeitpunkt i0
    (Gyro-Integration rückwärts). Kein Bias-Abzug: im kurzen Ruhefenster
    dominiert Körperschwanken (~0,1-0,2 rad/s) den echten Gyro-Offset (<0,01 rad/s)."""
    k0 = max(0, i0 - n_back)
    dR = Rot.from_rotvec(w_f[k0:i0] / fs)
    R = [Rot.identity()]
    for k in range(i0 - k0 - 1, -1, -1):
        # R(k+1) = R(k) * exp(w_k dt)  ->  R(k) = R(k+1) * exp(w_k dt)^-1
        R.append(R[-1] * dR[k].inv())
    R = Rot.concatenate(R[::-1])
    return k0, R


def analyze(folder):
    """Wertet alle Kandidaten aus und wählt das deutlichste Bremsplateau
    (größte mittlere Verzögerung bei Bremsdauer >= 0,5 s)."""
    t, a, w, fs = load(folder)
    a_f = lowpass(a, FC_ACC, fs)
    w_f = lowpass(w, FC_GYR, fs)
    best = None
    for ic in coarse_brake_candidates(t, a, fs):
        r = analyze_at(folder, t, a_f, w_f, fs, ic)
        if r is None or r["dur"] < 0.5:
            continue
        if best is None or r["mean"] > best["mean"]:
            best = r
    return best


def analyze_at(folder, t, a_f, w_f, fs, ic):
    q = quiet_window(t, a_f, w_f, fs, t[ic] + 0.3, t[ic] + 3.5)
    if q is None:
        return None
    i0, i1 = q
    g_end = a_f[i0:i1].mean(0)
    k0, R = to_stop_frame(a_f, w_f, i0, i1, fs, int(6 * fs))
    a_w = R.apply(a_f[k0:i0 + 1])
    w_w = R.apply(w_f[k0:i0 + 1])
    tt = t[k0:i0 + 1]
    ez = g_end / np.linalg.norm(g_end)
    a_lin = a_w - g_end
    a_v = a_lin @ ez
    a_h = a_lin - np.outer(a_v, ez)

    # Fahrtrichtung = Hauptachse der horizontalen Beschleunigung 3 s vor Ruhe
    m = tt > tt[-1] - 3.0
    _, _, vt = np.linalg.svd(a_h[m] - a_h[m].mean(0), full_matrices=False)
    a_x = a_h @ vt[0]
    n05 = int(0.5 * fs)
    ma = np.convolve(a_x, np.ones(n05) / n05, "same")
    if -ma[m].min() < ma[m].max():   # Vorzeichen: Bremsplateau negativ
        a_x, ma = -a_x, -ma
        vt[0] = -vt[0]
    ex = vt[0]
    ic2 = np.flatnonzero(m)[np.argmin(ma[m])]

    # Bremsfenster am 2-Hz-Signal: solange a_x < -1 m/s²
    a_d = lowpass(a_x, 2.0, fs)
    thr = -1.0
    st = ic2
    while st > 0 and a_d[st] < thr:
        st -= 1
    en = ic2
    while en < len(a_d) - 1 and a_d[en] < thr:
        en += 1
    # Baseline (Rollphase vor Bremsbeginn, konstante Geschwindigkeit -> a≈0)
    pre = (tt > tt[st] - 1.0) & (tt < tt[st] - 0.1)
    base = a_x[pre].mean() if pre.any() else 0.0
    a_c = a_x - base
    win = slice(st, en + 1)
    ip = st + np.argmin(a_c[win])
    dv = np.trapezoid(a_c[win], tt[win])   # Δv nur im Fenster (Konsistenz: ā·t_B)
    # Geschwindigkeit rückwärts vom Stillstand integriert (v = 0 im Ruhefenster):
    # schließt den Rückschwung des Rumpfs nach dem Fenster ein -> unverzerrtes v0
    seg = (a_c[1:] + a_c[:-1]) / 2 / fs
    v = np.concatenate([-np.cumsum(seg[::-1])[::-1], [0.0]])
    after = np.flatnonzero(v[st:] <= 0)
    ks = st + (after[0] if after.size else len(v) - 1 - st)   # erster Nulldurchgang
    # Rumpf-Nickwinkel: Drehung um die Querachse (ey = ez x ex), + = nach vorn
    ey = np.cross(ez, ex)
    a_y = a_h @ ey                         # Querbeschleunigung (für g-g-Diagramm)
    a_y = a_y - (a_y[pre].mean() if pre.any() else 0.0)
    pitch = np.degrees(np.cumsum(w_w @ ey) / fs)
    # Bezug = Rollphase (1,0-0,6 s vor Bremsbeginn), nicht der Bremsbeginn selbst:
    # bei 'Vorne' kippt der Rumpf bereits ~20° in der weichen Anbremsphase davor
    roll = (tt > tt[st] - 1.0) & (tt < tt[st] - 0.6)
    pitch -= pitch[roll].mean() if roll.any() else pitch[st]
    return dict(
        name=os.path.basename(folder), position=os.path.basename(folder).split()[0],
        fs=fs, t=tt, a_x=a_c, a_y=a_y, a_v=a_v, t_rel=tt - tt[st],
        t_start=tt[st], t_end=tt[en], t_peak=tt[ip], t_quiet=tt[-1],
        peak=-a_c[ip], mean=-a_c[win].mean(), dur=tt[en] - tt[st],
        dv=dv, v=v, v0=v[st], t_stop=tt[ks] - tt[st],
        dist=np.trapezoid(v[st:ks + 1], tt[st:ks + 1]),
        t_to_peak=tt[ip] - tt[st], pitch=pitch, pitch_max=pitch[win].max(),
        pitch_min=pitch[win].min(), baseline=base,
    )


if __name__ == "__main__":
    for d in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "files", "*"))):
        r = analyze(d)
        if r is None:
            print(os.path.basename(d), "kein Stillstand gefunden")
            continue
        print(f"{r['name']:24} end={r['t_end']:5.2f} start={r['t_start']:5.2f} dur={r['dur']:.2f} "
              f"peak={r['peak']:5.2f} mean={r['mean']:5.2f} dv={r['dv']:6.2f}")
