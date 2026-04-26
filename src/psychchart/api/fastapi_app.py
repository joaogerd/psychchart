"""FastAPI interface for psychChart.

The API is intentionally thin: it exposes HTTP endpoints around the reusable
application services while keeping all scientific behavior inside the core
``psychchart`` package.  This makes it suitable for React/Vite front-ends,
institutional demos, local services and automated workflows.
"""

from __future__ import annotations

import base64
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from psychchart.app.services import close_figure, figure_to_bytes, render_figure_from_yaml

ImageFormat = Literal["png", "svg", "pdf"]

MEDIA_TYPES: dict[str, str] = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
}

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


class RenderRequest(BaseModel):
    """Request body for chart rendering endpoints."""

    yaml: str = Field(..., min_length=1, description="Full psychChart YAML configuration.")
    format: ImageFormat = Field(default="png", description="Output format.")
    dpi: int = Field(default=180, ge=72, le=600, description="Export resolution for raster output.")


class RenderBase64Response(BaseModel):
    """Base64-encoded render response for browser/front-end clients."""

    format: ImageFormat
    media_type: str
    data_base64: str


app = FastAPI(
    title="psychChart API",
    version="0.2.0",
    description="HTTP API for rendering YAML-driven psychrometric charts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight health-check payload."""
    return {"status": "ok"}


@app.post("/render", response_model=RenderBase64Response)
def render_chart(req: RenderRequest) -> RenderBase64Response:
    """Render a chart and return base64-encoded image data.

    This endpoint is convenient for JavaScript clients because the response is
    JSON and can be directly converted to a browser data URL.
    """
    try:
        fig = render_figure_from_yaml(req.yaml)
        payload = figure_to_bytes(fig, req.format, dpi=req.dpi)
        close_figure(fig)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RenderBase64Response(
        format=req.format,
        media_type=MEDIA_TYPES[req.format],
        data_base64=base64.b64encode(payload).decode("ascii"),
    )


@app.post("/render/file")
def render_chart_file(req: RenderRequest) -> Response:
    """Render a chart and return a binary file response."""
    try:
        fig = render_figure_from_yaml(req.yaml)
        payload = figure_to_bytes(fig, req.format, dpi=req.dpi)
        close_figure(fig)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=payload,
        media_type=MEDIA_TYPES[req.format],
        headers={"Content-Disposition": f'inline; filename="psychchart.{req.format}"'},
    )
