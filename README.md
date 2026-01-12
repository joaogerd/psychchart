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

The package separates **physics**, **configuration**, and **visualization**,
enabling transparent and reproducible workflows.

---

## Key features

- 📄 **YAML-driven configuration** (no hard-coded plots)
- 🔬 **Scientifically consistent psychrometric formulations**
- 📊 **Matplotlib-based rendering**
- 🧱 Clear separation of concerns:
  - configuration schema
  - psychrometric calculations
  - plotting engine
- 🧪 Automated tests for numerical consistency and plotting stability
- 🧩 Extensible architecture (ITU, HLI, UTCI, custom zones)

---

## Scientific scope and assumptions

All psychrometric formulations assume:

- Dry-bulb temperature in **degrees Celsius (°C)**
- Atmospheric pressure in **Pascals (Pa)**
- Humidity ratio in **kg water vapor / kg dry air**

The implemented equations are consistent with **classical psychrometric theory**
(e.g. ASHRAE Fundamentals) and are intended for:

- psychrometric diagram construction
- comparative and educational analysis
- thermal comfort assessment

They are **not** intended for high-precision HVAC engineering design.

---

## Installation

```bash
pip install psychchart
````

Python ≥ 3.9 is recommended.

---

## Quick start (minimal example)

Create a minimal YAML file:

```yaml
# minimal.yaml
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

* saturation curve (100% RH)
* relative humidity isolines at 40%, 60% and 80%

---

## YAML configuration overview

A complete configuration may define:

* chart domain and rendering parameters
* psychrometric isolines (RH, wet-bulb, enthalpy, etc.)
* thermal comfort zones
* reference points (observations or scenarios)

### Chart section

```yaml
chart:
  t_min: 0
  t_max: 50
  pressure: 101325
  output: chart.png
  dpi: 150
  style: seaborn-v0_8
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

* `relative_humidity`
* `wet_bulb`
* `enthalpy`
* `specific_volume`
* `moisture_quantity`

---

### Index fields (thermal comfort maps)

psychchart supports the visualization of thermal indexes
(e.g. ITU, HLI) as continuous fields over the psychrometric domain.

These fields may be rendered using:
- filled contours (contourf)
- rasterized meshes (pcolormesh)

Index fields are defined declaratively in YAML and share
the same computational grid used for isolines.

---

### Comfort zones (example: animal thermal comfort)

```yaml
zones:
  - name: Taurinos
    t_range: [15, 25]
    rh_range: [0.40, 0.70]
    follow_rh: true
    edgecolor: darkred
```

Zones may:

* follow real RH curves (`follow_rh: true`)
* represent comfort or stress regions
* overlap for comparative analysis

---

### Reference points

```yaml
points:
  - label: Sample A
    t: 32
    rh: 55
```

Points represent:

* experimental observations
* station data
* design or scenario conditions

---

## Python API

psychchart can be used programmatically:

```python
from psychchart import load_chart_config, PsychChart

data = load_chart_config("examples/givoni_basic.yaml")

chart = PsychChart(
    cfg=data["cfg"],
    isolines=data["isolines"],
    zones=data["zones"],
    points=data["points"],
)

chart.draw()

```

The `draw()` method returns a Matplotlib `Axes` object, allowing further
customization or export.

---

## Command-line interface (CLI)

The package provides a thin CLI wrapper:

```bash
psychchart examples/givoni_basic.yaml
```

The CLI:

1. loads the YAML configuration
2. normalizes inputs (e.g. RH in %)
3. renders the psychrometric chart
4. saves the output file

---

## Project structure

```text
psychchart/
├── docs/
│   ├── VERSIONING.md      # Versioning policy (SemVer and release rules)
│   ├── VALIDATION.md      # Scientific validation and assumptions
│   └── METHODS_TEXT.md    # Reusable methods text for papers and reports
│
├── examples/              # User-facing YAML examples and demonstrations
│
├── src/psychchart/        # Core Python package
│   ├── psychrometrics.py  # Scientific psychrometric formulations
│   │                       # (thermodynamics, humidity ratio, enthalpy, etc.)
│   │
│   ├── config.py          # Declarative data models (schema)
│   │                       # Defines charts, isolines, zones, points and indexes
│   │
│   ├── loader.py          # YAML loader and normalization layer
│   │                       # Reads configuration files and converts inputs
│   │                       # to validated, normalized internal objects
│   │
│   ├── plot/              # Rendering engine (modular backend)
│   │   ├── __init__.py    # Public plotting API and backend entry point
│   │   ├── chart.py       # Plot orchestration (figure, axes, layout, z-order)
│   │   ├── zones.py       # Rendering of psychrometric zones (polygons, fills)
│   │   ├── isolines.py    # Rendering of psychrometric isolines (RH, WB, h, v)
│   │   └── indexes.py     # Rendering of thermal index fields (ITU, ITI, HLI)
│   │
│   ├── cli.py             # Command-line interface (psychchart <config.yaml>)
│
├── tests/                 # Automated tests (numerical + plotting smoke tests)
│
├── CHANGELOG.md           # Chronological record of changes
├── LICENSE
└── README.md
```
The project is organized around a strict separation of concerns:

- **psychrometrics**: physical and thermodynamic formulations
- **config / loader**: declarative configuration and normalization
- **plot**: visualization and rendering only
- **CLI**: thin execution layer

This design ensures scientific transparency, reproducibility,
and long-term maintainability.

---

## Reproducibility and versioning

psychchart follows **Semantic Versioning (SemVer)**:

* **MAJOR**: breaking API or scientific changes
* **MINOR**: new features, backward compatible
* **PATCH**: bug fixes

The versioning policy is documented in
[`docs/VERSIONING.md`](docs/VERSIONING.md).

All changes are tracked in `CHANGELOG.md`.

YAML-based configuration ensures:

* transparent assumptions
* exact reproducibility of figures
* suitability for scientific publications and supplements

---

## Typical applications

* Human thermal comfort (Givoni-style charts)
* Animal heat stress analysis (e.g. cattle breeds)
* Teaching psychrometrics and bioclimatology
* Comparative climate analysis
* Exploratory research and visualization

---

## License

This project is licensed under the **LGPL-3.0**.

---

## Citation (suggested)

If you use *psychchart* in academic work, please cite it as:

> *psychchart*: A YAML-driven psychrometric chart generator for reproducible thermal comfort analysis.


