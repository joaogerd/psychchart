"""Streamlit interface for interactive psychChart exploration."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
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


def _apply_controls(st, data: dict) -> dict:
    edited = dict(data)
    chart = dict(edited.get("chart", {}))
    edited["chart"] = chart

    st.sidebar.subheader("Chart domain")
    chart["t_min"] = st.sidebar.number_input("T min", value=float(chart.get("t_min", 10.0)))
    chart["t_max"] = st.sidebar.number_input("T max", value=float(chart.get("t_max", 45.0)))
    chart["y_min"] = st.sidebar.number_input("W min", value=float(chart.get("y_min", 0.0)), format="%.4f")
    chart["y_max"] = st.sidebar.number_input("W max", value=float(chart.get("y_max", 0.035)), format="%.4f")
    chart["pressure"] = st.sidebar.number_input("Pressure", value=float(chart.get("pressure", 101325.0)), step=100.0)

    st.sidebar.subheader("Layers")
    if not st.sidebar.checkbox("RH isolines", value="relative_humidity" in edited.get("isolines", {})):
        isolines = dict(edited.get("isolines", {}))
        isolines.pop("relative_humidity", None)
        edited["isolines"] = isolines
    if not st.sidebar.checkbox("Index layers", value=bool(edited.get("indexes"))):
        edited["indexes"] = []
    if not st.sidebar.checkbox("Zones", value=bool(edited.get("zones"))):
        edited["zones"] = []
    if not st.sidebar.checkbox("Data layers", value=bool(edited.get("data_layers"))):
        edited["data_layers"] = []
    if not st.sidebar.checkbox("Operational overlay", value=bool(edited.get("operational_overlays"))):
        edited["operational_overlays"] = []
    elif edited.get("operational_overlays"):
        st.sidebar.subheader("Operational state")
        overlay = dict(edited["operational_overlays"][0])
        overlay["load_class"] = st.sidebar.selectbox("Load class", ["A0", "A1", "A2", "A3", "A4"], index=2)
        overlay["trend"] = st.sidebar.selectbox("Trend", ["falling", "steady", "rising"], index=1)
        overlay["alpha"] = st.sidebar.slider("Operational alpha", 0.0, 0.7, float(overlay.get("alpha", 0.18)), 0.01)
        edited["operational_overlays"] = [overlay]

    return edited


def _render(yaml_text: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "interactive.yaml"
        path.write_text(yaml_text, encoding="utf-8")
        data = load_chart_config(path)
        chart = PsychChart(**data)
        chart.draw()
        return chart.fig


def _png_bytes(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()


def _point_readout(st, pressure: float) -> None:
    st.sidebar.subheader("Point readout")
    T = st.sidebar.number_input("Readout T", value=30.0, step=0.5)
    RH_pct = st.sidebar.number_input("Readout RH (%)", value=70.0, min_value=0.0, max_value=100.0, step=1.0)
    RH = RH_pct / 100.0
    W = Psychrometrics.humidity_ratio(T, RH, pressure)
    h = Psychrometrics.enthalpy(T, W)
    Tdp = Psychrometrics.dew_point_temperature(RH, T)
    itu = ITU.compute({"T": T, "RH": RH})
    st.sidebar.metric("ITU", f"{itu:.1f}")
    st.sidebar.caption(f"W={W:.5f} kg/kg | h={h:.1f} kJ/kg | Tdp={Tdp:.1f} C")


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
    yaml_text = _dump_yaml(data)
    _point_readout(st, float(data.get("chart", {}).get("pressure", 101325.0)))

    left, right = st.columns([0.60, 0.40], gap="large")
    with right:
        st.subheader("YAML source of truth")
        yaml_text = st.text_area("Edit YAML", value=yaml_text, height=680)
        st.download_button("Download YAML", yaml_text.encode("utf-8"), "psychchart_interactive.yaml", "text/yaml")
    with left:
        st.subheader("Chart preview")
        try:
            fig = _render(yaml_text)
            st.pyplot(fig, clear_figure=False)
            st.download_button("Download PNG", _png_bytes(fig), "psychchart_interactive.png", "image/png")
            plt.close(fig)
        except Exception as exc:
            st.error(str(exc))
            st.exception(exc)


if __name__ == "__main__":
    main()
