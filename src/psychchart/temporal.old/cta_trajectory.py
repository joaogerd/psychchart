from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
import numpy as np


CTA_COLOR_RULES = (
    (22.4, "green", "Recovery"),
    (83.6, "orange", "Alert"),
    (165.2, "darkorange", "Critical"),
    (np.inf, "red", "Fatigue"),
)


def classify_cta_to_color(cta: float) -> str:
    """
    Map accumulated thermal load (CTA) to marker color.
    """
    cta = float(cta)
    for upper, color, _label in CTA_COLOR_RULES:
        if cta < upper:
            return color
    return "red"


def classify_cta_to_label(cta: float) -> str:
    """
    Map accumulated thermal load (CTA) to a semantic class label.
    """
    cta = float(cta)
    for upper, _color, label in CTA_COLOR_RULES:
        if cta < upper:
            return label
    return "Fatigue"


@dataclass(frozen=True)
class CTATrajectoryResult:
    """
    Fully prepared temporal trajectory, ready for psychrometric plotting.
    """
    data: pd.DataFrame
    t_col: str
    rh_col: str
    time_col: str
    cta_col: str
    color_col: str = "_cta_color"
    class_col: str = "_cta_class"


def build_cta_trajectory(
    df: pd.DataFrame,
    *,
    t_col: str,
    rh_col: str,
    time_col: str,
    cta_col: str,
    sort: bool = True,
) -> CTATrajectoryResult:
    """
    Prepare a temporal trajectory colored by CTA.

    Parameters
    ----------
    df : pandas.DataFrame
        Input trajectory table.
    t_col, rh_col, time_col, cta_col : str
        Required column names.
    sort : bool, optional
        Whether to sort by the time column before drawing.

    Returns
    -------
    CTATrajectoryResult
        Processed result ready for plotting.
    """
    out = df.copy()

    required = {t_col, rh_col, time_col, cta_col}
    missing = required.difference(out.columns)
    if missing:
        raise ValueError(
            f"CTA trajectory missing required columns: {sorted(missing)}"
        )

    if sort:
        out = out.sort_values(time_col)

    out["_cta_color"] = out[cta_col].map(classify_cta_to_color)
    out["_cta_class"] = out[cta_col].map(classify_cta_to_label)

    return CTATrajectoryResult(
        data=out,
        t_col=t_col,
        rh_col=rh_col,
        time_col=time_col,
        cta_col=cta_col,
    )
