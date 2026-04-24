"""
Operational zone field generation for psychrometric charts.

This module converts a declarative operational policy into a gridded field
that can be rendered on top of the psychrometric diagram.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .engine import action
from .enums import TrendMode
from .profile import OperationalProfile


@dataclass(frozen=True)
class OperationalZoneField:
    """Curvilinear gridded operational field in psychrometric space."""

    T_grid: np.ndarray
    RH_grid: np.ndarray
    W_grid: np.ndarray
    ITU_grid: np.ndarray
    action_grid: np.ma.MaskedArray
    load_class_name: str
    trend: TrendMode
    representative_ca: float
    representative_dca_dt: float


def representative_dca_dt(
    profile: OperationalProfile,
    trend: TrendMode,
) -> float:
    """Return a representative dCA/dt value for a trend state."""
    if trend is TrendMode.RISING:
        if profile.modifiers.rising_load is not None:
            return profile.modifiers.rising_load.dca_dt_gt + 1e-6
        return 0.002

    if trend is TrendMode.FALLING:
        if profile.modifiers.recovery is not None:
            return profile.modifiers.recovery.dca_dt_lt - 1e-6
        return -0.002

    return 0.0


def build_operational_zone_field(
    *,
    chart_cfg,
    profile: OperationalProfile,
    load_class_name: str,
    trend: TrendMode,
    itu_evaluator: Callable[[np.ndarray, np.ndarray], np.ndarray],
    humidity_ratio_evaluator: Callable[[np.ndarray, np.ndarray], np.ndarray],
    n_t: int = 220,
    n_rh: int = 180,
) -> OperationalZoneField:
    """
    Build a zone field for one accumulated-load class.

    Parameters
    ----------
    chart_cfg:
        Chart configuration object with at least `t_min`, `t_max`, and
        optionally `y_min`, `y_max`.
    profile:
        Declarative operational profile.
    load_class_name:
        Name of the accumulated-load class to project as a static zone map.
    trend:
        Trend state used to choose the representative dCA/dt.
    itu_evaluator:
        Callable that computes ITU on arrays `(T, RH)`.
    humidity_ratio_evaluator:
        Callable that computes humidity ratio `W` on arrays `(T, RH)`.
    n_t, n_rh:
        Grid resolution for T and RH.
    """
    t_values = np.linspace(chart_cfg.t_min, chart_cfg.t_max, n_t)
    rh_values = np.linspace(0.0, 1.0, n_rh)

    T_grid, RH_grid = np.meshgrid(t_values, rh_values)

    ITU_grid = np.asarray(itu_evaluator(T_grid, RH_grid), dtype=float)
    W_grid = np.asarray(humidity_ratio_evaluator(T_grid, RH_grid), dtype=float)

    load_class = profile.get_load_class(load_class_name)
    representative_ca = load_class.representative_value()
    representative_rate = representative_dca_dt(profile, trend)

    raw_actions = np.zeros_like(ITU_grid, dtype=int)

    for i in range(T_grid.shape[0]):
        for j in range(T_grid.shape[1]):
            raw_actions[i, j] = int(
                action(
                    profile,
                    T=float(T_grid[i, j]),
                    RH=float(RH_grid[i, j]),
                    itu=float(ITU_grid[i, j]),
                    ca=representative_ca,
                    dca_dt=representative_rate,
                )
            )

    mask = ~np.isfinite(W_grid)

    y_min = getattr(chart_cfg, "y_min", None)
    y_max = getattr(chart_cfg, "y_max", None)

    if y_min is not None:
        mask |= W_grid < y_min
    if y_max is not None:
        mask |= W_grid > y_max

    action_grid = np.ma.masked_array(raw_actions, mask=mask)

    return OperationalZoneField(
        T_grid=T_grid,
        RH_grid=RH_grid,
        W_grid=W_grid,
        ITU_grid=ITU_grid,
        action_grid=action_grid,
        load_class_name=load_class_name,
        trend=trend,
        representative_ca=representative_ca,
        representative_dca_dt=representative_rate,
    )
