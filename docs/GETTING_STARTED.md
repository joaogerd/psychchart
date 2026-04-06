# Getting Started with psychchart

This guide walks you through **creating your first psychrometric chart** using `psychchart`, step by step. No deep Python knowledge required.

---

## 1. Installation

```bash
pip install psychchart
```

Or, from source:

```bash
git clone https://github.com/joaogerd/psychchart.git
cd psychchart
pip install -e .
```

---

## 2. Your First Chart (Minimal Example)

The fastest way to get a chart is using the **minimal YAML configuration**.

### File: `examples/minimal.yaml`

```yaml
chart:
  t_min: 0
  t_max: 40
  pressure: 101325
  output: psychchart_minimal.png
  dpi: 150

isos:
  - name: relative_humidity
    values: [0.3, 0.5, 0.7]

points:
  - label: Sample point
    t: 30
    rh: 0.6
```

### Run from the command line

```bash
psychchart examples/minimal.yaml
```

If everything works, you should see:

```text
[OK] Chart successfully saved to 'psychchart_minimal.png'
```
### Result

![Minimal psychrometric chart](images/minimal.png)

This example is ideal for:

* checking installation
* understanding the coordinate system
* using psychchart as a base layer for further analysis

This already gives you:

* a full psychrometric chart
* saturation curve
* relative humidity isolines
* one reference point

---

## 3. Full ITU Example (Index Field + Isolines)

Now let’s generate a **scientific-style chart** using a bioclimatic index.

### File: `examples/itu_full.yaml`

This example demonstrates:

* ITU background field (heatmap)
* ITU isolines
* comfort zones
* reference points

Run it the same way:

```bash
psychchart examples/itu_full.yaml
```

You will obtain a chart with:

* continuous ITU field (colored background)
* ITU stress thresholds
* physical psychrometric isolines

---

## 4. Understanding the Structure

At a high level, `psychchart` works like this:

```text
YAML file
   ↓
load_chart_config()
   ↓
PsychChart(**data)
   ↓
chart.draw()
   ↓
PNG / PDF figure
```

You do **not** need to interact with Matplotlib directly.

---

## 5. When to Use Python Instead of YAML

Use **YAML** when:

* you want reproducible figures
* you are sharing configs with others
* you want CLI usage

Use **Python** when:

* loading observational datasets
* generating paths or density fields
* embedding charts in notebooks or scripts

Example (Python):

```python
from psychchart import load_chart_config, PsychChart

data = load_chart_config("examples/minimal.yaml")
chart = PsychChart(**data)
chart.draw()
```

---

## 6. What’s Next?

* ✔ You can already generate publication-quality charts
* ✔ Index fields and zones are fully supported

Next steps you may want:

* loading time-series observations (paths)
* density / frequency maps
* custom index definitions

See the documentation files in `docs/` for deeper explanations.

---

Happy charting 🚀

