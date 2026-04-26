"""Streamlit interface for interactive psychChart exploration.

The Streamlit module intentionally contains only UI orchestration. Reusable
application logic lives in :mod:`psychchart.app.services`, which keeps this app
thin and allows the same operations to be reused by tests, notebooks, CLI tools
or a future HTTP API.
"""

from __future__ import annotations

import copy
from typing import Any

import pandas as pd

from psychchart.app.services import (
    CsvLayerOptions,
    PointReadout,
    apply_csv_layer,
    build_csv_data_layer,
    build_report,
    close_figure,
    compute_point_readout,
    dump_yaml,
    ensure_operational_overlay,
    figure_to_bytes,
    inject_readout_point,
    is_empty_layer_value,
    load_yaml_text,
    render_figure_from_yaml,
)
from psychchart.app.templates import TEMPLATES


def _require_streamlit():
    """Import Streamlit lazily so the core package can be used without it."""
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "The interactive app requires Streamlit. Install it with: pip install -e .[app]"
        ) from exc
    return st


def _uploaded_text(uploaded_file) -> str | None:
    """Return uploaded text content or None when no file was provided."""
    if uploaded_file is None:
        return None
    return uploaded_file.getvalue().decode("utf-8")


def _template_data(template_name: str) -> dict[str, Any]:
    """Return a deep-copied mapping for a built-in template."""
    return copy.deepcopy(load_yaml_text(TEMPLATES.get(template_name, "")))


def _template_section(template_name: str, section: str, fallback: Any) -> Any:
    """Return a deep-copied section from a built-in template."""
    data = _template_data(template_name)
    return copy.deepcopy(data.get(section, fallback))


def _restore_or_hide_section(st, data: dict, section: str, enabled: bool, template_name: str, fallback: Any) -> dict:
    """Restore a UI-managed section from session cache or hide it."""
    edited = dict(data)
    cache_key = f"layer_manager_cache_{section}"

    if enabled:
        current = edited.get(section)
        if is_empty_layer_value(current):
            cached = st.session_state.get(cache_key)
            restored = cached if not is_empty_layer_value(cached) else _template_section(template_name, section, fallback)
            edited[section] = copy.deepcopy(restored)
        return edited

    current = edited.get(section)
    if not is_empty_layer_value(current):
        st.session_state[cache_key] = copy.deepcopy(current)
    edited[section] = copy.deepcopy(fallback)
    return edited


def _restore_or_hide_relative_humidity(st, data: dict, enabled: bool, template_name: str) -> dict:
    """Restore or remove the relative-humidity isoline group."""
    edited = dict(data)
    isolines = dict(edited.get("isolines", {}) or {})
    cache_key = "layer_manager_cache_relative_humidity"

    if enabled:
        if "relative_humidity" not in isolines:
            cached = st.session_state.get(cache_key)
            template_isolines = _template_section(template_name, "isolines", {}) or {}
            restored = cached if not is_empty_layer_value(cached) else template_isolines.get("relative_humidity")
            if restored is not None:
                isolines["relative_humidity"] = copy.deepcopy(restored)
        edited["isolines"] = isolines
        return edited

    if "relative_humidity" in isolines:
        st.session_state[cache_key] = copy.deepcopy(isolines["relative_humidity"])
        isolines.pop("relative_humidity", None)
    edited["isolines"] = isolines
    return edited


def _apply_controls(st, data: dict, template_name: str) -> dict:
    """Apply sidebar controls to the current YAML-derived configuration."""
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
        show_rh = st.checkbox("RH isolines", value="relative_humidity" in (edited.get("isolines", {}) or {}))
        edited = _restore_or_hide_relative_humidity(st, edited, show_rh, template_name)

        show_indexes = st.checkbox("Index layers", value=not is_empty_layer_value(edited.get("indexes")))
        edited = _restore_or_hide_section(st, edited, "indexes", show_indexes, template_name, [])

        show_zones = st.checkbox("Zones", value=not is_empty_layer_value(edited.get("zones")))
        edited = _restore_or_hide_section(st, edited, "zones", show_zones, template_name, [])

        show_data_layers = st.checkbox("Data layers", value=not is_empty_layer_value(edited.get("data_layers")))
        edited = _restore_or_hide_section(st, edited, "data_layers", show_data_layers, template_name, [])

        show_operational = st.checkbox(
            "Management layer",
            value=not is_empty_layer_value(edited.get("operational_overlays")),
            help="Draw the operational cooling-management overlay.",
        )
        edited = _restore_or_hide_section(st, edited, "operational_overlays", show_operational, template_name, [])
        if show_operational:
            edited = ensure_operational_overlay(edited)

    if edited.get("operational_overlays"):
        with st.sidebar.expander("Management state", expanded=True):
            overlay = dict(edited["operational_overlays"][0])
            load_classes = ["A0", "A1", "A2", "A3", "A4"]
            trends = ["falling", "steady", "rising"]
            overlay["load_class"] = st.selectbox("Load class", load_classes, index=load_classes.index(overlay.get("load_class", "A2")))
            overlay["trend"] = st.selectbox("Trend", trends, index=trends.index(overlay.get("trend", "steady")))
            overlay["alpha"] = st.slider("Management alpha", 0.0, 0.7, float(overlay.get("alpha", 0.18)), 0.01)
            overlay["zorder"] = st.slider("Management z-order", 0.0, 10.0, float(overlay.get("zorder", 0.55)), 0.05)
            overlay["show_boundaries"] = st.checkbox("Show management boundaries", value=bool(overlay.get("show_boundaries", True)))
            edited["operational_overlays"] = [overlay]

    return edited


def _apply_csv_import(st, data: dict) -> dict:
    """Apply an uploaded CSV file as a canonical data layer."""
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
        value_options = ["<none>"] + columns
        time_col = st.selectbox("Time/order column", time_options, index=0)
        value_col = st.selectbox("Class/value column", value_options, index=0)
        render_mode = st.selectbox("CSV render", ["scatter", "path", "classified_points"], index=0)
        replace_existing = st.checkbox("Replace existing data layers", value=True)

    options = CsvLayerOptions(
        t_col=t_col,
        rh_col=rh_col,
        time_col=None if time_col == "<none>" else time_col,
        value_col=None if value_col == "<none>" else value_col,
        render_mode=render_mode,
        replace_existing=replace_existing,
    )
    layer = build_csv_data_layer(df, options)
    return apply_csv_layer(data, layer, replace_existing=replace_existing)


def _select_template_yaml(st, template_name: str, uploaded_text: str | None) -> str:
    """Select the active YAML document from upload, session state or template."""
    if uploaded_text is not None:
        st.session_state.yaml_text = uploaded_text
        st.session_state.active_template = None
        return st.session_state.yaml_text

    reset_requested = st.sidebar.button("Reset from template")
    template_changed = st.session_state.get("active_template") != template_name
    if "yaml_text" not in st.session_state or reset_requested or template_changed:
        st.session_state.yaml_text = TEMPLATES[template_name]
        st.session_state.active_template = template_name
    return st.session_state.yaml_text


def _render_point_readout_sidebar(st, pressure: float) -> tuple[PointReadout, bool]:
    """Render the sidebar controls for point readout."""
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
    result = compute_point_readout(T, RH_pct, pressure)
    st.sidebar.metric("ITU", f"{result.ITU:.1f}")
    st.sidebar.caption(
        f"W={result.W:.5f} kg/kg | h={result.h:.1f} kJ/kg | Tdp={result.Tdp:.1f} °C"
    )
    return result, show_on_chart


def _render_point_readout_card(st, result: PointReadout) -> None:
    """Render the main-panel point readout metrics."""
    st.subheader("Point readout")
    cols = st.columns(4)
    cols[0].metric("T", f"{result.T:.1f} °C")
    cols[1].metric("RH", f"{result.RH_pct:.0f}%")
    cols[2].metric("ITU", f"{result.ITU:.1f}")
    cols[3].metric("Dew point", f"{result.Tdp:.1f} °C")
    st.caption(f"Humidity ratio: {result.W:.5f} kg/kg dry air | Enthalpy: {result.h:.1f} kJ/kg dry air")


def main() -> None:
    """Run the interactive Streamlit application."""
    st = _require_streamlit()

    st.set_page_config(page_title="psychChart interactive", layout="wide")
    st.title("psychChart interactive")
    st.caption("Interactive YAML-driven psychrometric and bovine bioclimatic chart explorer.")

    template = st.sidebar.selectbox("Template", list(TEMPLATES), index=0)
    upload = st.sidebar.file_uploader("Load YAML", type=["yaml", "yml"])
    active_yaml_text = _select_template_yaml(st, template, _uploaded_text(upload))

    data = _apply_controls(st, load_yaml_text(active_yaml_text), template)
    data = _apply_csv_import(st, data)

    point_readout, show_readout_point = _render_point_readout_sidebar(
        st,
        float(data.get("chart", {}).get("pressure", 101325.0)),
    )
    data = inject_readout_point(data, point_readout, show_readout_point)

    yaml_text = dump_yaml(data)
    report_text = build_report(data, yaml_text)

    left, right = st.columns([0.60, 0.40], gap="large")

    with right:
        _render_point_readout_card(st, point_readout)
        st.subheader("YAML source of truth")
        yaml_text = st.text_area("Edit YAML", value=yaml_text, height=620)
        st.session_state.yaml_text = yaml_text
        st.download_button("Download YAML", yaml_text.encode("utf-8"), "psychchart_interactive.yaml", "text/yaml")
        st.download_button("Download report", report_text.encode("utf-8"), "psychchart_report.md", "text/markdown")

    with left:
        st.subheader("Chart preview")
        try:
            fig = render_figure_from_yaml(yaml_text)
            st.pyplot(fig, clear_figure=False)
            export_cols = st.columns(3)
            with export_cols[0]:
                st.download_button("PNG", figure_to_bytes(fig, "png"), "psychchart_interactive.png", "image/png")
            with export_cols[1]:
                st.download_button("SVG", figure_to_bytes(fig, "svg"), "psychchart_interactive.svg", "image/svg+xml")
            with export_cols[2]:
                st.download_button("PDF", figure_to_bytes(fig, "pdf"), "psychchart_interactive.pdf", "application/pdf")
            close_figure(fig)
        except Exception as exc:
            st.error(str(exc))
            st.exception(exc)


if __name__ == "__main__":
    main()
