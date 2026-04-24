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
from psychchart.operations.enums import OperationalAction, TrendMode
from psychchart.operations.zones import build_operational_zone_field
from psychchart.psychrometrics import Psychrometrics


def _default_itu_evaluator(T: np.ndarray, RH: np.ndarray) -> np.ndarray:
    """
    Evaluate ITU on array inputs.

    The operational layer uses the same ITU implementation registered in the
    index system instead of importing an obsolete experimental domain-engine
    module. This keeps operational overlays numerically aligned with the ITU
    fields and isolines rendered elsewhere in the chart.
    """
    return ITU.compute_vectorized({"T": T, "RH": RH})


def _wrap_humidity_ratio_candidate(
    candidate: Callable,
    pressure: float,
) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """
    Wrap supported humidity-ratio call signatures into ``f(T, RH)``.

    Psychrometric helper names are not fully standardized across older
    psychChart versions. This wrapper keeps the operational layer independent
    of those historical naming differences while preserving one canonical
    runtime signature for the gridded operational-field builder.
    """

    def evaluator(T: np.ndarray, RH: np.ndarray) -> np.ndarray:
        try:
            return candidate(T, RH, pressure)
        except TypeError:
            return candidate(T, RH)

    return evaluator


def _resolve_humidity_ratio_evaluator(
    chart,
) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """
    Resolve a humidity-ratio evaluator from the live chart object.

    The operational-zone builder expects a callable with signature
    ``f(T, RH) -> W``. The current psychrometric core exposes the canonical
    method ``Psychrometrics.humidity_ratio(T, RH, P)``. Older experimental
    versions used names such as ``humidity_ratio_from_rh`` or ``w_from_t_rh``.

    This resolver first searches for historical aliases on the chart instance
    and then falls back to the canonical static method using ``chart.cfg``
    pressure. This makes operational overlays work with the current public
    psychrometric API and preserves compatibility with older branches.
    """
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


def _build_action_colormap(profile):
    """Build categorical colormap and norm for operational actions."""
    ordered_actions = list(OperationalAction)
    colors = [profile.action_styles[action].facecolor for action in ordered_actions]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(-0.5, len(ordered_actions) + 0.5, 1.0), cmap.N)
    return cmap, norm


def _legend_handles(profile):
    """Build proxy legend handles for operational actions."""
    handles = []
    for action in OperationalAction:
        style = profile.action_styles[action]
        handles.append(
            Patch(
                facecolor=style.facecolor,
                edgecolor=style.edgecolor,
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
    """
    Draw one operational overlay for one accumulated-load class and trend.
    """
    operational_profiles = getattr(chart, "operational_profiles", None)
    if operational_profiles is None:
        raise AttributeError(
            "PsychChart instance has no 'operational_profiles'. "
            "Make sure AppConfig is attached to the chart instance."
        )

    if cfg.profile not in operational_profiles:
        raise KeyError(
            f"Operational profile {cfg.profile!r} was not found in chart."
        )

    profile_cfg = operational_profiles[cfg.profile]
    profile = profile_cfg.to_runtime()

    trend = TrendMode(cfg.trend)
    humidity_ratio_evaluator = _resolve_humidity_ratio_evaluator(chart)

    field = build_operational_zone_field(
        chart_cfg=chart.cfg,
        profile=profile,
        load_class_name=cfg.load_class,
        trend=trend,
        itu_evaluator=_default_itu_evaluator,
        humidity_ratio_evaluator=humidity_ratio_evaluator,
        n_t=cfg.n_t,
        n_rh=cfg.n_rh,
    )

    cmap, norm = _build_action_colormap(profile)

    mesh = ax.pcolormesh(
        field.T_grid,
        field.W_grid,
        field.action_grid,
        cmap=cmap,
        norm=norm,
        shading="auto",
        alpha=cfg.alpha,
        zorder=cfg.zorder,
    )

    if cfg.show_boundaries:
        ax.contour(
            field.T_grid,
            field.W_grid,
            field.action_grid,
            levels=np.arange(0.5, len(OperationalAction), 1.0),
            colors=cfg.boundary_color,
            linewidths=cfg.boundary_linewidth,
            alpha=cfg.boundary_alpha,
            zorder=cfg.zorder + 0.01,
        )

    if cfg.show_colorbar:
        cbar = plt.colorbar(mesh, ax=ax, pad=0.02)
        cbar.set_ticks(np.arange(len(OperationalAction)))
        cbar.set_ticklabels(
            [profile.action_styles[action].label for action in OperationalAction]
        )
        cbar.set_label(cfg.colorbar_label)

    if cfg.show_legend:
        handles = _legend_handles(profile)
        ax.legend(
            handles=handles,
            title=cfg.label or "Ação operacional",
            loc="best",
        )
