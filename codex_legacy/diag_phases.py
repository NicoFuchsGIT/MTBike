"""Compare event-segmentation vs signed-longitudinal brake detection."""
import os
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks

base = r"C:\Users\nico2\Desktop\Mountainbike\extracted"
fc_high, fc_low = 0.5, 8.0
tail_cut_sec = 1.5
event_thr = 3.0  # m/s^2
min_quiet = 0.6  # s of roll/stabilize between accel and brake
min_event = 0.08  # s


def load_trial(folder):
    path = os.path.join(base, folder, "Accelerometer.csv")
    df = pd.read_csv(path)
    t = df.iloc[:, 0].to_numpy(dtype=float)
    ax = df.iloc[:, 1].to_numpy(dtype=float)
    ay = df.iloc[:, 2].to_numpy(dtype=float)
    az = df.iloc[:, 3].to_numpy(dtype=float)
    mask = (t > 0) & np.isfinite(t) & np.isfinite(ax) & np.isfinite(ay) & np.isfinite(az)
    t, ax, ay, az = t[mask], ax[mask], ay[mask], az[mask]
    dt = float(np.median(np.diff(t)))
    t_u = np.arange(t[0], t[-1], dt)
    ax = np.interp(t_u, t, ax)
    ay = np.interp(t_u, t, ay)
    az = np.interp(t_u, t, az)
    return t_u, ax, ay, az, 1.0 / dt


def lin(folder):
    t, ax, ay, az, fs = load_trial(folder)
    nyq = fs / 2
    b_hp, a_hp = butter(2, fc_high / nyq, "high")
    b_lp, a_lp = butter(4, fc_low / nyq, "low")
    axl = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, ax))
    ayl = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, ay))
    azl = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, az))
    mag = np.sqrt(axl**2 + ayl**2 + azl**2)
    cut = max(1, len(t) - int(tail_cut_sec * fs))
    return t, axl, ayl, azl, mag, cut, fs


def regions(mask):
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return []
    breaks = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[breaks + 1]]
    ends = np.r_[idx[breaks], idx[-1]]
    return list(zip(starts.tolist(), ends.tolist()))


folders = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
positions = ["Vorne", "Neutral", "Hinten"]

print(f"{'pos':8} {'trial':26} {'t_acc':6} {'t_brk':6} {'a_acc':6} {'a_fwd_brk':8} {'a_mag_brk':8} {'n_ev'}")
summary = {p: [] for p in positions}

for pos in positions:
    for tr in [f for f in folders if pos.lower() in f.lower()]:
        t, axl, ayl, azl, mag, cut, fs = lin(tr)
        mag_v = mag[:cut]
        evs = [(s, e) for s, e in regions(mag_v > event_thr) if (e - s) / fs >= min_event]
        # merge events separated by less than min_quiet (same phase)
        merged = []
        for s, e in evs:
            if merged and (s - merged[-1][1]) / fs < min_quiet:
                merged[-1] = (merged[-1][0], e)
            else:
                merged.append((s, e))
        evs = merged
        if len(evs) < 2:
            # fallback: last half max
            mid = len(mag_v) // 2
            bpk = mid + int(np.argmax(mag_v[mid:]))
            apk = int(np.argmax(mag_v[:mid])) if mid > 10 else 0
            acc_s, acc_e = apk, apk
            brk_s, brk_e = bpk, bpk
        else:
            acc_s, acc_e = evs[0]
            brk_s, brk_e = evs[-1]

        acc_pk = acc_s + int(np.argmax(mag_v[acc_s : acc_e + 1]))
        brk_pk = brk_s + int(np.argmax(mag_v[brk_s : brk_e + 1]))

        u = np.array([axl[acc_pk], ayl[acc_pk], azl[acc_pk]])
        nrm = np.linalg.norm(u)
        if nrm < 1e-6:
            a_fwd = np.nan
        else:
            u = u / nrm
            a_long = axl * u[0] + ayl * u[1] + azl * u[2]
            # brake = most negative after accel event
            search = a_long[acc_e:cut]
            imin = acc_e + int(np.argmin(search))
            a_fwd = float(a_long[imin])
            # if signed min is later, use that as brake peak time too
            brk_signed = imin

        print(
            f"{pos:8} {tr:26} {t[acc_pk]:6.2f} {t[brk_pk]:6.2f} {mag_v[acc_pk]:6.1f} "
            f"{a_fwd:8.1f} {mag_v[brk_pk]:8.1f} {len(evs):4}"
        )
        summary[pos].append((mag_v[brk_pk], a_fwd, t[brk_pk], t[acc_pk], t[cut - 1]))

print("\n=== signed brake (min a_long after first event) vs last |a| event ===")
for pos in positions:
    mag = np.array([x[0] for x in summary[pos]])
    fwd = np.array([x[1] for x in summary[pos]])
    tbrk = np.array([x[2] for x in summary[pos]])
    tacc = np.array([x[3] for x in summary[pos]])
    print(
        f"{pos:8} n={len(mag)}  |a|_lastEvent={mag.mean():.2f}?{mag.std(ddof=1):.2f}  "
        f"a_long_min={fwd.mean():.2f}?{fwd.std(ddof=1):.2f}  "
        f"t_acc={tacc.mean():.1f}s  t_brk={tbrk.mean():.1f}s"
    )
