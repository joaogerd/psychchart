<p align="center">
  <img src="docs/assets/logo.png" alt="psychChart logo" width="480">
</p>

<p align="center">
    A Python package for generating psychrometric charts using a declarative, YAML-driven configuration.
</p>

---

## Quick usage

### CLI

```bash
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

### Streamlit app

```bash
pip install -e .[app]
psychchart-app
```

### API (production mode)

```bash
pip install -e .[api]
uvicorn psychchart.api.fastapi_app:app --reload
```

---

## Architecture

psychChart is structured as a modular system:

```text
CORE (physics + rendering)
    ↑
SERVICES (application layer)
    ↑
INTERFACES:
  - CLI
  - Streamlit
  - FastAPI
```

This allows:

- reproducible scientific workflows
- interactive exploration
- integration with modern frontends (React/Vite)
- batch processing pipelines

---

## Index field labels

Continuous index fields can display their semantic class labels directly inside the psychrometric diagram. The index semantics remain defined at the index level through `levels`, `colors`, and `labels`; the nested `render.field.labels` option only controls whether those labels are drawn inside the field.

```yaml
indexes:
  - index: ITU
    label: "Temperature-Humidity Index (ITU)"
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert", "Stress"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: true
        label_fontsize: 22
        label_color: "#222222"
        label_alpha: 0.85
        label_fontweight: bold
        label_rotation: -15
```

Manual positions may be declared either in chart coordinates (`t`/`w`) or in the more intuitive dry-bulb temperature and relative humidity form (`t`/`rh`). Relative humidity accepts both fractions and percentages.

```yaml
render:
  field:
    labels: true
    label_positions:
      - label: "Comfort"
        t: 18
        rh: 60
      - label: "Alert"
        t: 26
        rh: 0.70
      - label: "Stress"
        t: 34
        w: 0.020
```

A complete example is available at:

```bash
psychchart examples/itu_field_labels.yaml
```

---

## API usage

### Render chart (JSON)

```http
POST /render
```

Response:

```json
{
  "format": "png",
  "media_type": "image/png",
  "data_base64": "..."
}
```

### Render chart (file)

```http
POST /render/file
```

Returns binary image.

---

## Python usage

```python
from psychchart import load_chart_config, PsychChart

cfg = load_chart_config("chart.yaml")
chart = PsychChart(**cfg)
chart.draw()
```

---

## Documentation

- docs/api_usage.md
- docs/BOVINE_BIOCLIMATIC_CHART.md
- docs/OPERATIONAL_OVERLAYS.md

---

## License

LGPL-3.0
