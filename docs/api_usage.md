# psychChart API Usage

## Run locally

```bash
pip install -e .[api]
uvicorn psychchart.api.fastapi_app:app --reload
```

## Endpoints

### Health

```
GET /health
```

### Render (base64)

```
POST /render
```

Body:

```json
{
  "yaml": "...",
  "format": "png"
}
```

### Render (file)

```
POST /render/file
```

Returns binary image.

## Example (Python)

```python
import requests

resp = requests.post(
    "http://localhost:8000/render",
    json={"yaml": open("chart.yaml").read()}
)
```

## Example (Frontend)

```javascript
const res = await fetch('/render', {
  method: 'POST',
  body: JSON.stringify({ yaml }),
  headers: { 'Content-Type': 'application/json' }
});

const data = await res.json();
img.src = `data:${data.media_type};base64,${data.data_base64}`;
```
