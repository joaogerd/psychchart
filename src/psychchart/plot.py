"""
Plotting engine for psychrometric charts.

This module receives validated configuration objects and
produces a Matplotlib-based psychrometric diagram.

Responsibilities
----------------
- Transform psychrometric relationships into visual elements
- Draw saturation curves, isolines, zones, and reference points
- Handle axis scaling, labels, legends, and styles

Non-responsibilities
--------------------
- YAML parsing
- Input validation
- Command-line interfaces

All inputs are assumed to be **validated and normalized**
before reaching this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Dict, Any, List, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .psychrometrics import Psychrometrics
from .config import ChartConfig, IsoSet, Zone, Point


# =============================================================================
# Internal helper functions
# =============================================================================
def _zone_polygon_rh(zone: Zone, pressure: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate polygon vertices following relative humidity curves.

    The polygon is constructed between T_min and T_max and bounded
    by RH_min and RH_max, closing on the left side.

    Parameters
    ----------
    zone : Zone
        Zone with ``t_range=(T_min, T_max)`` and ``rh_range=(RH_min, RH_max)``.
    pressure : float
        Total air pressure (Pa).

    Returns
    -------
    T_poly : ndarray
        Dry-bulb temperature coordinates (°C).
    W_poly : ndarray
        Humidity ratio coordinates (kg_vapor / kg_dry_air).
    """
    t_lo, t_hi = zone.t_range
    rh_lo, rh_hi = zone.rh_range

    # Lower RH boundary (forward direction)
    t_fwd = np.linspace(t_lo, t_hi, 200)
    w_lo = Psychrometrics.humidity_ratio(t_fwd, rh_lo, pressure)

    # Upper RH boundary (reverse direction)
    t_rev = t_fwd[::-1]
    w_hi = Psychrometrics.humidity_ratio(t_rev, rh_hi, pressure)

    # Close polygon
    T_poly = np.concatenate([t_fwd, t_rev, [t_lo]])
    W_poly = np.concatenate([w_lo, w_hi, [w_lo[0]]])

    return T_poly, W_poly


def _draw_isoline(
    ax: Axes,
    key: str,
    iso: IsoSet,
    t: np.ndarray,
    cfg: ChartConfig
) -> None:
    """
    Draw isolines of a given physical quantity.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes on which isolines are drawn.
    key : str
        Isoline identifier:
        - ``"relative_humidity"``
        - ``"wet_bulb"``
        - ``"enthalpy"``
        - ``"specific_volume"``
        - ``"moisture_quantity"``
    iso : IsoSet
        Isoline configuration (values, style, colors).
    t : ndarray
        Dry-bulb temperature array (°C).
    cfg : ChartConfig
        Global chart configuration.
    """
    # Saturation curve for masking
    w_sat = Psychrometrics.humidity_ratio(t, np.ones_like(t), cfg.pressure)

    if key == "relative_humidity":
        for rh in iso.values:
            color = (
                plt.get_cmap(iso.cmap)(rh) if iso.cmap
                else iso.color or "k"
            )
            w = Psychrometrics.humidity_ratio(t, rh, cfg.pressure)
            ax.plot(t, w, iso.style, color=color, lw=0.8)

    elif key == "wet_bulb":
        for twb in iso.values:
            W_sat = Psychrometrics.humidity_ratio(twb, 1.0, cfg.pressure)
            h_wb = Psychrometrics.enthalpy(twb, W_sat)
            W_line = (h_wb - Psychrometrics.cp * t) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * t
            )
            mask = W_line < w_sat
            ax.plot(
                t[mask], W_line[mask],
                iso.style, color=iso.color or "gray", lw=0.8
            )

    elif key == "enthalpy":
        for h in iso.values:
            W_line = (h - Psychrometrics.cp * t) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * t
            )
            mask = (W_line > 0) & (W_line < w_sat)
            ax.plot(
                t[mask], W_line[mask],
                iso.style, color=iso.color or "steelblue", lw=0.8
            )

    elif key == "specific_volume":
        for v in iso.values:
            T_K = t + 273.15
            W_line = (v * cfg.pressure / (Psychrometrics.Rd * T_K) - 1) / 1.6078
            mask = (W_line > 0) & (W_line < w_sat)
            ax.plot(
                t[mask], W_line[mask],
                iso.style, color=iso.color or "green", lw=0.8
            )

    elif key == "moisture_quantity":
        for w_val in iso.values:
            ax.hlines(
                y=w_val,
                xmin=cfg.t_min,
                xmax=cfg.t_max,
                colors=iso.color or "green",
                linestyles=iso.style,
                lw=0.8,
                zorder=3
            )


# =============================================================================
# Main plotting class
# =============================================================================
@dataclass
class PsychChart:
    """
    Psychrometric chart rendering engine.

    Parameters
    ----------
    cfg : ChartConfig
        Global chart configuration.
    isolines : dict of str -> IsoSet, optional
        Mapping between isoline keys and IsoSet definitions.
    zones : list of Zone, optional
        Highlighted regions in the chart.
    points : list of Point, optional
        Reference points to be plotted.

    Notes
    -----
    This class assumes that all inputs are valid.
    """

    cfg: ChartConfig
    isolines: Dict[str, IsoSet] = None
    zones: List[Zone] = None
    points: List[Point] = None

    def __post_init__(self):
        self.isolines = self.isolines or {}
        self.zones = self.zones or []
        self.points = self.points or []

    # ------------------------------------------------------------------
    def draw(self) -> Axes:
        """
        Render the psychrometric chart.

        Returns
        -------
        ax : matplotlib.axes.Axes
            Axes containing the full psychrometric diagram.
        """
        if self.cfg.style:
            plt.style.use(self.cfg.style)

        t = np.linspace(self.cfg.t_min, self.cfg.t_max, 600)
        fig, ax = plt.subplots(figsize=(12, 7))

        # Saturation curve (100 % RH)
        w_sat = Psychrometrics.humidity_ratio(
            t, np.ones_like(t), self.cfg.pressure
        )
        ax.plot(t, w_sat, lw=2, color="orange", label="100 % RH")

        # Draw isolines
        for key, iso in self.isolines.items():
            if not iso.enabled:
                continue
            _draw_isoline(ax, key, iso, t, self.cfg)

        # Draw zones
        for z in self.zones:
            if z.vertices:
                verts = np.asarray(z.vertices)
                t_poly = verts[:, 0]
                rh_vals = verts[:, 1]
                w_poly = Psychrometrics.humidity_ratio(
                    t_poly, rh_vals, self.cfg.pressure
                )
                if not np.allclose(verts[0], verts[-1]):
                    t_poly = np.append(t_poly, t_poly[0])
                    w_poly = np.append(w_poly, w_poly[0])

            elif z.follow_rh and z.t_range and z.rh_range:
                t_poly, w_poly = _zone_polygon_rh(z, self.cfg.pressure)

            elif z.t_range and z.rh_range:
                t_lo, t_hi = z.t_range
                rh_lo, rh_hi = z.rh_range
                t_poly = [t_lo, t_hi, t_hi, t_lo, t_lo]
                w_poly = [
                    Psychrometrics.humidity_ratio(t_lo, rh_lo, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_hi, rh_lo, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_hi, rh_hi, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_lo, rh_hi, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_lo, rh_lo, self.cfg.pressure),
                ]

            else:
                raise ValueError(f"Zone '{z.name}' is ill-defined.")

            ax.plot(
                t_poly, w_poly,
                lw=z.linewidth, color=z.edgecolor, label=z.name
            )
            if z.facecolor and z.facecolor.lower() != "none":
                ax.fill(t_poly, w_poly, facecolor=z.facecolor, alpha=0.20)

        # Draw reference points
        for p in self.points:
            w_p = Psychrometrics.humidity_ratio(
                p.t, p.rh, self.cfg.pressure
            )
            ax.scatter(p.t, w_p, marker=p.marker, color=p.color, zorder=5)
            ax.text(
                p.t, w_p, f" {p.label}",
                va="center", ha="left",
                fontsize=9, color=p.color
            )

        # Axis labels and limits
        ax.set_xlabel("Dry-bulb temperature (°C)")
        ax.set_ylabel("Humidity ratio (kg vapor / kg dry air)")
        ax.set_xlim(self.cfg.t_min, self.cfg.t_max)

        y_min = self.cfg.y_min if self.cfg.y_min is not None else 0.0
        if self.cfg.y_max is not None:
            y_max = self.cfg.y_max
        else:
            y_max = (
                Psychrometrics.humidity_ratio(
                    self.cfg.t_max, 1.0, self.cfg.pressure
                ) * 1.05
            )
        ax.set_ylim(y_min, y_max)

        ax.grid(True, ls="--", lw=0.5)
        ax.legend(loc="upper left")

        # Secondary Y-axis
        ax2 = ax.twinx()
        ax2.set_ylim(ax.get_ylim())
        ax2.set_ylabel("Humidity ratio (kg vapor / kg dry air) — right axis")

        return ax


# =============================================================================
# Usage examples
# =============================================================================
#
# Example 1: Minimal chart
#
# >>> import matplotlib.pyplot as plt
# >>> from psychchart import ChartConfig, IsoSet, PsychChart
# >>> cfg = ChartConfig(t_min=0, t_max=40)
# >>> isos = {
# ...     "relative_humidity": IsoSet(
# ...         name="relative_humidity",
# ...         values=[0.3, 0.5, 0.7, 0.9],
# ...         style="--"
# ...     )
# ... }
# >>> chart = PsychChart(cfg, isolines=isos)
# >>> ax = chart.draw()
# >>> plt.show()
#
#
# Example 2: Chart with zones and points
#
# >>> import matplotlib.pyplot as plt
# >>> from psychchart import Zone, Point
# >>> comfort = Zone(
# ...     name="Comfort",
# ...     t_range=(18, 26),
# ...     rh_range=(0.4, 0.7),
# ...     facecolor="lightgreen",
# ...     edgecolor="green"
# ... )
# >>> ref = Point(label="Observed", t=30, rh=0.65, color="red")
# >>> chart = PsychChart(cfg, isolines=isos, zones=[comfort], points=[ref])
# >>> chart.draw()
# >>> plt.show()
#

