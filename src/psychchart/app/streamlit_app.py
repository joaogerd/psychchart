"""Streamlit interface for interactive psychChart exploration."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from psychchart import PsychChart, load_chart_config
from psychchart.app.templates import TEMPLATES
from psychchart.indexes.itu import ITU
from psychchart.psychrometrics import Psychrometrics


def _require_streamlit():
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "The interactive app requires Streamlit. Install it with: pip install -e .[app]"
        ) from exc
    return st


def _load_yaml(text: str) -> dict:
    data = yaml.safe_load(text) if text.strip() else {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError("The YAML document must be a mapping at the top level.")
    return data


def _dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)


def _uploaded_text(uploaded_file) -> str | None:
    if uploaded_file is None:
        return None
    return uploaded_file.getvalue().decode("utf-8")


def _layer_count(data: dict, key: str) -> int:
    value = data.get(key)
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    return 0


def _build_report(data: dict, yaml_text: str) -> str:
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
            f"- Isoline groups: {_layer_count(data, 'isolines')}",
            f"- Index layers: {_layer_count(data, 'indexes')}",
            f"- Zones/envelopes: {_layer_count(data, 'zones')}",
            f"- Data layers: {_layer_count(data, 'data_layers')}",
            f"- Operational overlays: {_layer_count(data, 'operational_overlays')}",
            f"- Reference points: {_layer_count(data, 'points')}",
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


def _compute_point_readout(T: float, RH_pct: float, pressure: float) -> dict[str, float]:
    RH = RH_pct / 100.0
    W = Psychrometrics.humidity_ratio(T, RH, pressure)
    h = Psychrometrics.enthalpy(T, W)
    Tdp = Psychrometrics.dew_point_temperature(RH, T)
    itu = ITU.compute({"T": T, "RH": RH})
    return {"T": T, "RH_pct": RH_pct, "RH": RH, "W": W, "h": h, "Tdp": Tdp, "ITU": itu}


def _render_point_readout_sidebar(st, pressure: float) -> tuple[dict[str, float], bool]:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Point readout")
    T = st.sidebar.number_input("Readout T (°C)", value=30.0, step=0.5, key="readout_t")
    RH_pct = st.sidebar.number_input(
        "Readout RH (%)",
        value=50.0,
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key="readout_rh",
    )
    show_on_chart = st.sidebar.checkbox("Show readout point on chart", value=True)
    result = _compute_point_readout(T, RH_pct, pressure)
    st.sidebar.metric("ITU", f"{result['ITU']:.1f}")
    st.sidebar.caption(
        f"W={result['W']:.5f} kg/kg | h={result['h']:.1f} kJ/kg | "
        f"Tdp={result['Tdp']:.1f} °C"
    )
    return result, show_on_chart


def _render_point_readout_card(st, result: dict[str, float]) -> None:
    st.subheader("Point readout")
    cols = st.columns(4)
    cols[0].metric("T", f"{result['T']:.1f} °C")
    cols[1].metric("RH", f"{result['RH_pct']:.0f}%")
    cols[2].metric("ITU", f"{result['ITU']:.1f}")
    cols[3].metric("Dew point", f"{result['Tdp']:.1f} °C")
    st.caption(
        f"Humidity ratio: {result['W']:.5f} kg/kg dry air | "
        f"Enthalpy: {result['h']:.1f} kJ/kg dry air"
    )


def _inject_readout_point(data: dict, result: dict[str, float], enabled: bool) -> dict:
    edited = dict(data)
    points = []
    for item in list(edited.get("points", []) or []):
        if not str(item.get("label", "")).startswith("Readout:"):
            points.append(item)
    if enabled:
        points.append(
            {
                "t": float(result["T"]),
                "rh": float(result["RH"]),
                "label": f"Readout: T={result['T']:.1f} °C | RH={result['RH_pct']:.0f}% | ITU={result['ITU']:.1f}",
                "marker": "X",
                "color": "#000000",
                "size": 95.0,
                "alpha": 1.0,
                "zorder": 95,
                "show_label": True,
            }
        )
    edited["points"] = points
    return edited


def _apply_controls(st, data: dict) -> dict:
    edited = dict(data)
    chart = dict(edited.get("chart", {}))
    edited["chart"] = chart

    with st.sidebar.expander("Chart domain", expanded=True):
        chart["t_min"] = st.number_input("T min", value=float(chart.get("t_min", 10.0)))
        chart["t_max"] = st.number_input("T max", value=float(chart.get("t_max", 45.0)))
        chart["y_min"] = st.number_input("W min", value=float(chart.get("y_min", 0.0)), format="%.4f")
        chart["y_max"] = st.number_input("W max", value=float(chart.get("y_max", 0.035)), format="%.4f")
        chart["pressure"] = st.number_input("Pressure", value=float(chart.get("pressure", 101325.0)), step=100.0)

    with st.sidebar.expander("Layer manager", expanded=True):
        if not st.checkbox("RH isolines", value="relative_humidity" in edited.get("isolines", {})):
            isolines = dict(edited.get("isolines", {}))
            isolines.pop("relative_humidity", None)
            edited["isolines"] = isolines
        if not st.checkbox("Index layers", value=bool(edited.get("indexes"))):
            edited["indexes"] = []
        if not st.checkbox("Zones", value=bool(edited.get("zones"))):
            edited["zones"] = []
        if not st.checkbox("Data layers", value=bool(edited.get("data_layers"))):
            edited["data_layers"] = []
        if not st.checkbox("Operational overlay", value=bool(edited.get("operational_overlays"))):
            edited["operational_overlays"] = []

    if edited.get("operational_overlays"):
        with st.sidebar.expander("Operational state", expanded=True):
            overlay = dict(edited["operational_overlays"][0])
            overlay["load_class"] = st.selectbox("Load class", ["A0", "A1", "A2", "A3", "A4"], index=2)
            overlay["trend"] = st.selectbox("Trend", ["falling", "steady", "rising"], index=1)
            overlay["alpha"] = st.slider("Operational alpha", 0.0, 0.7, float(overlay.get("alpha", 0.18)), 0.01)
            edited["operational_overlays"] = [overlay]

    return edited


def _apply_csv_import(st, data: dict) -> dict:
    with st.sidebar.expander("CSV data import", expanded=False):
        uploaded_csv = st.file_uploader("Overlay CSV", type=["csv"], key="csv_overlay")
        if uploaded_csv is None:
            return data
        df = pd.read_csv(uploaded_csv)
        columns = list(df.columns)
        if not columns:
            return data
        t_col = st.selectbox("Temperature column", columns, index=0)
        rh_col = st.selectbox("RH column", columns, index=min(1, len(columns) - 1))
        time_options = ["<none>"] + columns
        time_col = st.selectbox("Time/order column", time_options, index=0)
        value_options = ["<none>"] + columns
        value_col = st.selectbox("Class/value column", value_options, index=0)
        render_mode = st.selectbox("CSV render", ["scatter", "path", "classified_points"], index=0)
        replace_existing = st.checkbox("Replace existing data layers", value=True)

    path = Path(tempfile.gettempdir()) / "psychchart_streamlit_overlay.csv"
    df.to_csv(path, index=False)
    layer: dict[str, Any] = {
        "data": str(path),
        "format": "csv",
        "projection": {"t_col": t_col, "rh_col": rh_col, "rh_unit": "auto"},
        "fields": [],
        "render": [],
    }
    if time_col != "<none>":
        layer["temporal"] = {"time_col": time_col, "sort": True}
    if value_col != "<none>":
        layer["fields"].append({"type": "direct_column", "name": "csv_value", "col": value_col})
    if render_mode == "path":
        layer["render"].append({"type": "path", "order_by": None if time_col == "<none>" else time_col, "color": "#264653", "linewidth": 2.0, "alpha": 0.9, "zorder": 60})
    elif render_mode == "classified_points" and value_col != "<none>":
        layer["render"].append({"type": "classified_points", "value_col": "csv_value", "profile": "CTA", "size": 42, "alpha": 0.9, "edgecolor": "black", "edgewidth": 0.4, "zorder": 65})
    else:
        render = {"type": "scatter", "size": 26, "alpha": 0.75, "edgecolor": "black", "edgewidth": 0.3, "zorder": 65}
        if value_col != "<none>":
            render["value"] = "csv_value"
            render["colorbar"] = True
        layer["render"].append(render)
    edited = dict(data)
    edited["data_layers"] = [layer] if replace_existing else list(edited.get("data_layers", []) or []) + [layer]
    return edited


def _render(yaml_text: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "interactive.yaml"
        path.write_text(yaml_text, encoding="utf-8")
        data = load_chart_config(path)
        chart = PsychChart(**data)
        chart.draw()
        return chart.fig


def _figure_bytes(fig, fmt: str, dpi: int = 180) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format=fmt, dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()


def main() -> None:
    st = _require_streamlit()
    st.set_page_config(page_title="psychChart interactive", layout="wide")
    st.title("psychChart interactive")
    st.caption("Interactive YAML-driven psychrometric and bovine bioclimatic chart explorer.")

    template = st.sidebar.selectbox("Template", list(TEMPLATES), index=0)
    upload = st.sidebar.file_uploader("Load YAML", type=["yaml", "yml"])
    if "yaml_text" not in st.session_state or st.sidebar.button("Reset from template"):
        st.session_state.yaml_text = TEMPLATES[template]
    if (text := _uploaded_text(upload)) is not None:
        st.session_state.yaml_text = text

    data = _apply_controls(st, _load_yaml(st.session_state.yaml_text))
    data = _apply_csv_import(st, data)
    point_readout, show_readout_point = _render_point_readout_sidebar(st, float(data.get("chart", {}).get("pressure", 101325.0)))
    data = _inject_readout_point(data, point_readout, show_readout_point)
    yaml_text = _dump_yaml(data)
    report_text = _build_report(data, yaml_text)

    left, right = st.columns([0.60, 0.40], gap="large")
    with right:
        _render_point_readout_card(st, point_readout)
        st.subheader("YAML source of truth")
        yaml_text = st.text_area("Edit YAML", value=yaml_text, height=620)
        st.download_button("Download YAML", yaml_text.encode("utf-8"), "psychchart_interactive.yaml", "text/yaml")
        st.download_button("Download report", report_text.encode("utf-8"), "psychchart_report.md", "text/markdown")
    with left:
        st.subheader("Chart preview")
        try:
            fig = _render(yaml_text)
            st.pyplot(fig, clear_figure=False)
            export_cols = st.columns(3)
            with export_cols[0]:
                st.download_button("PNG", _figure_bytes(fig, "png"), "psychchart_interactive.png", "image/png")
            with export_cols[1]:
                st.download_button("SVG", _figure_bytes(fig, "svg"), "psychchart_interactive.svg", "image/svg+xml")
            with export_cols[2]:
                st.download_button("PDF", _figure_bytes(fig, "pdf"), "psychchart_interactive.pdf", "application/pdf")
            plt.close(fig)
        except Exception as exc:
            st.error(str(exc))
            st.exception(exc)


if __name__ == "__main__":
    main()
