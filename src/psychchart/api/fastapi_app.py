"""FastAPI interface for psychChart."""

from __future__ import annotations

import base64
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from psychchart.api.workspace import ProjectRecord, WorkspaceStore
from psychchart.app.services import (
    close_figure,
    compute_point_readout,
    figure_to_bytes,
    render_figure_from_yaml,
)

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

store = WorkspaceStore()


class RenderRequest(BaseModel):
    yaml: str = Field(..., min_length=1, description="Full psychChart YAML configuration.")
    format: ImageFormat = Field(default="png", description="Output format.")
    dpi: int = Field(default=180, ge=72, le=600, description="Export resolution for raster output.")


class RenderBase64Response(BaseModel):
    format: ImageFormat
    media_type: str
    data_base64: str


class ReadoutRequest(BaseModel):
    T: float = Field(..., description="Dry-bulb temperature in Celsius.")
    RH_pct: float = Field(..., ge=0, le=100, description="Relative humidity in percent.")
    pressure: float = Field(default=101325.0, gt=0, description="Air pressure in Pa.")


class ReadoutResponse(BaseModel):
    T: float
    RH_pct: float
    RH: float
    W: float
    h: float
    Tdp: float
    ITU: float


class ProjectCreateRequest(BaseModel):
    name: str = Field(default="Untitled chart")
    yaml: str = Field(..., min_length=1)


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    yaml: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    yaml: str
    created_at: str
    updated_at: str


def _project_response(record: ProjectRecord) -> ProjectResponse:
    return ProjectResponse(**record.__dict__)


app = FastAPI(
    title="psychChart API",
    version="0.3.0",
    description="HTTP API for rendering and managing YAML-driven psychrometric charts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/readout", response_model=ReadoutResponse)
def readout(req: ReadoutRequest) -> ReadoutResponse:
    try:
        result = compute_point_readout(T=req.T, RH_pct=req.RH_pct, pressure=req.pressure)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReadoutResponse(**result.as_dict())


@app.post("/render", response_model=RenderBase64Response)
def render_chart(req: RenderRequest) -> RenderBase64Response:
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


@app.get("/projects", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    return [_project_response(item) for item in store.list_projects()]


@app.post("/projects", response_model=ProjectResponse)
def create_project(req: ProjectCreateRequest) -> ProjectResponse:
    return _project_response(store.create_project(name=req.name, yaml=req.yaml))


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> ProjectResponse:
    try:
        return _project_response(store.get_project(project_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, req: ProjectUpdateRequest) -> ProjectResponse:
    try:
        return _project_response(store.update_project(project_id, name=req.name, yaml=req.yaml))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@app.delete("/projects/{project_id}")
def delete_project(project_id: str) -> dict[str, str]:
    try:
        store.delete_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    return {"status": "deleted"}
