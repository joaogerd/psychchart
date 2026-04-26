"""
Renderer for operational cooling zones.

This layer draws explicit operational policy fields over the psychrometric
space without mixing operational recommendations into the core index logic.
"""

from __future__ import annotations

from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

from psychchart.config.operations import OperationalOverlayConfig
from psychchart.indexes.itu import ITU
from psychchart.operations.management_engine import (
    ACTIONS,
    action_colors,
    action_labels,
    classify_management,
)
from psychchart.psychrometrics import Psychrometrics


def _default_itu_evaluator(T: np.ndarray, RH: np.ndarray) -> np.ndarray:
    """Evaluate ITU on array inputs using the canonical ITU implementation."""
    return ITU.compute_vectorized({"T": T, "RH": RH})


def _wrap_humidity_ratio_candidate(
    candidate: Callable,
    pressure: float,
) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """Wrap supported humidity-ratio call signatures into ``f(T, RH)``."""

    def evaluator(T: np.ndarray, RH: np.ndarray) -> np.ndarray:
        try:
            return candidate(T, RH, pressure)
        except TypeError:
            return candidate(T, RH)

    return evaluator


def _resolve_humidity_ratio_evaluator(
    chart,
) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """Resolve a humidity-ratio evaluator from the live chart object."""
    pressure = getattr(getattr(chart, "cfg", None), "pressure", 101325.0)
    candidates = []

    psychro = getattr(chart, "psychrometrics", None)
    if psychro is not None:
        candidates.extend(
            [
                getattr(psychro, "humidity_ratio_from_rh", None),
                getattr(psychro, "get_humidity_ratio_from_rh", None),
                getattr(psychro, "w_from_t_rh", None),
                getattr(psychro, "humidity_ratio", None),
            ]
        )

    chart_psychro = getattr(chart, "psych", None)
    if chart_psychro is not None:
        candidates.extend(
            [
                getattr(chart_psychro, "humidity_ratio_from_rh", None),
                getattr(chart_psychro, "get_humidity_ratio_from_rh", None),
                getattr(chart_psychro, "w_from_t_rh", None),
                getattr(chart_psychro, "humidity_ratio", None),
            ]
        )

    candidates.append(Psychrometrics.humidity_ratio)

    for candidate in candidates:
        if callable(candidate):
            return _wrap_humidity_ratio_candidate(candidate, pressure)

    raise AttributeError(
        "Could not resolve a humidity-ratio evaluator from chart. "
        "Expected a callable equivalent to "
        "Psychrometrics.humidity_ratio(T, RH, pressure)."
    )


def _trend_name(value: str) -> str:
    """Normalize trend names from configuration values."""
    return str(value).lower()


def _representative_cta(chart, cfg: OperationalOverlayConfig) -> float:
    """
    Resolve representative CTA from overlay load class.

    The interactive overlay uses a static psychrometric field. Since a true CTA
    is temporal, this value represents the selected accumulated-load class for
    the whole field. It keeps the operational surface explicitly tied to load
    class while avoiding hidden time integration inside the renderer.
    """
    profile_name = getattr(cfg, "profile", "default")
    load_class = getattr(cfg, "load_class", "A2")
    profiles = getattr(chart, "operational_profiles", {}) or {}
    profile_cfg = profiles.get(profile_name)

    if profile_cfg is not None:
        try:
            runtime = profile_cfg.to_runtime()
            return float(runtime.get_load_class(load_class).representative_value())
        except Exception:
            pass

    fallback = {
        "A0": 0.0,
        "A1": 10.0,
        "A2": 30.0,
        "A3": 60.0,
        "A4": 90.0,
    }
    return fallback.get(str(load_class), 30.0)


def _build_management_field(
    chart,
    cfg: OperationalOverlayConfig,
):
    """Build a management-action field over the psychrometric domain."""
    n_t = int(getattr(cfg, "n_t", 220))
    n_rh = int(getattr(cfg, "n_rh", 180))

    t_values = np.linspace(chart.cfg.t_min, chart.cfg.t_max, n_t)
    rh_values = np.linspace(0.0, 1.0, n_rh)
    T_grid, RH_grid = np.meshgrid(t_values, rh_values)

    humidity_ratio_evaluator = _resolve_humidity_ratio_evaluator(chart)
    W_grid = np.asarray(humidity_ratio_evaluator(T_grid, RH_grid), dtype=float)
    ITU_grid = np.asarray(_default_itu_evaluator(T_grid, RH_grid), dtype=float)

    CTA_grid = np.full_like(ITU_grid, _representative_cta(chart, cfg), dtype=float)
    action_grid = classify_management(
        T_grid,
        RH_grid,
        ITU_grid,
        CTA_grid,
        trend=_trend_name(getattr(cfg, "trend", "steady")),
    )

    mask = ~np.isfinite(W_grid)
    y_min = getattr(chart.cfg, "y_min", None)
    y_max = getattr(chart.cfg, "y_max", None)
    if y_min is not None:
        mask |= W_grid < y_min
    if y_max is not None:
        mask |= W_grid > y_max

    return T_grid, W_grid, np.ma.masked_array(action_grid, mask=mask)


def _build_action_colormap():
    """Build categorical colormap and norm for management actions."""
    colors = action_colors()
    ordered_codes = [action.code for action in ACTIONS]
    cmap = ListedColormap([colors[code] for code in ordered_codes])
    levels = np.arange(-0.5, len(ordered_codes) + 0.5, 1.0)
    norm = BoundaryNorm(levels, cmap.N)
    return cmap, norm, levels


def _legend_handles():
    """Build proxy legend handles for management actions."""
    labels = action_labels()
    colors = action_colors()
    return [
        Patch(
            facecolor=colors[action.code],
            edgecolor="black",
            label=labels[action.code],
        )
        for action in ACTIONS
    ]


def draw_operational_zones(
    ax: Axes,
    chart,
    cfg: OperationalOverlayConfig,
) -> None:
    """Draw one bovine thermal-management overlay."""
    T_grid, W_grid, action_grid = _build_management_field(chart, cfg)
    cmap, norm, levels = _build_action_colormap()

    artist = ax.contourf(
        T_grid,
        W_grid,
        action_grid,
        levels=levels,
        cmap=cmap,
        norm=norm,
        alpha=cfg.alpha,
        antialiased=True,
        zorder=cfg.zorder,
    )

    if cfg.show_boundaries:
        ax.contour(
            T_grid,
            W_grid,
            action_grid,
            levels=np.arange(0.5, len(ACTIONS), 1.0),
            colors=cfg.boundary_color,
            linewidths=cfg.boundary_linewidth,
            alpha=cfg.boundary_alpha,
            zorder=cfg.zorder + 0.01,
        )

    if cfg.show_colorbar:
        cbar = plt.colorbar(artist, ax=ax, pad=0.02)
        cbar.set_ticks(np.arange(len(ACTIONS)))
        cbar.set_ticklabels([action.label for action in ACTIONS])
        cbar.set_label(cfg.colorbar_label)

    if cfg.show_legend:
        ax.legend(
            handles=_legend_handles(),
            title=cfg.label or "Thermal-management action",
            loc="best",
        )
