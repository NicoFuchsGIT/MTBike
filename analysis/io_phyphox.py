"""Robustes Einlesen von phyphox-CSV (Komma- oder Tab-getrennt, Dezimalpunkt oder -komma)."""
import numpy as np
import pandas as pd


def read_phyphox(path):
    with open(path, encoding="utf-8") as f:
        header = f.readline()
    sep = "\t" if "\t" in header else ","
    df = pd.read_csv(path, sep=sep, dtype=str)
    arr = df.apply(lambda c: pd.to_numeric(c.str.replace(",", ".", regex=False), errors="coerce"))
    arr = arr.dropna().to_numpy(float)
    t = arr[:, 0]
    # doppelte/rückläufige Zeitstempel (phyphox-Startartefakt) entfernen
    keep = np.r_[True, np.diff(t) > 0]
    return t[keep], arr[keep, 1:4]
