# psychchart

**psychchart** is a Python package for generating **psychrometric charts** using a
**declarative, YAML-driven configuration**.

It is designed for **scientific reproducibility**, **educational use**, and
**applied research** in areas such as:

- thermal comfort (human and animal)
- bioclimatology
- building physics
- environmental and agricultural sciences
- heat stress analysis (e.g. Givoni, ITU, HLI)
- bovine bioclimatic decision charts

The package separates **physics**, **configuration**, **data layers**, and
**visualization**, enabling transparent and reproducible workflows.

---

## Key features

- 📄 **YAML-driven configuration** (no hard-coded plots)
- 🔬 **Scientifically consistent psychrometric formulations**
- 📊 **Matplotlib-based rendering**
- 🧱 Clear separation of concerns:
  - configuration schema
  - psychrometric calculations
  - index computation
  - data-layer processing
  - plotting engine
  - operational decision overlays
- 🧪 Automated tests for numerical consistency and plotting stability
- 🧩 Extensible architecture for ITU, HLI, thermal excess, custom zones, data layers, and operational overlays
- 🐄 Bovine bioclimatic chart examples combining ITU fields, literature envelopes, accumulated load, and cooling-management regions

---

## Scientific scope and assumptions

All psychrometric formulations assume:

- Dry-bulb temperature in **degrees Celsius (°C)**
- Atmospheric pressure in **Pascals (Pa)**
- Relative humidity as fraction or percent, normalized internally
- Humidity ratio in **kg water vapor / kg dry air**

The implemented equations are consistent with **classical psychrometric theory**
(e.g. ASHRAE Fundamentals) and are intended for:

- psychrometric diagram construction
- comparative and educational analysis
- thermal comfort assessment
- animal heat-stress visualization
- decision-support chart prototyping

They are **not** intended for high-precision HVAC engineering design.

---

## Installation

```bash
pip install psychchart
```

For development:

```bash
pip install -e .[dev]
```

For parquet data layers:

```bash
pip install -e .[parquet]
```

Python ≥ 3.10 is required.

---

## Quick start (minimal example)

Create a minimal YAML file:

```yaml
profile: default_si

chart:
  t_min: 0
  t_max: 35

isolines:
  relative_humidity:
    values: [40, 60, 80]
```

Generate the chart via CLI:

```bash
psychchart minimal.yaml
```

This produces a valid psychrometric chart with:

- saturation curve (100% RH)
- relative humidity isolines at 40%, 60% and 80%

---

## Bovine bioclimatic chart

psychChart can now be used to build a Givoni-like **bovine bioclimatic chart**.
The goal is not only to diagnose where a T x RH point falls, but to combine:

- physical psychrometric structure;
- thermal-index fields such as ITU or thermal excess;
- physiological threshold isolines;
- literature-derived environmental envelopes;
- observed data layers;
- temporal trajectories;
- accumulated thermal-load classes;
- operational cooling-management overlays.

The main prototype is:

```bash
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

It generates:

```text
bovine_bioclimatic_final_azevedo.png
```

This example combines a psychrometric base chart, an ITU field, critical ITU
isolines, Azevedo et al. (2005) T x RH experimental envelopes, and a sample
trajectory classified by accumulated thermal load.

The concept is documented in:

```text
docs/BOVINE_BIOCLIMATIC_CHART.md
```

---

## Operational overlays

Operational overlays turn the chart into a decision-support diagram. They map a
thermal state into actions such as monitoring, ventilation, ventilation plus
sprinkling/aspersion, maximum cooling, and emergency response.

A minimal operational overlay can use the built-in dairy cooling profile:

```yaml
operational_overlays:
  - load_class: A2
    trend: steady
    alpha: 0.18
    zorder: 0.55
    show_boundaries: true
```

The built-in profile is named:

```text
dairy_cooling_default
```

A trajectory example with accumulated-load classes and operational overlay can
be rendered with:

```bash
psychchart examples/thermal_trajectory_classified.yaml
```

The operational overlay system is documented in:

```text
docs/OPERATIONAL_OVERLAYS.md
```

---

## YAML configuration overview

A complete configuration may define:

- chart domain and rendering parameters
- psychrometric isolines (RH, wet-bulb, enthalpy, etc.)
- thermal index fields and isolines
- index-derived zones
- literature or management zones
- reference points
- data layers
- temporal paths
- operational overlays

### Chart section

```yaml
chart:
  t_min: 0
  t_max: 50
  pressure: 101325
  output: chart.png
  dpi: 150
```

---

### Isolines

```yaml
isolines:
  relative_humidity:
    values: [30, 50, 70, 90]

  wet_bulb:
    values: [10, 20, 30]
```

Supported isoline types include:

- `relative_humidity`
- `wet_bulb`
- `enthalpy`
- `specific_volume`
- `moisture_quantity`

---

### Index fields and isolines

psychChart supports visualization of thermal indexes such as ITU, HLI, and TE
as fields or isolines over the psychrometric domain.

```yaml
indexes:
  - index: ITU
    label: Temperature-Humidity Index
    levels: [60, 72, 76, 77, 79, 84, 89, 98]
    cmap: Spectral_r
    render:
      field:
        alpha: 0.42
        colorbar: true

  - index: ITU
    render:
      isolines:
        levels: [72, 76, 77, 79, 84, 89]
        color: black
        linewidth: 1.0
        label: true
```

---

### Zones and literature envelopes

```yaml
zones:
  - name: Summer afternoon
    t_range: [21, 34]
    rh_range: [33, 100]
    follow_rh: true
    edgecolor: "#C0392B"
    facecolor: none
    linewidth: 2.5
    show_label: true
    label: "Summer\nafternoon"
    label_t: 30
    label_rh: 47
```

Zones may:

- follow real RH curves (`follow_rh: true`)
- represent experimental envelopes
- represent comfort or stress regions
- overlap for comparative analysis
- carry labels directly inside the chart

---

### Data layers

Data layers are the canonical way to overlay observations, trajectories, density
fields, classified points, annotations, and scalar fields.

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
        color: "#2a9d8f"

      - type: classified_points
        value_col: CTA
        profile: CTA

      - type: annotate
        every: 1
        template: "{time:.1f}h"
        time_field: hour
        value_field: CTA
```

---

## Python API

psychChart can be used programmatically:

```python
from psychchart import load_chart_config, PsychChart

data = load_chart_config("examples/bovine_bioclimatic_final_azevedo.yaml")
chart = PsychChart(**data)
ax = chart.draw()
```

The `draw()` method returns a Matplotlib `Axes` object, allowing further
customization or export.

---

## Command-line interface (CLI)

The package provides a thin CLI wrapper:

```bash
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

The CLI:

1. loads the YAML configuration;
2. normalizes inputs such as RH;
3. validates all configuration sections;
4. renders the psychrometric chart;
5. saves the output file declared in `chart.output`.

---

## Project structure

```text
psychchart/
├── docs/
│   ├── BOVINE_BIOCLIMATIC_CHART.md
│   ├── OPERATIONAL_OVERLAYS.md
│   ├── VERSIONING.md
│   ├── VALIDATION.md
│   └── METHODS_TEXT.md
│
├── examples/
│   ├── bovine_bioclimatic_final_azevedo.yaml
│   ├── thermal_trajectory_classified.yaml
│   └── data/
│
├── src/psychchart/
│   ├── config/
│   ├── data/
│   ├── indexes/
│   ├── operations/
│   ├── plot/
│   ├── psychrometrics.py
│   ├── loader.py
│   └── cli.py
│
├── tests/
├── CHANGELOG.md
├── LICENSE
└── README.md
```

The project is organized around a strict separation of concerns:

- **psychrometrics**: physical and thermodynamic formulations
- **indexes**: thermal and bioclimatic index computation
- **operations**: explicit management-decision policies
- **config / loader**: declarative configuration and normalization
- **data**: runtime data-layer processing
- **plot**: visualization and rendering only
- **CLI**: thin execution layer

This design ensures scientific transparency, reproducibility, and long-term
maintainability.

---

## Reproducibility and versioning

psychChart follows **Semantic Versioning (SemVer)**:

- **MAJOR**: breaking API or scientific changes
- **MINOR**: new features, backward compatible
- **PATCH**: bug fixes

The versioning policy is documented in [`docs/VERSIONING.md`](docs/VERSIONING.md).

All changes are tracked in `CHANGELOG.md`.

YAML-based configuration ensures:

- transparent assumptions
- exact reproducibility of figures
- suitability for scientific publications and supplements

---

## Typical applications

- Human thermal comfort (Givoni-style charts)
- Bovine heat-stress and cooling-management analysis
- Dairy compost-barn bioclimatic visualization
- Teaching psychrometrics and bioclimatology
- Comparative climate analysis
- Exploratory research and visualization

---

## License

This project is licensed under the **LGPL-3.0**.

---

## Citation (suggested)

If you use *psychChart* in academic work, please cite it as:

> *psychChart*: A YAML-driven psychrometric and bioclimatic chart generator for reproducible thermal comfort and animal heat-stress analysis.
