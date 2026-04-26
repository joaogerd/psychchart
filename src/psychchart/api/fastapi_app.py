"""Minimal FastAPI interface for psychChart.

This module exposes a thin HTTP layer around the reusable application services
so that the psychChart engine can be consumed by modern front-ends (React/Vite,
Dash alternatives, etc.) without duplicating logic.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from psychchart.app.services import render_figure_from_yaml, figure_to_bytes, close_figure


class RenderRequest(BaseModel):
    yaml: str
    format: str = "png"


app = FastAPI(title="psychChart API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/render")
def render_chart(req: RenderRequest):
    try:
        fig = render_figure_from_yaml(req.yaml)
        data = figure_to_bytes(fig, req.format)
        close_figure(fig)
        return {
            "format": req.format,
            "bytes": data.hex(),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
