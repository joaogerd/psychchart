"""
Unified data-layer configuration models for psychchart.

This module defines the strongly typed configuration models used to describe
dataset-driven layers in the ``psychchart`` package.

A data layer is the canonical declarative representation for any chart element
that originates from an external tabular dataset and is projected into the
psychrometric domain. This includes, in a single unified structure:

- plain observed points,
- scatter plots colored by scalar variables,
- density fields,
- scalar fields aggregated from observations,
- time-ordered trajectories,
- textual annotations derived from dataset columns.

The main goal of this module is to provide a single, extensible, and stable
configuration contract capable of replacing the older split between:

- observational datasets, and
- temporal overlays.

Notes
-----
This module belongs to the configuration layer.

It is responsible for:
- validating dataset-oriented layer definitions
- validating thermodynamic projection settings
- validating optional temporal ordering metadata
- validating declarative derived fields
- validating rendering specifications for data-driven layers

It is not responsible for:
- loading datasets from disk
- computing psychrometric coordinates
- evaluating scalar fields
- binning or interpolation
- rendering Matplotlib artists

Design Principles
-----------------
The data-layer contract is intentionally structured in five conceptual blocks:

1. dataset identity
2. thermodynamic projection
3. optional temporal ordering
4. optional derived fields
5. one or more render specifications

This separation keeps the configuration clear, composable, and maintainable.

See Also
--------
base
    Shared strict configuration base model.
app
    Root validated configuration model that aggregates data layers.
observations
    Legacy observational configuration kept only for backward compatibility.
overlays
    Legacy temporal overlay configuration kept only for backward compatibility.

Examples
--------
Define a simple scatter layer:

>>> cfg = DataLayerConfig(
...     data="observations.csv",
...     format="csv",
...     projection={"t_col": "T", "rh_col": "RH"},
...     render=[{"type": "points"}],
... )
>>> cfg.data
'observations.csv'
>>> cfg.projection.t_col
'T'

Define a time-ordered layer with a derived field and multiple renderers:

>>> cfg = DataLayerConfig(
...     data="animal_day.csv",
...     format="csv",
...     projection={"t_col": "temp", "rh_col": "rh"},
...     temporal={"time_col": "hour", "sort": True},
...     fields=[
...         {"type": "direct_column", "name": "CTA", "col": "cta_acumulada"}
...     ],
...     render=[
...         {"type": "path", "order_by": "hour"},
...         {"type": "scatter", "value": "CTA", "cmap": "viridis"},
...     ],
... )
>>> cfg.temporal.time_col
'hour'
>>> cfg.render[0].type
'path'
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Tuple, Union

from pydantic import Field

from .base import StrictModel


# =============================================================================
# Projection and ordering
# =============================================================================
class ProjectionConfig(StrictModel):
    """
    Thermodynamic projection settings for a dataset-driven layer.

    This model defines how a tabular dataset should be interpreted as
    psychrometric states prior to any rendering or derived-field computation.

    Parameters
    ----------
    t_col : str
        Name of the dry-bulb temperature column.
    rh_col : str
        Name of the relative humidity column.
    rh_unit : {"fraction", "percent", "auto"}, default="auto"
        Convention used by the relative humidity column.

        - ``"fraction"`` expects values in ``[0, 1]``
        - ``"percent"`` expects values in ``[0, 100]``
        - ``"auto"`` accepts both conventions and normalizes at runtime

    Returns
    -------
    ProjectionConfig
        Validated projection configuration.

    Notes
    -----
    This class is declarative only. It does not normalize values or compute
    humidity ratio directly.
    """

    t_col: str
    rh_col: str
    rh_unit: Literal["fraction", "percent", "auto"] = "auto"


class TemporalConfig(StrictModel):
    """
    Optional temporal ordering metadata for a data layer.

    This model stores the information required to interpret a dataset as an
    ordered sequence, typically for trajectory/path rendering or periodic
    annotation.

    Parameters
    ----------
    time_col : str
        Column used as the temporal coordinate.
    sort : bool, default=True
        Whether the runtime should sort the dataset by ``time_col`` before
        rendering temporal representations.

    Returns
    -------
    TemporalConfig
        Validated temporal configuration.
    """

    time_col: str
    sort: bool = True


# =============================================================================
# Derived field configuration
# =============================================================================
class DirectColumnFieldConfig(StrictModel):
    """
    Declarative mapping of an existing dataset column into a named field.

    Parameters
    ----------
    type : {"direct_column"}, fixed
        Discriminator used by the union parser.
    name : str
        Public field name exposed to renderers.
    col : str
        Name of the source dataset column.

    Returns
    -------
    DirectColumnFieldConfig
        Validated direct-column field definition.
    """

    type: Literal["direct_column"] = "direct_column"
    name: str
    col: str


class DataIndexFieldConfig(StrictModel):
    """
    Declarative definition of a field computed from a registered data index.

    Parameters
    ----------
    type : {"data_index"}, fixed
        Discriminator used by the union parser.
    name : str
        Public field name exposed to renderers.
    index : str
        Registered data-index identifier used by the runtime field registry.
    source_col : str or None, optional
        Optional source column used by the data-index backend.

        This is commonly used when the backend consumes a structured payload
        such as a behavior dictionary stored in a single dataset column.
    parameters : dict of str to Any, optional
        Optional parameters forwarded to the data-index backend.

    Returns
    -------
    DataIndexFieldConfig
        Validated data-index field definition.

    Notes
    -----
    This class is configuration only. It does not compute the field itself.
    """

    type: Literal["data_index"] = "data_index"
    name: str
    index: str
    source_col: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)


FieldConfig = Annotated[
    Union[
        DirectColumnFieldConfig,
        DataIndexFieldConfig,
    ],
    Field(discriminator="type"),
]


# =============================================================================
# Render configuration
# =============================================================================
class PointsRenderConfig(StrictModel):
    """
    Render specification for plain dataset points.

    Parameters
    ----------
    type : {"points"}, fixed
        Discriminator used by the union parser.
    color : str, default="black"
        Marker color.
    size : float, default=20.0
        Marker size.
    alpha : float, default=0.8
        Marker opacity.
    zorder : int, default=40
        Drawing order.
    """

    type: Literal["points"] = "points"
    color: str = "black"
    size: float = 20.0
    alpha: float = 0.8
    zorder: int = 40


class ScatterRenderConfig(StrictModel):
    """
    Render specification for scatter plots.

    Parameters
    ----------
    type : {"scatter"}, fixed
        Discriminator used by the union parser.
    value : str or None, optional
        Field or dataset column used to color the points.

        If ``None``, a fixed-color scatter plot is expected.
    cmap : str or None, optional
        Colormap used when ``value`` is provided.
    color : str or None, optional
        Fixed marker color used when ``value`` is not provided.
    size : float, default=20.0
        Marker size.
    alpha : float, default=0.8
        Marker opacity.
    edgecolor : str, default="black"
        Marker edge color.
    edgewidth : float, default=0.3
        Marker edge width.
    colorbar : bool, default=False
        Whether a colorbar should be displayed.
    zorder : int, default=45
        Drawing order.
    """

    type: Literal["scatter"] = "scatter"
    value: Optional[str] = None
    cmap: Optional[str] = None
    color: Optional[str] = None
    size: float = 20.0
    alpha: float = 0.8
    edgecolor: str = "black"
    edgewidth: float = 0.3
    colorbar: bool = False
    zorder: int = 45


class DensityRenderConfig(StrictModel):
    """
    Render specification for density fields derived from a dataset.

    Parameters
    ----------
    type : {"density"}, fixed
        Discriminator used by the union parser.
    bins : tuple of int, default=(60, 60)
        2D histogram resolution.
    cmap : str, default="viridis"
        Colormap name.
    vmin : float or None, optional
        Lower normalization bound.
    vmax : float or None, optional
        Upper normalization bound.
    alpha : float, default=0.6
        Field opacity.
    colorbar : bool, default=True
        Whether a colorbar should be displayed.
    normalize : bool, default=True
        Whether density values should be normalized before rendering.
    zorder : int, default=20
        Drawing order.
    """

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
    """
    Render specification for scalar fields aggregated from a dataset.

    Parameters
    ----------
    type : {"scalar_field"}, fixed
        Discriminator used by the union parser.
    value : str
        Field or dataset column to aggregate as a scalar field.
    bins : tuple of int, default=(40, 40)
        Aggregation/binning resolution.
    cmap : str, default="viridis"
        Colormap name.
    alpha : float, default=0.6
        Field opacity.
    colorbar : bool, default=True
        Whether a colorbar should be displayed.
    zorder : int, default=25
        Drawing order.
    """

    type: Literal["scalar_field"] = "scalar_field"
    value: str
    bins: Tuple[int, int] = (40, 40)
    cmap: str = "viridis"
    alpha: float = 0.6
    colorbar: bool = True
    zorder: int = 25


class PathRenderConfig(StrictModel):
    """
    Render specification for ordered trajectories.

    This configuration supports two rendering modes:

    1. Plain path
       A standard polyline drawn over the psychrometric chart.

    2. Scalar-colored path
       A segmented line whose colors are driven by one scalar column already
       present in the processed dataframe.

    Parameters
    ----------
    type : {"path"}, fixed
        Discriminator used by the union parser.
    order_by : str or None, optional
        Column used to order the path before rendering.

        When omitted, the runtime may use the layer temporal configuration or
        preserve the dataset order.
    color : str, default="blue"
        Path color used for plain-line rendering.
    alpha : float, default=0.6
        Path opacity.
    linewidth : float, default=1.2
        Path line width.
    linestyle : str, default="-"
        Matplotlib line style used for plain paths and, when supported by the
        backend, for segmented colored paths.
    label : str or None, optional
        Optional legend label.
    color_by : str or None, optional
        Name of the dataframe column used for per-segment coloring.

        When provided, the renderer switches from plain ``ax.plot`` mode to a
        ``LineCollection``-based segmented rendering mode.
    cmap : str, default="viridis"
        Matplotlib colormap used when ``color_by`` is provided.
    vmin : float or None, optional
        Optional lower normalization bound for scalar-colored paths.
    vmax : float or None, optional
        Optional upper normalization bound for scalar-colored paths.
    zorder : int, default=20
        Drawing order.
    """

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
    zorder: int = 20

class AnnotateRenderConfig(StrictModel):
    """
    Render specification for periodic annotations along a data layer.

    Parameters
    ----------
    type : {"annotate"}, fixed
        Discriminator used by the union parser.
    every : int, default=3
        Annotation interval in number of points.
    template : str, default="{time}"
        Annotation text template.

        Runtime formatting typically uses ``time`` and ``value`` placeholders.
    time_field : str or None, optional
        Field or column used as ``time`` in the annotation template.
    value_field : str or None, optional
        Field or column used as ``value`` in the annotation template.
    dx : float, default=0.35
        Horizontal label offset.
    dy : float, default=0.0005
        Vertical label offset.
    fontsize : float, default=8.0
        Annotation font size.
    fontweight : str, default="bold"
        Annotation font weight.
    color : str, default="black"
        Annotation text color.
    zorder : int, default=30
        Drawing order.
    """

    type: Literal["annotate"] = "annotate"
    every: int = 3
    template: str = "{time}"
    time_field: Optional[str] = None
    value_field: Optional[str] = None
    dx: float = 0.35
    dy: float = 0.0005
    fontsize: float = 8.0
    fontweight: str = "bold"
    color: str = "black"
    zorder: int = 30

class ClassifiedPointsRenderConfig(StrictModel):
    """
    Render specification for observation points classified by a semantic profile.

    Parameters
    ----------
    type : {"classified_points"}, fixed
        Discriminator used by the render union.
    value_col : str
        Dataframe column containing the numeric values to classify.
    profile : str
        Semantic profile name used to classify the values.
    order_by : str or None, optional
        Optional column used to order the dataframe before rendering.
    size : float, default=52.0
        Marker size.
    alpha : float, default=1.0
        Marker opacity.
    edgecolor : str, default="black"
        Marker edge color.
    edgewidth : float, default=0.8
        Marker edge width.
    marker : str, default="o"
        Matplotlib marker style.
    zorder : int, default=25
        Drawing order.
    label : str or None, optional
        Optional legend label for the observation points.
    legend_markersize : float, default=7.0
        Marker size used in the legend proxy handle.
    """

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

# =============================================================================
# Root data-layer model
# =============================================================================
class DataLayerConfig(StrictModel):
    """
    Canonical configuration for a dataset-driven layer.

    This model is the stable public contract used to describe any chart layer
    originating from an external dataset. It unifies the older concepts of
    observational datasets and temporal overlays into a single extensible
    structure.

    Parameters
    ----------
    data : str
        Path to the source dataset.
    format : str, default="parquet"
        File format identifier, such as ``"csv"`` or ``"parquet"``.
    projection : ProjectionConfig
        Thermodynamic projection metadata.
    temporal : TemporalConfig or None, optional
        Optional temporal ordering metadata.
    fields : list of FieldConfig, optional
        Optional declarative derived fields exposed to renderers.
    render : list of RenderConfig, optional
        One or more render specifications applied to the dataset.

    Returns
    -------
    DataLayerConfig
        Validated data-layer configuration.

    Notes
    -----
    This class is intentionally declarative and stable. It is the canonical
    configuration shape expected by the next-generation runtime layer.
    """

    data: str
    format: str = "parquet"
    projection: ProjectionConfig
    temporal: Optional[TemporalConfig] = None
    fields: list[FieldConfig] = Field(default_factory=list)
    render: list[RenderConfig] = Field(default_factory=list)
