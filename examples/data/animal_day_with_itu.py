from __future__ import annotations

import pandas as pd


def compute_itu(temp_c: pd.Series, rh: pd.Series) -> pd.Series:
    """
    Compute Temperature-Humidity Index (ITU / THI).

    Parameters
    ----------
    temp_c : pd.Series
        Air temperature in degrees Celsius.
    rh : pd.Series
        Relative humidity either as fraction [0, 1] or percent [0, 100].

    Returns
    -------
    pd.Series
        ITU values.
    """
    rh_pct = rh.copy().astype(float)
    if rh_pct.max() <= 1.0:
        rh_pct = rh_pct * 100.0

    t = temp_c.astype(float)
    return (1.8 * t + 32.0) - (0.55 - 0.0055 * rh_pct) * (1.8 * t - 26.8)


df = pd.read_csv("examples/data/animal_day.csv")

df["itu"] = compute_itu(df["temp"], df["rh"])

df.to_csv("examples/data/animal_day_with_itu.csv", index=False)

print("OK -> examples/data/animal_day_with_itu.csv")
print(df.head())
