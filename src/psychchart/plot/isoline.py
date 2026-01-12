import numpy as np
from matplotlib.axes import Axes

from psychchart.psychrometrics import Psychrometrics
from psychchart.config import IsoSet, ChartConfig


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
    Draw isolines of a given psychrometric physical quantity.

    This internal helper renders **classical psychrometric isolines**
    (isopleths) directly in thermodynamic space.

    Supported isoline families include:
    - relative humidity
    - wet-bulb temperature
    - enthalpy
    - specific volume
    - moisture quantity (humidity ratio)

    The function evaluates analytical psychrometric relationships
    along the dry-bulb temperature axis and clips results
    to physically meaningful regions (below saturation).

    This function is intentionally:
    - imperative
    - low-level
    - non-polymorphic
    - free of validation or orchestration logic

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes where the isolines will be drawn.
    key : str
        Identifier of the psychrometric quantity.
        Expected values:
        - ``"relative_humidity"``
        - ``"wet_bulb"``
        - ``"enthalpy"``
        - ``"specific_volume"``
        - ``"moisture_quantity"``
    iso : IsoSet
        Isoline configuration (values, style, color, etc.).
    T : numpy.ndarray
        Dry-bulb temperature array (°C).
    W_sat : numpy.ndarray
        Saturation humidity ratio corresponding to ``T``.
    cfg : ChartConfig
        Global chart configuration (pressure, limits).

    Notes
    -----
    - Relative humidity is expressed as fraction (0–1).
    - All isolines are clipped below the saturation curve.
    - No legend handling is performed here.
    """

    # ------------------------------------------------------------------
    # Relative humidity isolines (RH = constant)
    # ------------------------------------------------------------------
    if key == "relative_humidity":
        for rh in iso.values:
            # Convert RH to humidity ratio along temperature axis
            w = Psychrometrics.humidity_ratio(T, rh, cfg.pressure)

            # Plot isoline (below saturation by construction)
            ax.plot(
                T,
                w,
                iso.style,
                color=iso.color or "gray",  # FIX: color was undefined
                lw=0.8,
            )

    # ------------------------------------------------------------------
    # Enthalpy isolines (h = constant)
    # ------------------------------------------------------------------
    elif key == "enthalpy":
        for h in iso.values:
            # Analytical enthalpy relationship:
            # h = cp*T + W*(Hfg + cp_v*T)
            W_line = (h - Psychrometrics.cp * T) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * T
            )

            # Physical validity mask:
            # - humidity ratio must be positive
            # - must lie below saturation curve
            mask = (W_line > 0) & (W_line < W_sat)

            ax.plot(
                T[mask],
                W_line[mask],
                iso.style,
                color=iso.color or "black",
                lw=0.8,
            )

    # ------------------------------------------------------------------
    # Wet-bulb temperature isolines (Twb = constant)
    # ------------------------------------------------------------------
    elif key == "wet_bulb":
        for twb in iso.values:
            # Saturation humidity ratio at wet-bulb temperature
            W_sat_wb = Psychrometrics.humidity_ratio(
                twb, 1.0, cfg.pressure
            )

            # Enthalpy at wet-bulb condition (constant along isoline)
            h_wb = Psychrometrics.enthalpy(twb, W_sat_wb)

            # Reconstruct humidity ratio as function of dry-bulb temperature
            W_line = (h_wb - Psychrometrics.cp * T) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * T
            )

            # Valid only below saturation
            mask = (W_line > 0) & (W_line < W_sat)

            ax.plot(
                T[mask],
                W_line[mask],
                iso.style,
                color=iso.color or "blue",
                lw=0.8,
            )

    # ------------------------------------------------------------------
    # Specific volume isolines (v = constant)
    # ------------------------------------------------------------------
    elif key == "specific_volume":
        for v in iso.values:
            # Convert temperature to Kelvin
            T_K = T + 273.15

            # Analytical specific volume relation
            W_line = (
                v * cfg.pressure / (Psychrometrics.Rd * T_K) - 1
            ) / 1.6078

            # Physical constraints
            mask = (W_line > 0) & (W_line < W_sat)

            ax.plot(
                T[mask],
                W_line[mask],
                iso.style,
                color=iso.color or "purple",
                lw=0.8,
            )

    # ------------------------------------------------------------------
    # Moisture quantity isolines (W = constant)
    # ------------------------------------------------------------------
    elif key == "moisture_quantity":
        for w_val in iso.values:
            # Find temperature range where this humidity ratio is physically possible
            mask = chart.W_sat >= w_val
    
            if not mask.any():
                continue  # this W is never reachable in the domain
    
            T_valid = chart.T[mask]
            # Horizontal isolines in humidity ratio space
            ax.hlines(
                y=w_val,
                xmin=T_valid.min(),
                xmax=T_valid.max(),
                colors=iso.color or "green",
                linestyles=iso.style,
                lw=0.8,
                zorder=3,
            )


# =============================================================================
# Public dispatcher
# =============================================================================
def draw_isolines(ax: Axes, chart) -> None:
    """
    Draw all enabled psychrometric isolines defined in the chart.

    This function acts as a **dispatcher**, iterating over the
    isoline configuration dictionary and invoking the internal
    drawing routine for each enabled isoline family.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes where isolines will be rendered.
    chart : PsychChart
        PsychChart instance providing:
        - isoline definitions
        - thermodynamic domain
        - global configuration
    """
    for key, iso in chart.isolines.items():
        # Skip disabled isoline sets
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

