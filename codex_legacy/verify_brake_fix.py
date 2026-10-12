"""Verify corrected CoM-deceleration logic (matches FINAL_Brems_Analyse.m)."""
import os
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

base = r"C:\Users\nico2\Desktop\Mountainbike\extracted"
fc_high, fc_low = 0.5, 8.0
tail_cut_sec = 1.5
threshold_ratio = 0.20
abs_threshold = 2.0


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


def analyze(folder):
    t, ax, ay, az, fs = load_trial(folder)
    nyq = fs / 2
    b_hp, a_hp = butter(2, fc_high / nyq, "high")
    b_lp, a_lp = butter(4, fc_low / nyq, "low")
    ax_lin = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, ax))
    ay_lin = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, ay))
    az_lin = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, az))
    a_lin = np.sqrt(ax_lin**2 + ay_lin**2 + az_lin**2)
    cut = max(1, len(t) - int(tail_cut_sec * fs))
    a_valid = a_lin[:cut]
    peak_idx = int(np.argmax(a_valid))
    peak = float(a_valid[peak_idx])
    thr = max(abs_threshold, threshold_ratio * peak)
    start = peak_idx
    while start > 0 and a_valid[start] > thr:
        start -= 1
    end = peak_idx
    while end < len(a_valid) - 1 and a_valid[end] > thr:
        end += 1
    duration = float(t[end] - t[start])
    return peak, duration, float(np.mean(a_valid[start : end + 1]))


def old_algorithm(folder):
    """Reproduce the original FINAL_Brems_Analyse bug for contrast."""
    path = os.path.join(base, folder, "Accelerometer.csv")
    df = pd.read_csv(path)
    ax = df.iloc[:, 1].to_numpy(dtype=float)
    ay = df.iloc[:, 2].to_numpy(dtype=float)
    az = df.iloc[:, 3].to_numpy(dtype=float)
    mag = np.sqrt(ax**2 + ay**2 + az**2)
    fs = 400.0
    t = np.arange(len(mag)) / fs
    b_hp, a_hp = butter(2, 0.5 / (fs / 2), "high")
    b_lp, a_lp = butter(4, 20 / (fs / 2), "low")
    mag_f = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, mag))
    mask = mag_f < -0.5
    if not mask.any():
        return np.nan, np.nan
    idx = np.where(mask)[0]
    duration = float(t[idx[-1]] - t[idx[0]])
    mean_decel = float(abs(np.mean(mag_f[mask])))
    return duration, mean_decel


folders = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
positions = ["Vorne", "Neutral", "Hinten"]

print("OLD algorithm (first trial only): high-pass of |a|, then a < -0.5")
for pos in positions:
    trial = next(f for f in folders if pos.lower() in f.lower())
    dur, mean_d = old_algorithm(trial)
    print(f"  {pos:8} duration={dur:.2f}s  mean_decel={mean_d:.2f}  trial={trial}")

print("\nNEW algorithm (all trials): per-axis gravity removal, peak of |a_lin|")
summary = {}
for pos in positions:
    trials = [f for f in folders if pos.lower() in f.lower()]
    rows = [analyze(tr) for tr in trials]
    peaks = np.array([r[0] for r in rows])
    durs = np.array([r[1] for r in rows])
    summary[pos] = {"n": len(rows), "peak_mean": peaks.mean(), "dur_mean": durs.mean()}
    print(
        f"  {pos:8} n={len(rows)}  max_decel={peaks.mean():.2f}?{peaks.std(ddof=1):.2f}  "
        f"duration={durs.mean():.3f}s"
    )

# Old bug: brake window spanned almost the whole recording (~15?21 s)
# and mean deceleration was nearly identical across positions.
for pos in positions:
    trial = next(f for f in folders if pos.lower() in f.lower())
    dur_old, _ = old_algorithm(trial)
    assert dur_old > 10.0, f"expected old window to be huge, got {dur_old}"

assert all(summary[p]["dur_mean"] < 2.0 for p in positions), "new brake window still too long"
assert all(summary[p]["dur_mean"] > 0.05 for p in positions), "new brake window collapsed"
vals = [summary[p]["peak_mean"] for p in positions]
assert max(vals) - min(vals) > 1.0, "positions still look identical"
print("\nCHECKS PASSED.")
