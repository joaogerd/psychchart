"""
Temporal overlay configuration models for psychchart.

This module defines the typed configuration model used to describe temporal
trajectory overlays in the ``psychchart`` package.

A temporal overlay represents the evolution of a system through time in
psychrometric space, typically using a connected path, point markers, and
optional annotations. These overlays are especially useful for visualizing
time-ordered environmental exposure, chamber experiments, or animal-response
histories.

The main purpose of this module is to keep time-dependent overlay settings
declarative, strongly typed, and clearly separated from evaluation and
rendering logic.

Notes
-----
This module belongs to the configuration layer.

It is responsible for:
- validating temporal overlay settings
- storing dataset column mappings
- storing path, point, and annotation style options
- organizing overlay legend and visibility metadata

It is not responsible for:
- loading tabular data
- sorting timestamps
- computing humidity ratio
- drawing paths, markers, or annotations

See Also
--------
app
    Root configuration model that aggregates temporal overlays.
base
    Shared strict configuration base model.
observations
    Dataset-oriented observation models that may complement overlays.
paths
    Declarative path model for ordered psychrometric trajectories.

Examples
--------
Create a temporal overlay configuration:

>>> cfg = TemporalOverlayConfig(
...     type="CTA",
...     data="trajectory.csv",
...     t_col="temperature",
...     rh_col="relative_humidity",
...     time_col="hour",
...     cta_col="cta",
... )
>>> cfg.type
'CTA'
>>> cfg.show_path
True
"""


from __future__ import annotations

from typing import Optional

from .base import StrictModel


class TemporalOverlayConfig(StrictModel):
    """
    Configuration for a temporal trajectory overlay.

    This model defines the configuration used to render a time-ordered
    trajectory over the psychrometric chart. A temporal overlay typically
    represents the evolution of an observed system through time, such as an
    animal's environmental exposure, a chamber experiment, or a sequence of
    meteorological states.

    The overlay may include:

    - a path connecting time-ordered points
    - markers positioned at each sampled state
    - text annotations at configurable intervals
    - legend metadata for chart interpretation

    Parameters
    ----------
    type : str
        Overlay type identifier.

        This field is used by the runtime registry to resolve the appropriate
        evaluator or rendering logic for the overlay.
    data : str
        Path to the source dataset containing the temporal trajectory.
    t_col : str
        Name of the dry-bulb temperature column in the dataset.
    rh_col : str
        Name of the relative humidity column in the dataset.
    time_col : str
        Name of the time column in the dataset.

        This column is typically used both for sorting the trajectory and for
        generating annotation labels.
    cta_col : str
        Name of the cumulative metric column in the dataset.

        In many use cases this corresponds to an accumulated thermal-load
        quantity, such as CTA, used to color or annotate the trajectory.
    annotate_every : int or None, default=3
        Annotation interval in number of points.

        For example, ``3`` means that every third point may receive an
        annotation. If ``None``, the plotting layer may interpret this as no
        periodic annotation.
    annotation_template : str, default="{time}h\\n(CTA:{cta:.0f})"
        String template used to generate annotation text.

        The template is typically formatted with values extracted from each
        point, such as time and CTA.
    show_path : bool, default=True
        Whether the path line connecting the temporal points should be shown.
    path_color : str, default="blue"
        Color of the path line.
    path_alpha : float, default=0.6
        Opacity of the path line.
    path_linewidth : float, default=1.2
        Width of the path line.
    path_zorder : int, default=20
        Drawing order of the path line.
    point_size : float, default=42.0
        Marker size used for the temporal points.
    point_edgecolor : str, default="black"
        Edge color of the point markers.
    point_edgewidth : float, default=0.8
        Edge width of the point markers.
    point_zorder : int, default=25
        Drawing order of the point markers.
    annotation_dx : float, default=0.35
        Horizontal offset applied to annotations relative to the point
        position.
    annotation_dy : float, default=0.0005
        Vertical offset applied to annotations relative to the point position.
    annotation_fontsize : float, default=8.0
        Font size of annotation text.
    annotation_fontweight : str, default="bold"
        Font weight of annotation text.
    annotation_color : str, default="black"
        Color of annotation text.
    annotation_zorder : int, default=30
        Drawing order of annotation text.
    show_legend : bool, default=True
        Whether the overlay should contribute a legend entry.
    legend_loc : str, default="upper left"
        Legend location used when the overlay requests legend rendering.

    Returns
    -------
    TemporalOverlayConfig
        Validated temporal overlay configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported fields
        are provided, because this model inherits strict validation behavior
        from ``StrictModel``.

    Notes
    -----
    This class only stores declarative configuration. It does not load the
    dataset, sort timestamps, convert relative humidity to humidity ratio, or
    render the overlay by itself.

    The separation between path, points, and annotations is intentional:

    - path settings control the continuous trajectory
    - point settings control discrete observation markers
    - annotation settings control textual time or metric labels

    This makes the overlay configuration easier to extend and reason about in
    profile-based YAML systems.

    See Also
    --------
    StrictModel
        Strict base configuration model used across the package.
    ObservationsConfig
        Dataset-oriented configuration model that may complement overlay
        rendering in chart workflows.

    Examples
    --------
    Create a minimal temporal overlay configuration:

    >>> cfg = TemporalOverlayConfig(
    ...     type="CTA",
    ...     data="data/trajectory.csv",
    ...     t_col="temperature",
    ...     rh_col="relative_humidity",
    ...     time_col="hour",
    ...     cta_col="cta",
    ... )
    >>> cfg.type
    'CTA'
    >>> cfg.show_path
    True

    Configure a denser annotation pattern and custom styling:

    >>> cfg = TemporalOverlayConfig(
    ...     type="CTA",
    ...     data="data/trajectory.csv",
    ...     t_col="T",
    ...     rh_col="RH",
    ...     time_col="time",
    ...     cta_col="CTA",
    ...     annotate_every=1,
    ...     path_color="red",
    ...     point_size=60.0,
    ...     annotation_template="{time} h | CTA={cta:.1f}",
    ... )
    >>> cfg.annotate_every
    1
    >>> cfg.path_color
    'red'
    """

    # -------------------------------------------------------------------------
    # Core dataset identity
    # -------------------------------------------------------------------------
    # ``type`` identifies the semantic overlay/evaluator to use.
    # ``data`` points to the source dataset on disk.
    type: str
    data: str

    # -------------------------------------------------------------------------
    # Required dataset column mapping
    # -------------------------------------------------------------------------
    # These fields tell the runtime how to interpret the input tabular data.
    # The plotting/evaluation layer uses them to extract thermodynamic and
    # temporal variables in a fully declarative way.
    t_col: str
    rh_col: str
    time_col: str
    cta_col: str

    # -------------------------------------------------------------------------
    # Annotation behavior
    # -------------------------------------------------------------------------
    # ``annotate_every`` controls how often labels are drawn along the
    # trajectory. The template is intentionally free-form so users can expose
    # any supported metric in the annotation text.
    annotate_every: Optional[int] = 3
    annotation_template: str = "{time}h\n(CTA:{cta:.0f})"

    # -------------------------------------------------------------------------
    # Path styling
    # -------------------------------------------------------------------------
    # These options define the continuous line connecting the ordered points of
    # the trajectory.
    show_path: bool = True
    path_color: str = "blue"
    path_alpha: float = 0.6
    path_linewidth: float = 1.2
    path_zorder: int = 20

    # -------------------------------------------------------------------------
    # Point styling
    # -------------------------------------------------------------------------
    # These options define the appearance of the discrete sample markers along
    # the path.
    point_size: float = 42.0
    point_edgecolor: str = "black"
    point_edgewidth: float = 0.8
    point_zorder: int = 25

    # -------------------------------------------------------------------------
    # Annotation styling
    # -------------------------------------------------------------------------
    # Annotation offsets are expressed in chart coordinates and are useful to
    # keep labels from overlapping markers.
    annotation_dx: float = 0.35
    annotation_dy: float = 0.0005
    annotation_fontsize: float = 8.0
    annotation_fontweight: str = "bold"
    annotation_color: str = "black"
    annotation_zorder: int = 30

    # -------------------------------------------------------------------------
    # Legend behavior
    # -------------------------------------------------------------------------
    # These settings control whether the overlay contributes to the legend and
    # where that legend should be positioned.
    show_legend: bool = True
    legend_loc: str = "upper left"
