# Getting started with psychChart

This guide shows how to install psychChart, validate the local environment and render the main example charts.

psychChart is designed around declarative YAML files. A configuration file describes the psychrometric domain, physical isolines, indexes, data layers, semantic labels and optional operational overlays. The CLI loads the YAML, validates it with Pydantic and renders the chart.

---

## 1. Install from source

From the repository root:

```bash
python -m pip install -e ".[dev]"
```

For the Streamlit interface:

```bash
python -m pip install -e ".[app]"
```

For the FastAPI interface:

```bash
python -m pip install -e ".[api]"
```

For Parquet input support:

```bash
python -m pip install -e ".[parquet]"
```

---

## 2. Validate the installation

Run the test suite:

```bash
pytest
```

Then render the main smoke-tested examples:

```bash
psychchart examples/itu_field_labels.yaml
psychchart examples/operational_overlay_minimal.yaml
psychchart examples/thermal_trajectory_classified.yaml
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

All commands should be executed from the repository root because the example YAML files use repository-relative paths such as `examples/data/animal_day.csv`.

---

## 3. Minimal workflow

The standard CLI workflow is:

```text
YAML configuration
   ↓
load_chart_config()
   ↓
PsychChart(**data)
   ↓
chart.draw()
   ↓
PNG / PDF output
```

A typical command is:

```bash
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

When successful, the CLI prints a message like:

```text
[OK] Chart successfully saved to 'bovine_bioclimatic_final_azevedo.png'
```

---

## 4. Basic YAML structure

A chart configuration usually contains some of these top-level sections:

```yaml
chart:
  t_min: 10
  t_max: 45
  y_min: 0.0
  y_max: 0.035
  pressure: 101325
  output: chart.png

isolines:
  relative_humidity:
    enabled: true
    values: [0.2, 0.4, 0.6, 0.8, 1.0]

indexes:
  - index: ITU
    render:
      isolines:
        levels: [72, 78, 84]
        label: true

points:
  - label: Example point
    t: 31
    rh: 0.65
```

The `chart` section defines the physical domain and output. Other sections add visual layers.

---

## 5. Index fields and semantic labels

Index fields are continuous fields calculated over the psychrometric domain. Their semantic labels can be drawn directly inside the chart:

```yaml
indexes:
  - index: ITU
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert", "Stress"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: true
        label_fontsize: 22
```

Manual label positions can be configured with either `t`/`w` or `t`/`rh` coordinates:

```yaml
render:
  field:
    labels: true
    label_positions:
      - label: Comfort
        t: 18
        rh: 60
```

Run the complete example:

```bash
psychchart examples/itu_field_labels.yaml
```

---

## 6. Data layers

Data layers load observations from CSV or Parquet files and draw them as points, paths, density fields, scalar fields or annotations.

Example:

```yaml
data_layers:
  - data: examples/data/animal_day.csv
    format: csv
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
        color: black
      - type: scatter
        value: CTA
        cmap: viridis
```

Useful examples:

```bash
psychchart examples/example_points.yaml
psychchart examples/example_mixed.yaml
psychchart examples/path_scatter_annotate_cta.yaml
```

---

## 7. Operational overlays

Operational overlays project a declared management policy onto the psychrometric chart. They are useful when the chart must support decisions such as ventilation, sprinkling, maximum cooling or emergency response.

Minimal example:

```yaml
operational_overlays:
  - load_class: A2
    trend: steady
    alpha: 0.20
    show_boundaries: true
    show_legend: true
```

When no explicit profile is provided, psychChart injects the built-in `dairy_cooling_default` profile.

Run:

```bash
psychchart examples/operational_overlay_minimal.yaml
```

Read the full operational overlay guide:

```text
docs/OPERATIONAL_OVERLAYS.md
```

---

## 8. Python usage

YAML remains the recommended interface for reproducible figures, but the same workflow can be used from Python:

```python
from psychchart import PsychChart, load_chart_config

cfg = load_chart_config("examples/itu_field_labels.yaml")
chart = PsychChart(**cfg)
chart.draw()
chart.fig.savefig("chart.png", dpi=200)
```

---

## 9. Where to go next

Use these files as entry points:

- `examples/README.txt` for validated example commands;
- `docs/OPERATIONAL_OVERLAYS.md` for decision overlays;
- `docs/BOVINE_BIOCLIMATIC_CHART.md` for the bovine bioclimatic chart concept;
- `docs/api_usage.md` for FastAPI usage;
- `CHANGELOG.md` for release history.

