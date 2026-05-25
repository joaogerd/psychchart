from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Tuple, Union

from pydantic import Field

from .base import StrictModel


class ProjectionConfig(StrictModel):
    t_col: str
    rh_col: str
    rh_unit: Literal["fraction", "percent", "auto"] = "auto"


class TemporalConfig(StrictModel):
    time_col: str
    sort: bool = True


class DirectColumnFieldConfig(StrictModel):
    type: Literal["direct_column"] = "direct_column"
    name: str
    col: str


class DataIndexFieldConfig(StrictModel):
    type: Literal["data_index"] = "data_index"
    name: str
    index: str
    source_col: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)


FieldConfig = Annotated[
    Union[DirectColumnFieldConfig, DataIndexFieldConfig],
    Field(discriminator="type"),
]


class PointsRenderConfig(StrictModel):
    type: Literal["points"] = "points"
    color: str = "black"
    size: float = 20.0
    alpha: float = 0.8
    every: int = 1
    zorder: int = 40


class ScatterRenderConfig(StrictModel):
    type: Literal["scatter"] = "scatter"
    value: Optional[str] = None
    order_by: Optional[str] = None
    cmap: Optional[str] = None
    color: Optional[str] = None
    size: float = 20.0
    alpha: float = 0.8
    edgecolor: str = "black"
    edgewidth: float = 0.3
    every: int = 1
    colorbar: bool = False
    colorbar_label: Optional[str] = None
    colorbar_shrink: Optional[float] = None
    colorbar_pad: Optional[float] = None
    colorbar_aspect: Optional[float] = None
    colorbar_ticks: Optional[list[float]] = None
    zorder: int = 45


class DensityRenderConfig(StrictModel):
    type: Literal["density"] = "density"
    bins: Tuple[int, int] = (60, 60)
    cmap: str = "viridis"
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    alpha: float = 0.6
    colorbar: bool = True
    normalize: bool = True
    zorder: int = 20


class ScalarFieldRenderConfig(StrictModel):
    type: Literal["scalar_field"] = "scalar_field"
    value: str
    bins: Tuple[int, int] = (40, 40)
    cmap: str = "viridis"
    alpha: float = 0.6
    colorbar: bool = True
    zorder: int = 25


class PathRenderConfig(StrictModel):
    type: Literal["path"] = "path"
    order_by: Optional[str] = None
    color: str = "blue"
    alpha: float = 0.6
    linewidth: float = 1.2
    linestyle: str = "-"
    label: Optional[str] = None
    color_by: Optional[str] = None
    cmap: str = "viridis"
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    every: int = 1
    zorder: int = 20


class AnnotateRenderConfig(StrictModel):
    type: Literal["annotate"] = "annotate"
    every: int = 3
    template: str = "{time}"
    time_field: Optional[str] = None
    value_field: Optional[str] = None
    time_format: Optional[str] = None
    dx: float = 0.35
    dy: float = 0.0005
    fontsize: float = 8.0
    fontweight: str = "bold"
    color: str = "black"
    zorder: int = 30


class ClassifiedPointsRenderConfig(StrictModel):
    type: Literal["classified_points"] = "classified_points"
    value_col: str
    profile: str
    order_by: Optional[str] = None
    size: float = 52.0
    alpha: float = 1.0
    edgecolor: str = "black"
    edgewidth: float = 0.8
    marker: str = "o"
    zorder: int = 25
    label: Optional[str] = None
    legend_markersize: float = 7.0


RenderConfig = Annotated[
    Union[
        PointsRenderConfig,
        ScatterRenderConfig,
        PathRenderConfig,
        AnnotateRenderConfig,
        DensityRenderConfig,
        ScalarFieldRenderConfig,
        ClassifiedPointsRenderConfig,
    ],
    Field(discriminator="type"),
]


class DataLayerConfig(StrictModel):
    data: str
    format: str = "parquet"
    projection: ProjectionConfig
    temporal: Optional[TemporalConfig] = None
    fields: list[FieldConfig] = Field(default_factory=list)
    render: list[RenderConfig] = Field(default_factory=list)
