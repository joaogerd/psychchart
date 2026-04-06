"""
Label placement helpers for psychrometric isolines.

This module implements **heuristic, presentation-oriented helpers**
responsible for placing text labels along psychrometric isolines
(isopleths).

Scope and responsibilities
--------------------------
This module:
- computes suitable label anchor points for isolines,
- estimates local isoline slope to rotate labels,
- places labels using Matplotlib text primitives,
- applies chart-boundary–aware heuristics.

This module does NOT:
- compute isoline geometry,
- validate psychrometric correctness,
- manage label enable/disable logic,
- decide which isolines should be labeled.

All label placement here is **best-effort** and intentionally tolerant:
if a valid placement cannot be found, functions return ``None`` silently.

Design philosophy
-----------------
Label placement in psychrometric charts is inherently heuristic.
This module embraces that reality and prioritizes:
- visual clarity,
- robustness,
- non-intrusive behavior.

Each helper is isoline-specific and mirrors classical
psychrometric chart conventions.
"""
from typing import Dict, Tuple

import numpy as np
from typing import Optional
from scipy.optimize import brentq
from matplotlib.axes import Axes

from psychchart.psychrometrics import Psychrometrics
from psychchart.config import ChartConfig
from .util import find_curve_exit

def _small_segment(
    x: float,
    y: float,
    angle_deg: float,
    length: float = 1.0,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Generate a short line segment centered at a given point and oriented
    by a specified angle, expressed in data coordinates.

    Purpose
    -------
    This function is a **graphical primitive** used to create small,
    orientation-preserving line segments that act as visual anchors
    for labels on psychrometric charts.

    The segment is centered at ``(x, y)`` and aligned with the local
    direction of an isoline, as defined by ``angle_deg``. It does not
    perform any physical or thermodynamic computation and is entirely
    independent of psychrometric constraints.

    Coordinate system
    -----------------
    All computations are performed in **data coordinates**, not in
    display or pixel coordinates. As a result:
        - the segment orientation is physically meaningful,
        - the segment length scales with the chart axes,
        - no Matplotlib transforms are applied.

    Parameters
    ----------
    x : float
        x-coordinate of the segment center (typically dry-bulb
        temperature).
    y : float
        y-coordinate of the segment center (typically humidity ratio).
    angle_deg : float
        Segment orientation angle, in degrees, measured counterclockwise
        from the positive x-axis.
    length : float, optional
        Total length of the segment, expressed in data units.
        Default is 1.0.

    Returns
    -------
    tuple[tuple[float, float], tuple[float, float]]
        Two points ``(x1, y1)``, ``(x2, y2)`` defining the segment
        endpoints, ordered symmetrically around the center point.

    Notes
    -----
    - The returned points are symmetric with respect to ``(x, y)``.
    - This function is intentionally minimal and stateless.
    - It is primarily intended for internal use in label placement
      routines (e.g., enthalpy, wet-bulb, specific-volume isolines).

    See Also
    --------
    label_enthalpy
        Uses this primitive to draw short orientation-aligned segments
        at the start of enthalpy isolines.
    """

    theta = np.deg2rad(angle_deg)
    half_len = length * 0.5

    dx = np.cos(theta) * half_len
    dy = np.sin(theta) * half_len

    return (x - dx, y - dy), (x + dx, y + dy)


def label_enthalpy(
    ax: Axes,
    geom: dict[float, tuple[np.ndarray, np.ndarray]],
    cfg: ChartConfig,
    st: dict,
) -> None:
    """
    Place enthalpy labels at the *start point* of constant-enthalpy
    isolines on a psychrometric chart.

    Scope and responsibility
    ------------------------
    This function performs **semantic labeling only**. It does NOT:
        - compute psychrometric relationships,
        - detect physical intersections,
        - validate thermodynamic admissibility,
        - modify isoline geometry.

    All thermodynamic and geometric correctness is guaranteed upstream
    by :func:`draw_enthalpy`.

    Geometric contract
    ------------------
    For each enthalpy value ``h`` present in ``geom``, the associated
    geometry must satisfy the following contract:

        1) ``geom[h] = (T_line, W_line)``
        2) ``T_line`` and ``W_line`` are ordered arrays of equal length
        3) ``(T_line[0], W_line[0])`` is the **exact intersection**
           of the enthalpy isoline with the saturation curve (RH = 100%)
        4) Subsequent points ``(T_line[i], W_line[i])`` lie strictly
           inside the physically admissible sub-saturated region
           (``0 <= W <= W_sat(T)``)

    This contract allows the label position and orientation to be
    determined purely from the geometry, without recomputing any
    physical constraints.

    Label placement strategy
    ------------------------
    The label is placed at the *leftmost physical point* of the isoline,
    corresponding to the saturation intersection. The local direction
    of the isoline is estimated from the first two points of the curve,
    providing a physically meaningful orientation.

    A short line segment, aligned with the isoline direction, is drawn
    at the label location as a visual anchor. This reproduces the
    classical labeling convention found in psychrometric charts
    (e.g., ASHRAE and Mollier diagrams).

    Visual design principles
    ------------------------
    - The label orientation follows the local slope of the isoline.
    - The label is anchored to the segment endpoint using
      ``rotation_mode='anchor'`` to preserve alignment.
    - All styling (color, linewidth, font size, z-order) is controlled
      externally via the ``st`` dictionary.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes for rendering the labels.
    geom : dict[float, tuple[np.ndarray, np.ndarray]]
        Mapping from enthalpy value ``h`` to isoline geometry
        ``(T_line, W_line)``, as returned by :func:`draw_enthalpy`.
    cfg : ChartConfig
        Global chart configuration. Included for API consistency and
        potential future extensions; not directly modified here.
    st : dict
        Style and configuration dictionary. Expected keys include:
            - ``values``: iterable of enthalpy values to label
            - ``color``: label and segment color
            - ``linewidth``: segment line width
            - ``label_fontsize``: font size for text labels
            - ``zorder``: base drawing order

    Notes
    -----
    - If an enthalpy isoline has fewer than two points, no label is
      placed, as the local direction cannot be reliably estimated.
    - This function assumes that ``geom`` already excludes
      supersaturated regions and that isolines touching the saturation
      curve do so at their first point.
    - The function has no return value and produces only graphical
      side effects on the provided Matplotlib axes.

    See Also
    --------
    draw_enthalpy
        Computes physically admissible enthalpy isoline geometries and
        enforces correct intersection with the saturation curve.
    """

    print(f"t_min:{cfg.t_min}, t_max:{cfg.t_max}, y_max(w_max):{cfg.y_max}")
    for h in st["values"]:
        if h not in geom:
            continue

        T_line, W_line = geom[h]
        print(f"T_line: {T_line}")
        print(f"W_line: {W_line}")
        if len(T_line) < 2:
            continue

        # --- intersection point (first isoline point)
        T0, W0 = T_line[0], W_line[0]
        T1, W1 = T_line[1], W_line[1]

        # --- direction of enthalpy isoline
        dT = T_line[1] - T_line[0]
        dW = W_line[1] - W_line[0]
        angle = np.degrees(np.arctan2(dW, dT))

        # --- small segment for visual reference
        p1, p2 = _small_segment(T0, W0, angle, length=0.5)

        # --- top boundary (W = y_max)
        exit_info = find_curve_exit(
            T_line,
            W_line,
            t_min=cfg.t_min,
            t_max=cfg.t_max,
            y_max=cfg.y_max,
        )
        
        if exit_info is None:
            continue
        
        T_exit, W_exit, side, angle = exit_info
        print(h)
        print(exit_info)
        ax.plot(
            (p1[0], p2[0]),
            (p1[1], p2[1]),
            color=st["color"],
            lw=st["linewidth"],
            zorder=st["zorder"] + 2,
        )

        ax.text(
            p1[0],
            p1[1],
            f"{int(h)}",
            fontsize=st["label_fontsize"],
            color=st["color"],
            ha="right",
            va="bottom",
            rotation=angle,
            rotation_mode="anchor",
            zorder=st["zorder"] + 2,
            clip_on=False,
        )

def label_relative_humidity(
    ax: Axes,
    geom: dict[float, tuple[np.ndarray, np.ndarray]],
    cfg: ChartConfig,
    st: dict,
    segment_length=0.5,
) -> None:
    """
    Place relative-humidity (RH) labels at the boundary of the
    psychrometric chart.

    Scope and responsibility
    ------------------------
    This function performs **semantic labeling only**. It does NOT:
        - compute psychrometric relationships,
        - clip isolines to physical limits,
        - modify isoline geometry.

    All geometric information is consumed from ``geom``, which is
    expected to be produced by :func:`draw_relative_humidity`.

    Geometric contract
    ------------------
    For each relative humidity value ``RH`` present in ``geom``:

        - ``geom[RH] = (T_line, W_line)``
        - ``T_line`` and ``W_line`` are ordered arrays of equal length
        - The curve spans the temperature domain without explicit
          truncation at chart boundaries

    Label placement strategy
    ------------------------
    The label is placed at the point where the RH isoline exits the
    visible chart domain:

        - Preferentially at the top boundary (``W = cfg.y_max``),
        - Otherwise at the right boundary (``T = cfg.x_max``).

    The local orientation of the isoline is estimated from the last two
    valid points of the curve. A short line segment aligned with the
    isoline direction is drawn as a visual anchor for the label.

    Visual design principles
    ------------------------
    - Labels follow the local slope of the RH isoline.
    - A small oriented segment is used to anchor the text.
    - All visual styling is controlled externally via ``st``.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes for rendering.
    geom : dict[float, tuple[np.ndarray, np.ndarray]]
        Mapping from RH value (0–1) to isoline geometry ``(T, W)``.
    cfg : ChartConfig
        Global chart configuration. ``x_max`` and ``y_max`` must be
        defined for boundary detection.
    st : dict
        Style dictionary. Expected keys include:
            - ``values`` : iterable of RH values (0–1)
            - ``color`` : color for label and segment
            - ``linewidth`` : segment line width
            - ``label_fontsize`` : font size for text
            - ``zorder`` : base drawing order
    dx_right : float, optional
        Horizontal offset applied when labeling at the right boundary
        (data coordinates).
    dy_top : float, optional
        Vertical offset applied when labeling at the top boundary
        (data coordinates).

    Notes
    -----
    - If the chart limits are undefined, no labels are placed.
    - If an isoline has fewer than two points inside the visible domain,
      it is skipped.
    """
    if cfg.t_max is None or cfg.y_max is None:
        return
    
    for rh in st["values"]:
        if rh not in geom:
            continue
    
        T_line, W_line = geom[rh]
        if len(T_line) < 2:
            continue
    
        T_exit = W_exit = None
        angle_curve = None
        side = None
    
        # --------------------------------------------------------------
        # 1) Find the first segment that exits the visible domain
        # --------------------------------------------------------------
        for i in range(len(T_line) - 1):
            T0, W0 = T_line[i],   W_line[i]
            T1, W1 = T_line[i+1], W_line[i+1]
    
            # ignore segments fully outside
            if T0 > cfg.t_max and T1 > cfg.t_max:
                continue
            if W0 > cfg.y_max and W1 > cfg.y_max:
                continue
    
            # --- top boundary (W = y_max)
            if (W0 < cfg.y_max) and (W1 >= cfg.y_max):
                T_exit = np.interp(cfg.y_max, [W0, W1], [T0, T1])
                W_exit = cfg.y_max
                side = "top"
    
            # --- right boundary (T = t_max)
            elif (T0 < cfg.t_max) and (T1 >= cfg.t_max):
                W_exit = np.interp(cfg.t_max, [T0, T1], [W0, W1])
                T_exit = cfg.t_max
                side = "right"
    
            else:
                continue
    
            # local slope angle (from the same segment)
            dT = T1 - T0
            dW = W1 - W0
            angle_curve = np.degrees(np.arctan2(dW, dT))
            break
    
        if T_exit is None:
            continue
    
        # --------------------------------------------------------------
        # 2) Define angle and segment length
        # --------------------------------------------------------------
        if side == "top":
            angle = 90.0
            segment_length = 0.01 * (cfg.y_max - cfg.y_min)
        else:
            angle = angle_curve
            segment_length = 0.005 * (cfg.t_max - cfg.t_min)

        # --------------------------------------------------------------
        # 3) Build directional segment (NOT centered)
        # --------------------------------------------------------------
        if side == "top":
            # from exit point UPWARDS
            x0, y0 = T_exit, W_exit
            x1 = T_exit
            y1 = W_exit + segment_length
    
        else:
            # from first point of the segment TO exit
            x0 = T_exit - segment_length
            y0 = W_exit
            x1, y1 = T_exit, W_exit
    
        ax.plot(
            (x0, x1),
            (y0, y1),
            color=st["color"],
            lw=st["linewidth"],
            zorder=st["zorder"] + 2,
            clip_on=False,
        )
    
        # --------------------------------------------------------------
        # 4) Label at the outer end of the segment
        # --------------------------------------------------------------
        if side == "top":
            ha, va = "center", "bottom"
            x_txt, y_txt = x1, y1
        else:
            ha, va = "right", "center"
            x_txt, y_txt = x0, y0
    
        ax.text(
            x_txt,
            y_txt,
            f"{int(rh * 100)}%",
            fontsize=st["label_fontsize"],
            color=st["color"],
            ha=ha,
            va=va,
            #rotation=angle,
            rotation_mode="anchor",
            zorder=st["zorder"] + 2,
            clip_on=False,
        )

def _label_rh(
    ax: Axes,
    geom: Dict[float, Tuple[np.ndarray, np.ndarray]],
    cfg,
    st: Dict,
):
    """
    Place enthalpy labels at the intersection of enthalpy isolines
    with the saturation curve (psychrometric convention).

    The label represents the enthalpy of saturated air:
    h = const at RH = 100%.
    """
    
    for h in st["values"]:
        if h not in geom:
            continue

        T_line, W_line = geom[h]

        if len(T_line) < 2:
            continue

        # --- intersection point (first isoline point)
        T0, W0 = T_line[0], W_line[0]

        # --- direction of enthalpy isoline
        dT = T_line[1] - T_line[0]
        dW = W_line[1] - W_line[0]
        angle = np.degrees(np.arctan2(dW, dT))

        # --- small segment for visual reference
        p1, p2 = _small_segment(T0, W0, angle, length=0.5)

        ax.plot(
            (p1[0], p2[0]),
            (p1[1], p2[1]),
            color=st["color"],
            lw=st["linewidth"],
            zorder=st["zorder"] + 2,
        )

        ax.text(
            p1[0],
            p1[1],
            f"{int(h)}",
            fontsize=st["label_fontsize"],
            color=st["color"],
            ha="right",
            va="bottom",
            rotation=angle,
            rotation_mode="anchor",
            zorder=st["zorder"] + 2,
            clip_on=False,
        )

# =============================================================================
# Relative humidity (RH = const)
# =============================================================================
def label_rh(
    ax: Axes,
    geom: Dict[float, Tuple[np.ndarray, np.ndarray]],
    cfg: ChartConfig,
    st: Dict,
    P: float = 101325.0,
    dx_right: float = -1.5,
    dy_top: float = -0.0000,
):
    """
    Place a relative-humidity (RH) label at the chart boundary.

    The label is positioned where the RH curve exits the chart
    domain (top or right boundary).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axis.
    rh : float
        Relative humidity value (0–1).
    cfg : ChartConfig
        Global chart configuration.

    Returns
    -------
    tuple or None
        ``(T_label, W_label, side)`` if successful, otherwise ``None``.
    """

    if cfg.y_max is None:
        return None

    def W_rh(T, rh):
        return Psychrometrics.humidity_ratio(T, rh, P)

    for rh in st["values"]:
        if rh not in geom:
            continue
        
        try:
            # Attempt intersection with top boundary
            T_exit = brentq(lambda T: W_rh(T,rh) - cfg.y_max, cfg.t_min, cfg.t_max)
            W_exit = cfg.y_max
            side = "top"
        except ValueError:
            # Fallback: right boundary
            T_exit = cfg.t_max
            W_exit = W_rh(cfg.t_max, rh)
            side = "right"
    
        if side == "top":
            dx, dy = 0.0, dy_top
            ha, va = "center", "top"
        else:
            dx, dy = dx_right, 0.0
            ha, va = "left", "center"
    
        T_label = T_exit + dx
        W_label = W_exit + dy
    
        ax.text(
            T_label,
            W_label,
            f"{int(rh * 100)}%",
            fontsize=st["label_fontsize"],
            color=st["color"],
            ha=ha,
            va=va,
            zorder=st["zorder"] + 2,
            clip_on=False,
        )

