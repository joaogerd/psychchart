"""Built-in YAML templates for the optional interactive app."""

from __future__ import annotations

BOVINE_BIOCLIMATIC_TEMPLATE = """
profile: default_si

chart:
  t_min: 10
  t_max: 45
  y_min: 0.0
  y_max: 0.035
  pressure: 101325
  xlabel: "Dry-bulb temperature (°C)"
  ylabel: "Humidity ratio (kg/kg dry air)"
  title: "Interactive bovine bioclimatic chart"
  output: "interactive_bovine_bioclimatic.png"
  dpi: 180
  grid: true
  figsize: [14, 8]
  show_tw_grid: true
  tw_grid:
    vertical: true
    horizontal: true
    every:
      T: 5.0
      W: 0.005
  tw_grid_style:
    color: "#8a8a8a"
    linewidth: 0.45
    linestyle: "-"
    alpha: 0.22
  legend:
    show: true
    loc: "upper left"
    title: "Accumulated thermal-load state"
    frameon: true
    fancybox: true
    framealpha: 0.88
    fontsize: 8.5
    title_fontsize: 9.5
    entries:
      - type: classes_from_profile
        profile: CTA

isolines:
  relative_humidity:
    enabled: true
    values: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    color: "#6E3F4D"
    linestyle: "-"
    linewidth: 0.62
    alpha: 0.46
    labels: true
    label_fontsize: 7
    label_fmt: "{value:.0%}"

indexes:
  - index: ITU
    label: "Temperature-Humidity Index (ITU)"
    levels: [60, 72, 76, 77, 79, 84, 89, 98]
    cmap: "Spectral_r"
    vmin: 60
    vmax: 98
    render:
      field:
        alpha: 0.42
        colorbar: true

  - index: ITU
    label: "Critical ITU thresholds"
    render:
      isolines:
        levels: [72, 76, 77, 79, 84, 89]
        style: "-"
        color: "#111111"
        linewidth: 1.05
        alpha: 0.92
        label: true
        label_fontsize: 8
        label_fmt: "ITU {value:.0f}"

zones:
  - name: "Experimental envelope"
    t_range: [10, 34]
    rh_range: [26, 100]
    follow_rh: true
    edgecolor: "#111111"
    facecolor: "none"
    linewidth: 3.0
    alpha: 0.0
    show_label: true
    label: "Experimental envelope\n10–34 °C | RH 26–100%"
    label_t: 16.3
    label_rh: 90
    label_color: "#111111"
    label_fontsize: 9.0

  - name: "Winter morning"
    t_range: [10, 25]
    rh_range: [48, 100]
    follow_rh: true
    edgecolor: "#1F77B4"
    facecolor: "none"
    linewidth: 2.2
    alpha: 0.0
    show_label: true
    label: "Winter\nmorning"
    label_t: 16.0
    label_rh: 63
    label_color: "#1F77B4"
    label_fontsize: 9.0

  - name: "Winter afternoon"
    t_range: [18, 31]
    rh_range: [26, 90]
    follow_rh: true
    edgecolor: "#2E7D32"
    facecolor: "none"
    linewidth: 2.2
    alpha: 0.0
    show_label: true
    label: "Winter\nafternoon"
    label_t: 24.5
    label_rh: 34
    label_color: "#2E7D32"
    label_fontsize: 9.0

  - name: "Summer morning"
    t_range: [18, 29]
    rh_range: [52, 100]
    follow_rh: true
    edgecolor: "#B7950B"
    facecolor: "none"
    linewidth: 2.4
    alpha: 0.0
    show_label: true
    label: "Summer\nmorning"
    label_t: 22.8
    label_rh: 81
    label_color: "#8A6D00"
    label_fontsize: 9.0

  - name: "Summer afternoon"
    t_range: [21, 34]
    rh_range: [33, 100]
    follow_rh: true
    edgecolor: "#C0392B"
    facecolor: "none"
    linewidth: 2.5
    alpha: 0.0
    show_label: true
    label: "Summer\nafternoon"
    label_t: 30.0
    label_rh: 47
    label_color: "#922B21"
    label_fontsize: 9.0

data_layers:
  - data: "examples/data/animal_day.csv"
    format: "csv"
    projection:
      t_col: temp
      rh_col: rh
      rh_unit: auto
    temporal:
      time_col: hour
      sort: true
    fields:
      - type: direct_column
        name: CTA
        col: cta_acumulada
    render:
      - type: path
        order_by: hour
        color: "#264653"
        alpha: 0.88
        linewidth: 2.4
        linestyle: "-"
        label: "Thermal trajectory"
        zorder: 42
      - type: classified_points
        value_col: CTA
        profile: CTA
        order_by: hour
        size: 58
        alpha: 1.0
        edgecolor: "#111111"
        edgewidth: 0.75
        marker: "o"
        label: "Hourly accumulated-load state"
        zorder: 45
      - type: annotate
        every: 2
        template: "{time:.0f}h"
        time_field: hour
        value_field: CTA
        dx: 0.035
        dy: 0.00055
        fontsize: 7.8
        fontweight: bold
        color: "#111111"
        zorder: 50

operational_overlays:
  - load_class: A2
    trend: steady
    alpha: 0.18
    zorder: 0.55
    show_boundaries: true

points: []
observations: []
temporal_overlays: []
""".strip()

MINIMAL_TEMPLATE = """
profile: default_si

chart:
  t_min: 10
  t_max: 45
  y_min: 0.0
  y_max: 0.035
  pressure: 101325
  title: "Interactive psychrometric chart"
  output: "interactive_psychchart.png"
  dpi: 180

isolines:
  relative_humidity:
    enabled: true
    values: [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels: true
    label_fmt: "{value:.0%}"

indexes:
  - index: ITU
    label: ITU
    levels: [60, 72, 78, 84, 90, 98]
    cmap: Spectral_r
    render:
      field:
        alpha: 0.45
        colorbar: true
""".strip()

TEMPLATES = {
    "Bovine bioclimatic chart": BOVINE_BIOCLIMATIC_TEMPLATE,
    "Minimal ITU chart": MINIMAL_TEMPLATE,
}
