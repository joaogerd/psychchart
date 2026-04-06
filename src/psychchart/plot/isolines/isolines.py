"""
Low-level rendering of psychrometric isolines.

This module implements **imperative, low-level drawing routines**
responsible for rendering classical psychrometric isolines
(isopleths) on a Matplotlib axis.

Scope and responsibilities
--------------------------
This module:
- evaluates analytical psychrometric relationships
- clips results to physically meaningful regions
- draws isolines directly on Matplotlib axes
- places labels following psychrometric chart conventions

This module does NOT:
- define configuration schemas
- validate user input
- orchestrate plotting order
- manage legends or colorbars
- expose a public API for end users

All configuration is provided via declarative objects
(:class:`IsoSet`, :class:`ChartConfig`) and via the
higher-level ``PsychChart`` orchestrator.

Design philosophy
-----------------
- Low-level and imperative
- Explicit and readable physics
- No hidden abstractions
- No polymorphism or inheritance
"""

import numpy as np
from matplotlib.axes import Axes
from scipy.optimize import brentq
from typing import Optional

from psychchart.psychrometrics import Psychrometrics
from psychchart.config import IsoSet, ChartConfig
from psychchart.plot.isoline_profiles import get_isoline_profile

from .layers import ZORDER

def _resolve_iso_defaults(key: str, iso: IsoSet):
    """
    Resolve effective isoline rendering parameters by merging defaults
    and user overrides.

    This helper function computes the **final, effective rendering
    configuration** for a given isoline family by merging three layers,
    in strict priority order:

    1. User overrides provided via :class:`IsoSet`
    2. Semantic defaults from :class:`IsolineProfile`
    3. Hard-coded safe defaults (fallback of last resort)

    The result is a flat dictionary of resolved parameters, suitable
    for direct consumption by low-level rendering routines.

    Parameters
    ----------
    key : str
        Canonical isoline family name.

        This must match:
        - the key used by the renderer,
        - the key used in ``IsoSet``,
        - a registered semantic profile (if available).

        Example: ``"relative_humidity"``.

    iso : IsoSet
        User-provided isoline configuration.

        This object may partially override visual attributes such as
        color, line style, label behavior, or numerical values.

    Returns
    -------
    dict
        Dictionary containing the fully resolved isoline parameters.

        Guaranteed keys include:
        - ``color``
        - ``linewidth``
        - ``linestyle``
        - ``labels``
        - ``label_fontsize``
        - ``label_fmt``
        - ``zorder``
        - ``values``

        All values are guaranteed to be non-missing and safe for
        rendering.

    Notes
    -----
    Resolution precedence (highest to lowest priority):

    1. Explicit values in ``IsoSet``
    2. Defaults from ``IsolineProfile`` (if registered)
    3. Hard-coded safe defaults

    This function contains **no rendering logic** and performs
    **no validation** of numerical correctness. Its sole responsibility
    is deterministic resolution of defaults.

    Examples
    --------
    Basic usage inside a renderer:

    >>> iso = IsoSet(color="red", linewidth=2.0)
    >>> params = _resolve_iso_defaults("relative_humidity", iso)
    >>> params["color"]
    'red'
    >>> params["linewidth"]
    2.0

    Profile fallback when user does not override:

    >>> iso = IsoSet()
    >>> params = _resolve_iso_defaults("relative_humidity", iso)
    >>> params["linestyle"]
    '--'

    Safe fallback when profile is missing:

    >>> iso = IsoSet()
    >>> params = _resolve_iso_defaults("unknown_isoline", iso)
    >>> params["linestyle"]
    '-'
    """

    # ------------------------------------------------------------------
    # Resolve semantic profile (may be None if not registered)
    # ------------------------------------------------------------------
    profile = get_isoline_profile(key)

    # ------------------------------------------------------------------
    # Hard-coded safe defaults (last-resort fallback)
    # ------------------------------------------------------------------
    # These values guarantee that rendering never fails, even if:
    # - the isoline family is unknown,
    # - the profile is missing,
    # - the profile is incomplete.
    hard = {
        "color": "0.4",
        "linewidth": 1.0,
        "linestyle": "-",
        "labels": False,
        "label_fontsize": 6,
        "label_fmt": None,
        "zorder": ZORDER["isolines"],
        "values": None,
    }

    # ------------------------------------------------------------------
    # Base defaults: profile → hard fallback
    # ------------------------------------------------------------------
    if profile is None:
        # No semantic profile registered: use hard defaults directly
        base = hard
    else:
        # Start from semantic profile defaults
        base = {
            "color": profile.color,
            "linewidth": profile.linewidth,
            "linestyle": profile.linestyle,
            "labels": profile.labels,
            "label_fontsize": profile.label_fontsize,
            "label_fmt": profile.label_fmt,
            "zorder": profile.zorder,
            "values": profile.values,
        }

        # Fill missing profile attributes with hard defaults
        # This allows profiles to remain intentionally partial.
        for k, v in hard.items():
            if base.get(k) is None:
                base[k] = v

    # ------------------------------------------------------------------
    # Merge IsoSet overrides (highest priority)
    # ------------------------------------------------------------------
    resolved = dict(base)

    # Visual overrides
    if iso.color is not None:
        resolved["color"] = iso.color
    if iso.linewidth is not None:
        resolved["linewidth"] = iso.linewidth
    if iso.linestyle is not None:
        resolved["linestyle"] = iso.linestyle

    # Label behavior overrides
    # NOTE: iso.labels is currently a boolean, not Optional[bool],
    # so it is treated as an explicit override when provided.
    resolved["labels"] = iso.labels if iso.labels is not None else base["labels"]

    # Font size override
    # If IsoSet migrates label_fontsize to Optional[int], this logic
    # already supports that seamlessly.
    resolved["label_fontsize"] = (
        iso.label_fontsize
        if iso.label_fontsize is not None
        else base["label_fontsize"]
    )

    # Numerical values override
    # If user provides explicit isoline levels, they fully replace
    # profile defaults.
    resolved["values"] = (
        iso.values
        if (iso.values and len(iso.values) > 0)
        else base["values"]
    )
    return resolved

# =============================================================================
# Label placement helpers
# =============================================================================
def _label_specific_volume_isoline(
    ax: Axes,
    v: float,
    cfg: ChartConfig,
    color: Optional[str] = None,
    fontsize: int = 5,
    P: float = 101325.0,
    zorder: int = 10,
    W_target: float = 0.004,
):
    """
    Place a label for a constant specific-volume isoline (v = const).

    The label is placed using a **fixed humidity-ratio reference**
    and rotated according to the local slope of the isoline.

    This helper is intentionally heuristic and presentation-oriented.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axis.
    v : float
        Specific volume value (m³/kg dry air).
    cfg : ChartConfig
        Global chart configuration.
    color : str or None
        Text color.
    fontsize : int
        Label font size.
    P : float
        Atmospheric pressure (Pa).
    zorder : int
        Drawing order.
    W_target : float
        Reference humidity ratio for label placement.

    Notes
    -----
    - No guarantees are made that a label will be placed.
    - The function silently returns ``None`` if placement is invalid.
    """

    # ------------------------------------------------------------------
    # Invert specific-volume relation to estimate temperature
    # ------------------------------------------------------------------
    T_K = v * P / (Psychrometrics.Rd * (1 + 1.6078 * W_target))
    T_label = T_K - 273.15
    W_label = W_target

    # ------------------------------------------------------------------
    # Domain and saturation checks
    # ------------------------------------------------------------------
    if T_label < cfg.t_min or T_label > cfg.t_max:
        return None

    W_sat = Psychrometrics.humidity_ratio(T_label, 1.0, P)
    if W_label >= W_sat:
        return None

    # ------------------------------------------------------------------
    # Estimate local slope for rotation
    # ------------------------------------------------------------------
    dW = 0.0005

    def T_from_W(W):
        T_K = v * P / (Psychrometrics.Rd * (1 + 1.6078 * W))
        return T_K - 273.15

    T1 = T_from_W(W_target - dW)
    T2 = T_from_W(W_target + dW)

    angle = np.degrees(np.arctan2(2 * dW, T2 - T1))

    # ------------------------------------------------------------------
    # Draw label
    # ------------------------------------------------------------------
    ax.text(
        T_label,
        W_label,
        f"{v:.2f} m³/kg",
        fontsize=fontsize,
        color=color or "darkred",
        ha="center",
        va="center",
        rotation=angle,
        rotation_mode="anchor",
        zorder=zorder,
        clip_on=False,
    )

    return T_label, W_label


def _label_enthalpy_isoline(
    ax: Axes,
    h: float,
    cfg: ChartConfig,
    color: Optional[str] = None,
    fontsize: int = 5,
    P: float = 101325.0,
    zorder: int = 10,
    T_frac: float = 0.65,
    dW: float = 0.0005,
):
    """
    Place a label for a constant-enthalpy isoline (h = const).

    The label position is selected heuristically as a fraction
    of the temperature domain and adjusted if needed.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axis.
    h : float
        Enthalpy value (kJ/kg dry air).
    cfg : ChartConfig
        Global chart configuration.
    T_frac : float
        Fraction of temperature domain used as initial guess.

    Notes
    -----
    - Multiple fallback positions are attempted.
    - If no valid position exists, the function returns ``None``.
    """

    def W_from_h(T):
        return (h - Psychrometrics.cp * T) / (
            Psychrometrics.Hfg + Psychrometrics.cp_v * T
        )

    # ------------------------------------------------------------------
    # Try multiple candidate positions
    # ------------------------------------------------------------------
    for frac in [T_frac, 0.55, 0.45, 0.35]:
        T_label = cfg.t_min + frac * (cfg.t_max - cfg.t_min)
        W_label = W_from_h(T_label)

        if W_label <= 0:
            continue

        W_sat = Psychrometrics.humidity_ratio(T_label, 1.0, P)
        if W_label >= W_sat:
            continue

        # Estimate local slope for rotation
        dT = 0.5
        W1 = W_from_h(T_label - dT)
        W2 = W_from_h(T_label + dT)
        angle = np.degrees(np.arctan2(W2 - W1, 2 * dT))

        ax.text(
            T_label,
            W_label + dW,
            f"{int(h)} kJ/kg",
            fontsize=fontsize,
            color=color or "black",
            ha="center",
            va="bottom",
            rotation=angle,
            rotation_mode="anchor",
            zorder=zorder,
            clip_on=False,
        )

        return T_label, W_label

    return None


def _label_wet_bulb_isoline(
    ax: Axes,
    twb: float,
    cfg: ChartConfig,
    color: Optional[str] = None,
    fontsize: int = 5,
    P: float = 101325.0,
    zorder: int = 10,
    dT: float = 1.5,
    dW: float = -0.0006,
):
    """
    Place a label for a constant wet-bulb temperature isoline (Twb).

    The label is placed slightly inside the chart domain,
    following standard psychrometric chart conventions.
    """

    W_sat_wb = Psychrometrics.humidity_ratio(twb, 1.0, P)
    h_wb = Psychrometrics.enthalpy(twb, W_sat_wb)

    T_label = twb + dT
    if T_label > cfg.t_max:
        return None

    W_label = (h_wb - Psychrometrics.cp * T_label) / (
        Psychrometrics.Hfg + Psychrometrics.cp_v * T_label
    )

    W_sat = Psychrometrics.humidity_ratio(T_label, 1.0, P)
    if W_label <= 0 or W_label >= W_sat:
        return None

    # Rotation angle
    dT_rot = 0.5
    W1 = (h_wb - Psychrometrics.cp * (T_label - dT_rot)) / (
        Psychrometrics.Hfg + Psychrometrics.cp_v * (T_label - dT_rot)
    )
    W2 = (h_wb - Psychrometrics.cp * (T_label + dT_rot)) / (
        Psychrometrics.Hfg + Psychrometrics.cp_v * (T_label + dT_rot)
    )

    angle = np.degrees(np.arctan2(W2 - W1, 2 * dT_rot))

    ax.text(
        T_label,
        W_label + dW,
        f"{int(twb)}°C",
        fontsize=fontsize,
        color=color or "blue",
        ha="left",
        va="top",
        rotation=angle,
        rotation_mode="anchor",
        zorder=zorder,
        clip_on=False,
    )

    return T_label, W_label


def _label_rh_isoline(
    ax: Axes,
    rh: float,
    cfg: ChartConfig,
    color: Optional[str] = None,
    fontsize: int = 5,
    P: float = 101325.0,
    zorder: int = 10,
    dx_right: float = -1.5,
    dy_top: float = -0.0008,
):
    """
    Place a relative-humidity (RH) label at the chart boundary.

    The label is positioned where the RH curve exits the chart
    domain (top or right boundary).

    Returns
    -------
    tuple or None
        (T_label, W_label, side) if successful, otherwise None.
    """

    if cfg.y_max is None:
        return None

    def W_rh(T):
        return Psychrometrics.humidity_ratio(T, rh, P)

    try:
        T_exit = brentq(lambda T: W_rh(T) - cfg.y_max, cfg.t_min, cfg.t_max)
        W_exit = cfg.y_max
        side = "top"
    except ValueError:
        T_exit = cfg.t_max
        W_exit = W_rh(cfg.t_max)
        side = "right"

    if side == "top":
        dx, dy = -1.3, dy_top
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
        fontsize=fontsize,
        color=color or "black",
        ha=ha,
        va=va,
        zorder=zorder,
        clip_on=False,
    )

    return T_label, W_label, side


# =============================================================================
# Low-level isoline drawing helper
# =============================================================================
def _draw_isoline(
    ax: Axes,
    key: str,
    iso: IsoSet,
    T: np.ndarray,
    W_sat: np.ndarray,
    cfg: ChartConfig,
) -> None:
    """
    Draw isolines of a given psychrometric quantity.

    This function renders **classical psychrometric isopleths**
    directly in thermodynamic space, using analytical expressions.

    Supported isoline families
    --------------------------
    - relative_humidity
    - enthalpy
    - wet_bulb
    - specific_volume
    - moisture_quantity

    Notes
    -----
    - All isolines are clipped below the saturation curve.
    - No legend or validation logic is handled here.
    """

    # ------------------------------------------------------------------
    # Relative humidity isolines
    # ------------------------------------------------------------------
    if key == "relative_humidity":
        st = _resolve_iso_defaults(key, iso)
    
        # se não houver valores (nem no IsoSet, nem no profile), não desenha
        if not st["values"]:
            return
        
        for rh in st["values"]:
            w = Psychrometrics.humidity_ratio(T, rh, cfg.pressure)
    
            ax.plot(
                T,
                w,
                linestyle=st["linestyle"],
                color=st["color"],
                lw=st["linewidth"],
                zorder=st["zorder"],
            )
    
            if st["labels"]:
                _label_rh_isoline(
                    ax,
                    rh,
                    cfg,
                    color=st["color"],
                    fontsize=st["label_fontsize"],
                    zorder=st["zorder"] + 2,
                )
    # ------------------------------------------------------------------
    # Enthalpy isolines
    # ------------------------------------------------------------------
    elif key == "enthalpy":
        for h in iso.values:
            W_line = (h - Psychrometrics.cp * T) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * T
            )
            mask = (W_line > 0) & (W_line < W_sat)

            ax.plot(
                T[mask],
                W_line[mask],
                iso.linestyle,
                color=iso.color or "black",
                lw=iso.linewidth,
                zorder=ZORDER["isolines"],
            )
            if iso.labels:
                _label_enthalpy_isoline(
                    ax, h, cfg, iso.color,
                    fontsize=iso.label_fontsize,
                    zorder=ZORDER["isolines"] + 2,
                )

    # ------------------------------------------------------------------
    # Wet-bulb temperature isolines
    # ------------------------------------------------------------------
    elif key == "wet_bulb":
        for twb in iso.values:
            W_sat_wb = Psychrometrics.humidity_ratio(twb, 1.0, cfg.pressure)
            h_wb = Psychrometrics.enthalpy(twb, W_sat_wb)

            W_line = (h_wb - Psychrometrics.cp * T) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * T
            )
            mask = (W_line > 0) & (W_line < W_sat)

            ax.plot(
                T[mask],
                W_line[mask],
                iso.linestyle,
                color=iso.color or "blue",
                lw=iso.linewidth,
                zorder=ZORDER["isolines"],
            )
            if iso.labels:
                _label_wet_bulb_isoline(
                    ax, twb, cfg, iso.color,
                    fontsize=iso.label_fontsize,
                    zorder=ZORDER["isolines"] + 2,
                )

    # ------------------------------------------------------------------
    # Specific volume isolines
    # ------------------------------------------------------------------
    elif key == "specific_volume":
        for v in iso.values:
            T_K = T + 273.15
            W_line = (
                v * cfg.pressure / (Psychrometrics.Rd * T_K) - 1
            ) / 1.6078

            mask = (W_line > 0) & (W_line < W_sat)

            ax.plot(
                T[mask],
                W_line[mask],
                iso.linestyle,
                color=iso.color or "purple",
                lw=iso.linewidth,
                zorder=ZORDER["isolines"],
            )
            if iso.labels:
                _label_specific_volume_isoline(
                    ax, v, cfg, iso.color,
                    fontsize=iso.label_fontsize,
                    zorder=ZORDER["isolines"] + 2,
                )

    # ------------------------------------------------------------------
    # Moisture quantity isolines (W = const)
    # ------------------------------------------------------------------
    elif key == "moisture_quantity":
        for w_val in iso.values:
            mask = W_sat >= w_val
            if not mask.any():
                continue

            ax.hlines(
                y=w_val,
                xmin=T[mask].min(),
                xmax=T[mask].max(),
                colors=iso.color or "green",
                linewidths=iso.linewidth,
                linestyles=iso.linestyle,
                zorder=ZORDER["isolines"],
            )


# =============================================================================
# Public dispatcher
# =============================================================================
def draw_isolines(ax: Axes, chart) -> None:
    """
    Draw all enabled psychrometric isolines defined in a chart.

    This function acts as a **dispatcher**, iterating over the
    isoline configuration dictionary and invoking the internal
    drawing routine for each enabled isoline family.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axis.
    chart : PsychChart
        Chart instance providing:
        - ``chart.isolines`` : dict[str, IsoSet]
        - ``chart.T``        : temperature grid
        - ``chart.W_sat``    : saturation curve
        - ``chart.cfg``      : global chart configuration

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> draw_isolines(ax, chart)
    """

    for key, iso in chart.isolines.items():
        if not iso.enabled:
            continue

        _draw_isoline(
            ax=ax,
            key=key,
            iso=iso,
            T=chart.T,
            W_sat=chart.W_sat,
            cfg=chart.cfg,
        )

