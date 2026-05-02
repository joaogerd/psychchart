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

from psychchart.config.operations import (
    DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME,
    OperationalOverlayConfig,
)
from psychchart.indexes.itu import ITU
from psychchart.operations.engine import action
from psychchart.operations.enums import OperationalAction
from psychchart.operations.profile import (
    DEFAULT_DAIRY_COOLING_PROFILE,
    OperationalProfile,
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


def _trend_to_dca_dt(value: str) -> float:
    """
    Convert a static overlay trend name into a representative dCA/dt value.

    Operational overlays are static psychrometric projections. The trend cannot
    be inferred from a time series at this layer, so the configured trend is
    represented by a small deterministic derivative that activates the profile
    modifiers when appropriate.
    """
    trend = _trend_name(value)
    if trend == "rising":
        return 0.002
    if trend == "falling":
        return -0.002
    return 0.0


def _resolve_operational_profile(
    chart,
    cfg: OperationalOverlayConfig,
) -> OperationalProfile:
    """Resolve the runtime operational profile referenced by an overlay."""
    profile_name = getattr(cfg, "profile", DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME)
    profiles = getattr(chart, "operational_profiles", {}) or {}
    profile_cfg = profiles.get(profile_name)

    if profile_cfg is not None:
        return profile_cfg.to_runtime()

    if profile_name == DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME:
        return DEFAULT_DAIRY_COOLING_PROFILE

    raise KeyError(f"Unknown operational profile: {profile_name!r}")


def _representative_cta(profile: OperationalProfile, cfg: OperationalOverlayConfig) -> float:
    """
    Resolve representative CTA from the selected overlay load class.

    The interactive overlay uses a static psychrometric field. Since true CTA is
    temporal, this value represents the selected accumulated-load class for the
    whole field. It keeps the operational surface explicitly tied to load class
    without hiding time integration inside the renderer.
    """
    load_class = getattr(cfg, "load_class", "A2")
    return float(profile.get_load_class(load_class).representative_value())


def _classify_grid_with_profile(
    profile: OperationalProfile,
    T_grid: np.ndarray,
    RH_grid: np.ndarray,
    ITU_grid: np.ndarray,
    *,
    ca: float,
    dca_dt: float,
) -> np.ndarray:
    """Evaluate the declarative operational engine over a grid."""
    flat_actions = [
        int(
            action(
                profile,
                T=float(T),
                RH=float(RH),
                itu=float(itu),
                ca=ca,
                dca_dt=dca_dt,
            )
        )
        for T, RH, itu in zip(
            T_grid.ravel(),
            RH_grid.ravel(),
            ITU_grid.ravel(),
        )
    ]
    return np.asarray(flat_actions, dtype=int).reshape(T_grid.shape)


def _build_management_field(
    chart,
    cfg: OperationalOverlayConfig,
):
    """Build a management-action field over the psychrometric domain."""
    n_t = int(getattr(cfg, "n_t", 220))
    n_rh = int(getattr(cfg, "n_rh", 180))

    profile = _resolve_operational_profile(chart, cfg)
    ca = _representative_cta(profile, cfg)
    dca_dt = _trend_to_dca_dt(getattr(cfg, "trend", "steady"))

    t_values = np.linspace(chart.cfg.t_min, chart.cfg.t_max, n_t)
    rh_values = np.linspace(0.0, 1.0, n_rh)
    T_grid, RH_grid = np.meshgrid(t_values, rh_values)

    humidity_ratio_evaluator = _resolve_humidity_ratio_evaluator(chart)
    W_grid = np.asarray(humidity_ratio_evaluator(T_grid, RH_grid), dtype=float)
    ITU_grid = np.asarray(_default_itu_evaluator(T_grid, RH_grid), dtype=float)

    action_grid = _classify_grid_with_profile(
        profile,
        T_grid,
        RH_grid,
        ITU_grid,
        ca=ca,
        dca_dt=dca_dt,
    )

    mask = ~np.isfinite(W_grid)
    y_min = getattr(chart.cfg, "y_min", None)
    y_max = getattr(chart.cfg, "y_max", None)
    if y_min is not None:
        mask |= W_grid < y_min
    if y_max is not None:
        mask |= W_grid > y_max

    return T_grid, W_grid, np.ma.masked_array(action_grid, mask=mask), profile


def _ordered_actions() -> list[OperationalAction]:
    """Return operational actions in their semantic severity order."""
    return list(OperationalAction)


def _build_action_colormap(profile: OperationalProfile):
    """Build categorical colormap and norm for profile-defined actions."""
    ordered_actions = _ordered_actions()
    cmap = ListedColormap(
        [profile.action_styles[action].facecolor for action in ordered_actions]
    )
    levels = np.arange(-0.5, len(ordered_actions) + 0.5, 1.0)
    norm = BoundaryNorm(levels, cmap.N)
    return cmap, norm, levels


def _legend_handles(profile: OperationalProfile):
    """Build proxy legend handles for profile-defined operational actions."""
    handles = []
    for action_code in _ordered_actions():
        style = profile.action_styles[action_code]
        handles.append(
            Patch(
                facecolor=style.facecolor,
                edgecolor=style.edgecolor if style.edgecolor != "none" else "black",
                hatch=style.hatch,
                label=style.label,
            )
        )
    return handles


def draw_operational_zones(
    ax: Axes,
    chart,
    cfg: OperationalOverlayConfig,
) -> None:
    """Draw one bovine thermal-management overlay."""
    T_grid, W_grid, action_grid, profile = _build_management_field(chart, cfg)
    cmap, norm, levels = _build_action_colormap(profile)

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
            levels=np.arange(0.5, len(_ordered_actions()), 1.0),
            colors=cfg.boundary_color,
            linewidths=cfg.boundary_linewidth,
            alpha=cfg.boundary_alpha,
            zorder=cfg.zorder + 0.01,
        )

    if cfg.show_colorbar:
        cbar = plt.colorbar(artist, ax=ax, pad=0.02)
        cbar.set_ticks([int(action_code) for action_code in _ordered_actions()])
        cbar.set_ticklabels(
            [profile.action_styles[action_code].label for action_code in _ordered_actions()]
        )
        cbar.set_label(cfg.colorbar_label)

    if cfg.show_legend:
        ax.legend(
            handles=_legend_handles(profile),
            title=cfg.label or "Thermal-management action",
            loc="best",
        )
