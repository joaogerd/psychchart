# psychChart frontend

This directory contains the Vite/React frontend used by the interactive psychChart workspace.

## Development mode

Run the FastAPI backend from the repository root:

```bash
uvicorn psychchart.api.fastapi_app:app --reload
```

Then run the frontend from this directory:

```bash
cd frontend
npm install
VITE_PSYCHCHART_API_URL=http://127.0.0.1:8000 npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173/
```

The backend API will normally be available at:

```text
http://127.0.0.1:8000
```

## Why the API URL is required

The frontend defaults to `/api` when no API URL is configured. That works only when a proxy or container setup forwards `/api` to the FastAPI backend.

When running Vite and FastAPI manually in two terminals, set `VITE_PSYCHCHART_API_URL` so frontend requests go directly to the backend.

## Basic checks

Backend health check:

```bash
curl http://127.0.0.1:8000/health
```

Readout endpoint check:

```bash
curl -X POST http://127.0.0.1:8000/readout \
  -H 'Content-Type: application/json' \
  -d '{"T": 31.0, "RH_pct": 65.0, "pressure": 101325.0}'
```

## Lockfile

If `package-lock.json` is generated locally with `npm install`, keep it under version control in a dedicated frontend dependency PR. This makes frontend builds reproducible.
