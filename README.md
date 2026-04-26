# psychchart

**psychchart** is a Python package for generating **psychrometric charts** using a
**declarative, YAML-driven configuration**.

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
