"""
YAML configuration loader for psychchart.

This module is responsible for:
- reading YAML configuration files
- normalizing user inputs (e.g. relative humidity in %)
- validating basic semantic constraints
- instantiating configuration dataclasses

It acts as a bridge between declarative configuration files
(YAML) and the internal Python data models.
"""

from __future__ import annotations

from typing import Dict, Any, List
import pathlib

import yaml

from .config import ChartConfig, IsoSet, Zone, Point


# =============================================================================
# Internal helper utilities
# =============================================================================
def _normalize_rh(value: float) -> float:
    """
    Normalize relative humidity values.

    Accepts either:
    - fraction in [0, 1]
    - percentage in [0, 100]

    Parameters
    ----------
    value : float
        Relative humidity value.

    Returns
    -------
    rh : float
        Normalized relative humidity in the range [0, 1].

    Raises
    ------
    ValueError
        If the value is outside valid bounds.
    """
    if value > 1.0:
        value = value / 100.0

    if not (0.0 <= value <= 1.0):
        raise ValueError(f"Relative humidity out of range: {value}")

    return value


def _ensure_sequence(obj, name: str):
    """
    Ensure that an object is a sequence.

    Parameters
    ----------
    obj : Any
        Object to be checked.
    name : str
        Name used in error messages.

    Returns
    -------
    obj : sequence

    Raises
    ------
    TypeError
        If the object is not iterable.
    """
    if not hasattr(obj, "__iter__"):
        raise TypeError(f"'{name}' must be a sequence")
    return obj


# =============================================================================
# Main public API
# =============================================================================
def load_chart_config(path: str | pathlib.Path) -> Dict[str, Any]:
    """
    Load and parse a psychchart YAML configuration file.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the YAML configuration file.

    Returns
    -------
    config : dict
        Dictionary with instantiated configuration objects:
        - ``cfg``      : ChartConfig
        - ``isolines`` : dict[str, IsoSet]
        - ``zones``    : list[Zone]
        - ``points``   : list[Point]

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    ValueError
        If semantic validation fails.
    """
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Top-level YAML structure must be a mapping.")

    # ------------------------------------------------------------------
    # Chart configuration
    # ------------------------------------------------------------------
    chart_data = data.get("chart", {})
    cfg = ChartConfig(**chart_data)

    # ------------------------------------------------------------------
    # Isolines
    # ------------------------------------------------------------------
    isolines: Dict[str, IsoSet] = {}
    for iso in data.get("isos", []):
        if "name" not in iso:
            raise ValueError("Each isoline must define a 'name' field.")

        name = iso["name"]
        values = _ensure_sequence(iso.get("values", []), f"isos[{name}].values")

        # Normalize RH values if applicable
        if name == "relative_humidity":
            values = [_normalize_rh(v) for v in values]

        isolines[name] = IsoSet(
            name=name,
            values=values,
            style=iso.get("style", "-"),
            color=iso.get("color"),
            cmap=iso.get("cmap"),
            enabled=iso.get("enabled", True),
        )

    # ------------------------------------------------------------------
    # Zones
    # ------------------------------------------------------------------
    zones: List[Zone] = []
    for z in data.get("zones", []):
        if "name" not in z:
            raise ValueError("Each zone must define a 'name' field.")

        rh_range = z.get("rh_range")
        if rh_range is not None:
            rh_range = [_normalize_rh(v) for v in rh_range]

        zones.append(
            Zone(
                name=z["name"],
                vertices=z.get("vertices"),
                t_range=z.get("t_range"),
                rh_range=rh_range,
                follow_rh=z.get("follow_rh", False),
                edgecolor=z.get("edgecolor", "k"),
                facecolor=z.get("facecolor"),
                linewidth=z.get("linewidth", 1.5),
            )
        )

    # ------------------------------------------------------------------
    # Points
    # ------------------------------------------------------------------
    points: List[Point] = []
    for p in data.get("points", []):
        if not {"label", "t", "rh"} <= p.keys():
            raise ValueError(
                "Each point must define 'label', 't', and 'rh'."
            )

        points.append(
            Point(
                label=p["label"],
                t=p["t"],
                rh=_normalize_rh(p["rh"]),
                marker=p.get("marker", "o"),
                color=p.get("color", "k"),
            )
        )

    return {
        "cfg": cfg,
        "isolines": isolines,
        "zones": zones,
        "points": points,
    }


# =============================================================================
# Usage examples
# =============================================================================
#
# Example 1: Load full configuration from YAML
#
# >>> from psychchart.loader import load_chart_config
# >>> config = load_chart_config("config/chart.yml")
# >>> cfg = config["cfg"]
# >>> isolines = config["isolines"]
# >>> zones = config["zones"]
# >>> points = config["points"]
#
#
# Example 2: Typical YAML file structure
#
# chart:
#   t_min: 0
#   t_max: 40
#   pressure: 101325
#   output: chart.png
#
# isos:
#   - name: relative_humidity
#     values: [30, 50, 70, 90]   # percent accepted
#     style: "--"
#
#   - name: enthalpy
#     values: [30, 40, 50]
#
# zones:
#   - name: Comfort
#     t_range: [18, 26]
#     rh_range: [40, 70]         # percent accepted
#     facecolor: lightgreen
#
# points:
#   - label: Station A
#     t: 32
#     rh: 65                    # percent accepted
#
#
# Example 3: Integration with plotting engine
#
# >>> from psychchart import PsychChart
# >>> cfg_data = load_chart_config("config/chart.yml")
# >>> chart = PsychChart(
# ...     cfg=cfg_data["cfg"],
# ...     isolines=cfg_data["isolines"],
# ...     zones=cfg_data["zones"],
# ...     points=cfg_data["points"],
# ... )
# >>> chart.draw()
#

