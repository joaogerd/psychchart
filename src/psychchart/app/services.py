"""Reusable services for interactive psychChart applications.

This module contains the application-facing operations that are shared by the
optional Streamlit interface and by any future front-end, such as a FastAPI
service consumed by a React/Vite client.  The functions are intentionally free
from Streamlit imports so they can be tested, reused, cached and documented as a
stable application boundary around the scientific core.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
import tempfile
from pathlib import Path
from typing import Any, Mapping

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from psychchart import PsychChart, load_chart_config
from psychchart.indexes.itu import ITU
from psychchart.psychrometrics import Psychrometrics


DEFAULT_OPERATIONAL_OVERLAY: dict[str, Any] = {
    "load_class": "A2",
    "trend": "steady",
    "alpha": 0.18,
    "zorder": 0.55,
    "show_boundaries": True,
}


@dataclass(frozen=True)
class PointReadout:
    """Computed psychrometric readout for one temperature/RH state."""

    T: float
    RH_pct: float
    RH: float
    W: float
    h: float
    Tdp: float
    ITU: float

    def as_dict(self) -> dict[str, float]:
        """Return the readout as a plain dictionary for UI code."""
        return {
            "T": self.T,
            "RH_pct": self.RH_pct,
            "RH": self.RH,
            "W": self.W,
            "h": self.h,
            "Tdp": self.Tdp,
            "ITU": self.ITU,
        }


@dataclass(frozen=True)
class CsvLayerOptions:
    """Options used to convert an uploaded CSV into a data layer."""

    t_col: str
    rh_col: str
    time_col: str | None = None
    value_col: str | None = None
    render_mode: str = "scatter"
    replace_existing: bool = True
    temp_filename: str = "psychchart_streamlit_overlay.csv"


def load_yaml_text(text: str) -> dict[str, Any]:
    """Parse a YAML string and require a top-level mapping.

    Parameters
    ----------
    text : str
        YAML document provided by the user or by a built-in template.

    Returns
    -------
    dict[str, Any]
        Parsed mapping. Blank documents become an empty mapping.

    Raises
    ------
    TypeError
        If the YAML document does not contain a top-level mapping.
    """
    data = yaml.safe_load(text) if text.strip() else {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError("The YAML document must be a mapping at the top level.")
    return data


def dump_yaml(data: Mapping[str, Any]) -> str:
    """Serialize a mapping to stable, human-readable YAML."""
    return yaml.safe_dump(
        dict(data),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def is_empty_layer_value(value: Any) -> bool:
    """Return True for values that should be treated as an absent layer."""
    return value is None or value == [] or value == {}


def layer_count(data: Mapping[str, Any], key: str) -> int:
    """Count active items in a top-level configuration section."""
    value = data.get(key)
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    return 0


def build_report(data: Mapping[str, Any], yaml_text: str) -> str:
    """Build a small Markdown reproducibility report for a chart."""
    chart = data.get("chart", {}) or {}
    return "\n".join(
        [
            "# psychChart interactive report",
            "",
            "## Chart domain",
            f"- Temperature range: {chart.get('t_min')} to {chart.get('t_max')} °C",
            f"- Humidity-ratio range: {chart.get('y_min')} to {chart.get('y_max')} kg/kg dry air",
            f"- Pressure: {chart.get('pressure')} Pa",
            f"- Title: {chart.get('title', '')}",
            "",
            "## Active sections",
            f"- Isoline groups: {layer_count(data, 'isolines')}",
            f"- Index layers: {layer_count(data, 'indexes')}",
            f"- Zones/envelopes: {layer_count(data, 'zones')}",
            f"- Data layers: {layer_count(data, 'data_layers')}",
            f"- Operational overlays: {layer_count(data, 'operational_overlays')}",
            f"- Reference points: {layer_count(data, 'points')}",
            "",
            "## Reproducibility note",
            "This report was generated from the YAML configuration below. The YAML is the source of truth for the chart.",
            "",
            "```yaml",
            yaml_text.rstrip(),
            "```",
            "",
        ]
    )


def compute_point_readout(T: float, RH_pct: float, pressure: float) -> PointReadout:
    """Compute psychrometric quantities and ITU for one point."""
    RH = RH_pct / 100.0
    W = Psychrometrics.humidity_ratio(T, RH, pressure)
    h = Psychrometrics.enthalpy(T, W)
    Tdp = Psychrometrics.dew_point_temperature(RH, T)
    itu = ITU.compute({"T": T, "RH": RH})
    return PointReadout(T=T, RH_pct=RH_pct, RH=RH, W=W, h=h, Tdp=Tdp, ITU=itu)


def inject_readout_point(data: Mapping[str, Any], result: PointReadout, enabled: bool) -> dict[str, Any]:
    """Return a config copy with the optional readout point injected."""
    edited = dict(data)
    points = []
    for item in list(edited.get("points", []) or []):
        if not str(item.get("label", "")).startswith("Readout:"):
            points.append(item)

    if enabled:
        points.append(
            {
                "t": float(result.T),
                "rh": float(result.RH),
                "label": f"Readout: T={result.T:.1f} °C | RH={result.RH_pct:.0f}% | ITU={result.ITU:.1f}",
                "marker": "corner_cross",
                "color": "#000000",
                "size": 420.0,
                "alpha": 1.0,
                "zorder": 95,
                "show_label": True,
            }
        )

    edited["points"] = points
    return edited


def ensure_operational_overlay(data: Mapping[str, Any]) -> dict[str, Any]:
    """Ensure that a config contains at least one operational overlay."""
    edited = dict(data)
    overlays = list(edited.get("operational_overlays", []) or [])
    if not overlays:
        overlays = [dict(DEFAULT_OPERATIONAL_OVERLAY)]
    edited["operational_overlays"] = overlays
    return edited


def build_csv_data_layer(df: pd.DataFrame, options: CsvLayerOptions) -> dict[str, Any]:
    """Persist an uploaded CSV temporarily and return a canonical data layer."""
    path = Path(tempfile.gettempdir()) / options.temp_filename
    df.to_csv(path, index=False)

    layer: dict[str, Any] = {
        "data": str(path),
        "format": "csv",
        "projection": {"t_col": options.t_col, "rh_col": options.rh_col, "rh_unit": "auto"},
        "fields": [],
        "render": [],
    }

    if options.time_col is not None:
        layer["temporal"] = {"time_col": options.time_col, "sort": True}

    if options.value_col is not None:
        layer["fields"].append({"type": "direct_column", "name": "csv_value", "col": options.value_col})

    if options.render_mode == "path":
        layer["render"].append(
            {
                "type": "path",
                "order_by": options.time_col,
                "color": "#264653",
                "linewidth": 2.0,
                "alpha": 0.9,
                "zorder": 60,
            }
        )
    elif options.render_mode == "classified_points" and options.value_col is not None:
        layer["render"].append(
            {
                "type": "classified_points",
                "value_col": "csv_value",
                "profile": "CTA",
                "size": 42,
                "alpha": 0.9,
                "edgecolor": "black",
                "edgewidth": 0.4,
                "zorder": 65,
            }
        )
    else:
        render: dict[str, Any] = {
            "type": "scatter",
            "size": 26,
            "alpha": 0.75,
            "edgecolor": "black",
            "edgewidth": 0.3,
            "zorder": 65,
        }
        if options.value_col is not None:
            render["value"] = "csv_value"
            render["colorbar"] = True
        layer["render"].append(render)

    return layer


def apply_csv_layer(data: Mapping[str, Any], layer: Mapping[str, Any], replace_existing: bool = True) -> dict[str, Any]:
    """Return a config copy with a CSV-derived data layer applied."""
    edited = dict(data)
    existing = list(edited.get("data_layers", []) or [])
    edited["data_layers"] = [dict(layer)] if replace_existing else existing + [dict(layer)]
    return edited


def render_figure_from_yaml(yaml_text: str):
    """Render a chart from YAML text and return the Matplotlib figure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "interactive.yaml"
        path.write_text(yaml_text, encoding="utf-8")
        payload = load_chart_config(path)
        chart = PsychChart(**payload)
        chart.draw()
        return chart.fig


def figure_to_bytes(fig, fmt: str, dpi: int = 180) -> bytes:
    """Serialize a Matplotlib figure to bytes in the requested format."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format=fmt, dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()


def close_figure(fig) -> None:
    """Close a Matplotlib figure created by the app layer."""
    plt.close(fig)
