from __future__ import annotations

import numpy as np
from typing import List

from psychchart.psychrometrics import Psychrometrics
from psychchart.config import ChartConfig

from .geometry import PathLayer, Style


def build_saturation_curve(
    cfg: ChartConfig,
    psych: Psychrometrics,
    n: int = 300,
) -> PathLayer:
    """
    Build the saturation (RH=100%) curve as a polyline in (T, W) space.

    Returns
    -------
    PathLayer
        Single path representing the saturation boundary.
    """
    T = np.linspace(cfg.t_min, cfg.t_max, n)

    # saturation humidity ratio (kg/kg)
    W_sat = psych.humidity_ratio_saturation(T)

    # clip to chart domain
    mask = (W_sat >= cfg.y_min) & (W_sat <= cfg.y_max)
    points = [(float(t), float(w)) for t, w in zip(T[mask], W_sat[mask])]

    return PathLayer(
        name="saturation_curve",
        paths=[points],
        style=Style(
            stroke="#000000",
            stroke_width=2.0,
            fill=None,
            zorder=100,
        ),
        meta={"type": "boundary", "rh": 1.0},
    )
def build_relative_humidity_isolines(
    cfg: ChartConfig,
    psych: Psychrometrics,
    levels: List[float],
    n: int = 300,
) -> PathLayer:
    """
    Build relative humidity isolines (e.g. 0.2, 0.4, 0.6).

    Parameters
    ----------
    levels : list of float
        Relative humidity values in [0, 1].
    """
    T = np.linspace(cfg.t_min, cfg.t_max, n)

    paths: List[List[tuple[float, float]]] = []

    for rh in levels:
        W = psych.humidity_ratio_from_rh(T, rh)

        mask = (W >= cfg.y_min) & (W <= cfg.y_max)
        pts = [(float(t), float(w)) for t, w in zip(T[mask], W[mask])]

        if pts:
            paths.append(pts)

    return PathLayer(
        name="relative_humidity",
        paths=paths,
        style=Style(
            stroke="#555555",
            stroke_width=0.8,
            stroke_dasharray="4,4",
            opacity=0.8,
            zorder=20,
        ),
        meta={"type": "isoline", "quantity": "relative_humidity"},
    )

