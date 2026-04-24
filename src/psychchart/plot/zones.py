"""Rendering helpers for geometric zones on psychrometric charts."""

from __future__ import annotations

from typing import Tuple

import numpy as np

from psychchart.config import Zone
from psychchart.psychrometrics import Psychrometrics
from .layers import ZORDER
from .utils import clip_to_saturation


# =============================================================================
# Internal geometry helpers
# =============================================================================
def _zone_polygon_rh(
    zone: Zone,
    pressure: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a psychrometric polygon for a rectangular T-RH zone.

    The input zone is defined by a dry-bulb temperature interval and a relative
    humidity interval. The returned polygon is expressed in ``(T, W)`` chart
    coordinates, where the lower and upper boundaries follow RH curves.
    """
    t_lo, t_hi = zone.t_range
    rh_lo, rh_hi = zone.rh_range

    vertices = np.array(
        [
            [t_lo, rh_lo],
            [t_hi, rh_lo],
            [t_hi, rh_hi],
            [t_lo, rh_hi],
            [t_lo, rh_lo],
        ]
    )

    return _zone_polygon_vertices(vertices, pressure)


def _zone_polygon_vertices(
    vertices: np.ndarray,
    pressure: float,
    n: int = 80,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a psychrometric polygon from vertices defined in ``(T, RH)`` space.

    Constant-RH edges are sampled as RH curves. Edges with varying RH are
    linearly interpolated in ``(T, RH)`` space and then converted pointwise to
    humidity ratio.
    """
    T_all = []
    W_all = []

    for (T0, RH0), (T1, RH1) in zip(vertices[:-1], vertices[1:]):
        if np.isclose(RH0, RH1):
            T_seg = np.linspace(T0, T1, n)
            RH_seg = np.full_like(T_seg, RH0)
        else:
            T_seg = np.linspace(T0, T1, n)
            RH_seg = np.linspace(RH0, RH1, n)

        W_seg = Psychrometrics.humidity_ratio(T_seg, RH_seg, pressure)

        T_all.append(T_seg)
        W_all.append(W_seg)

    T_poly = np.concatenate(T_all)
    W_poly = np.concatenate(W_all)

    if (
        not np.isclose(T_poly[0], T_poly[-1])
        or not np.isclose(W_poly[0], W_poly[-1])
    ):
        T_poly = np.append(T_poly, T_poly[0])
        W_poly = np.append(W_poly, W_poly[0])

    return T_poly, W_poly


def _zone_label_position(
    zone: Zone,
    t_poly: np.ndarray,
    w_poly: np.ndarray,
    pressure: float,
) -> tuple[float, float]:
    """
    Return the label position for a zone in chart coordinates.

    Explicit ``label_t``/``label_rh`` values take precedence. Otherwise, the
    label is placed at the polygon centroid approximation.
    """
    if zone.label_t is not None and zone.label_rh is not None:
        label_w = Psychrometrics.humidity_ratio(
            zone.label_t,
            zone.label_rh,
            pressure,
        )
        return float(zone.label_t), float(label_w)

    return float(np.nanmean(t_poly)), float(np.nanmean(w_poly))


def _draw_zone_label(ax, zone: Zone, t_poly: np.ndarray, w_poly: np.ndarray, chart) -> None:
    """
    Draw an optional label associated with a geometric zone.

    Labels are deliberately handled here rather than in the configuration layer
    so the model remains declarative and the plotting backend owns all visual
    concerns.
    """
    if not zone.show_label:
        return

    text = zone.label or zone.name
    if not text:
        return

    x, y = _zone_label_position(zone, t_poly, w_poly, chart.cfg.pressure)

    bbox = zone.label_bbox
    if bbox is None:
        bbox = {
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.70,
        }

    ax.annotate(
        text,
        xy=(x, y),
        ha="center",
        va="center",
        color=zone.label_color or zone.edgecolor,
        fontsize=zone.label_fontsize,
        rotation=zone.label_rotation,
        bbox=bbox,
        zorder=ZORDER["zone_edge"] + 1,
    )


# =============================================================================
# Public zone drawing dispatcher
# =============================================================================
def draw_zones(ax, chart) -> None:
    """
    Draw all geometric zones defined in the chart configuration.

    Supported definitions are:

    1. explicit polygon vertices in ``(T, RH)`` space;
    2. curvilinear ``T x RH`` envelopes bounded by RH curves;
    3. simple interval zones converted directly from corner points.
    """
    for z in chart.zones:
        if z.vertices:
            verts = np.asarray(z.vertices, dtype=float)
            t_poly, w_poly = _zone_polygon_vertices(verts, chart.cfg.pressure)

        elif z.follow_rh and z.t_range and z.rh_range:
            t_poly, w_poly = _zone_polygon_rh(z, chart.cfg.pressure)

        elif z.t_range and z.rh_range:
            t_lo, t_hi = z.t_range
            rh_lo, rh_hi = z.rh_range

            t_poly = np.asarray([t_lo, t_hi, t_hi, t_lo, t_lo], dtype=float)
            w_poly = np.asarray(
                [
                    Psychrometrics.humidity_ratio(t_lo, rh_lo, chart.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_hi, rh_lo, chart.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_hi, rh_hi, chart.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_lo, rh_hi, chart.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_lo, rh_lo, chart.cfg.pressure),
                ],
                dtype=float,
            )

        else:
            raise ValueError(
                f"Zone '{z.name}' is ill-defined and cannot be rendered."
            )

        (line,) = ax.plot(
            t_poly,
            w_poly,
            lw=z.linewidth,
            color=z.edgecolor,
            label=z.name,
            zorder=ZORDER["zone_edge"],
        )

        clip_to_saturation(ax, line, chart.T, chart.W_sat)

        if z.facecolor and z.facecolor.lower() != "none":
            patch = ax.fill(
                t_poly,
                w_poly,
                facecolor=z.facecolor,
                alpha=z.alpha,
                zorder=ZORDER["zone_fill"],
            )[0]
            clip_to_saturation(ax, patch, chart.T, chart.W_sat)

        _draw_zone_label(ax, z, t_poly, w_poly, chart)
