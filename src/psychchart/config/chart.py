"""
Chart-level configuration models for psychchart.

This module defines the typed configuration models responsible for the global
chart settings used by the ``psychchart`` package.

It stores the high-level plotting parameters that describe the psychrometric
chart domain and export behavior, including axis limits, pressure, labels,
figure size, output metadata, and optional reference-grid settings. These
models provide the validated chart contract consumed by the runtime plotting
layer.

The main goal of this module is to keep chart-wide settings declarative,
strongly typed, and clearly separated from plotting implementation.

Notes
-----
This module belongs to the configuration layer.

It is responsible for:
- validating chart-wide plotting parameters
- storing figure and axis metadata
- defining the chart domain and export settings
- organizing optional grid-related configuration

It is not responsible for:
- plotting execution
- psychrometric coordinate computation
- index evaluation
- observational rendering

See Also
--------
app
    Root configuration model that owns the chart section.
base
    Shared strict configuration base model.
isolines
    Isoline-family configuration models used alongside chart settings.
indexes
    Configuration models for computed psychrometric and thermal indexes.

Examples
--------
Create a minimal chart configuration:

>>> cfg = ChartConfig(
...     t_min=0.0,
...     t_max=50.0,
...     pressure=101325.0,
...     xlabel="Dry-bulb temperature (°C)",
...     ylabel="Humidity ratio (kg/kg)",
...     output="chart.png",
...     dpi=150,
... )
>>> cfg.t_min
0.0
>>> cfg.figsize
(16.0, 8.0)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from pydantic import Field

from .base import StrictModel
from .legend import LegendConfig


class ChartConfig(StrictModel):
    """
    Global chart configuration model.

    This model defines the high-level settings used to construct and export a
    psychrometric chart. It contains geometric limits, output metadata, axis
    labels, figure sizing parameters, and optional configuration sections for
    the custom temperature-humidity-ratio reference grid.

    The model is intentionally declarative: it stores validated configuration
    values, but it does not perform plotting by itself.

    Parameters
    ----------
    t_min : float
        Minimum dry-bulb temperature shown on the x-axis.

        This value defines the left boundary of the psychrometric chart domain.
    t_max : float
        Maximum dry-bulb temperature shown on the x-axis.

        This value defines the right boundary of the psychrometric chart domain.
    y_min : float or None, optional
        Minimum humidity ratio shown on the y-axis.

        If ``None``, the plotting layer may infer the lower bound from internal
        defaults or from the computed chart domain.
    y_max : float or None, optional
        Maximum humidity ratio shown on the y-axis.

        If ``None``, the plotting layer may infer the upper bound from internal
        defaults or from the computed chart domain.
    pressure : float
        Reference thermodynamic pressure, in pascals.

        This pressure is a key physical parameter because psychrometric
        relationships depend on atmospheric pressure.
    xlabel : str
        Label used for the x-axis.
    ylabel : str
        Label used for the y-axis.
    title : str or None, optional
        Optional title for the figure.

        If omitted, the chart may be rendered without a title.
    output : str
        Output file name or output path used when exporting the chart.
    dpi : int
        Output resolution in dots per inch.

        This controls the raster export resolution and affects output quality
        for saved figures.
    style : str or None, optional
        Optional Matplotlib style name to apply before rendering.
    grid : bool or None, optional
        Whether the default axes grid should be enabled.

        If ``None``, the plotting layer may decide whether to apply a default
        behavior.
    figsize : tuple of float, default=(16.0, 8.0)
        Figure size expressed in inches as ``(width, height)``.
    show_tw_grid : bool, default=True
        Whether the custom temperature versus humidity-ratio reference grid
        should be displayed.
    tw_grid : dict of str to Any, optional
        Behavioral configuration for the custom reference grid.

        This dictionary is intended for non-visual settings such as spacing,
        activation flags, or logical controls used by the renderer.
    tw_grid_style : dict of str to Any, optional
        Visual styling configuration for the custom reference grid.

        This dictionary is intended for style-related attributes such as line
        width, alpha, linestyle, and color.

    Returns
    -------
    ChartConfig
        Validated chart configuration object.

    Raises
    ------
    pydantic.ValidationError
        Raised when field types are invalid or when unexpected fields are
        provided, because this model inherits strict validation behavior from
        ``StrictModel``.

    Notes
    -----
    This model does not compute psychrometric coordinates and does not render
    the chart. It only defines the validated input required by the chart
    construction pipeline.

    The separation between ``tw_grid`` and ``tw_grid_style`` is intentional:

    - ``tw_grid`` stores behavioral or semantic options
    - ``tw_grid_style`` stores visual appearance options

    This separation improves maintainability by avoiding the mixture of logic
    and aesthetics inside a single free-form dictionary.

    See Also
    --------
    StrictModel
        Strict Pydantic base model used across configuration sections.

    Examples
    --------
    Create a minimal valid chart configuration:

    >>> cfg = ChartConfig(
    ...     t_min=0.0,
    ...     t_max=50.0,
    ...     pressure=101325.0,
    ...     xlabel="Dry-bulb temperature (°C)",
    ...     ylabel="Humidity ratio (kg/kg)",
    ...     output="chart.png",
    ...     dpi=150,
    ... )
    >>> cfg.t_min
    0.0
    >>> cfg.figsize
    (16.0, 8.0)

    Configure the custom T × W reference grid explicitly:

    >>> cfg = ChartConfig(
    ...     t_min=10.0,
    ...     t_max=40.0,
    ...     pressure=101325.0,
    ...     xlabel="Temperature",
    ...     ylabel="Humidity ratio",
    ...     output="psychro.png",
    ...     dpi=200,
    ...     show_tw_grid=True,
    ...     tw_grid={"x_step": 2, "y_step": 0.002},
    ...     tw_grid_style={"alpha": 0.3, "linewidth": 0.5},
    ... )
    >>> cfg.show_tw_grid
    True
    >>> cfg.tw_grid["x_step"]
    2
    """

    # -------------------------------------------------------------------------
    # Domain limits
    # -------------------------------------------------------------------------
    # These fields define the visible thermodynamic domain of the chart.
    # The x-axis is dry-bulb temperature, while the y-axis is humidity ratio.
    t_min: float
    t_max: float
    y_min: Optional[float] = None
    y_max: Optional[float] = None

    # -------------------------------------------------------------------------
    # Physical reference state
    # -------------------------------------------------------------------------
    # Pressure is required because psychrometric relationships depend on it.
    # Even if the plotting layer uses helper functions elsewhere, this config
    # object must retain the reference pressure explicitly.
    pressure: float

    # -------------------------------------------------------------------------
    # Labels and figure metadata
    # -------------------------------------------------------------------------
    # These values control human-readable chart annotations and export details.
    xlabel: str
    ylabel: str
    title: Optional[str] = None
    output: str
    dpi: int
    style: Optional[str] = None
    grid: Optional[bool] = None

    # -------------------------------------------------------------------------
    # Figure geometry
    # -------------------------------------------------------------------------
    # A wide default figure size is commonly useful for psychrometric charts
    # because they contain many isolines, labels, and overlays.
    figsize: Tuple[float, float] = (16.0, 8.0)

    # -------------------------------------------------------------------------
    # Custom T × W reference grid
    # -------------------------------------------------------------------------
    # ``show_tw_grid`` enables or disables the custom auxiliary grid.
    # ``tw_grid`` stores behavioral parameters.
    # ``tw_grid_style`` stores visual styling parameters.
    #
    # Using separate dictionaries keeps semantics and styling decoupled, which
    # is particularly helpful in profile-based configuration systems.
    show_tw_grid: bool = True
    tw_grid: Dict[str, Any] = Field(default_factory=dict)
    tw_grid_style: Dict[str, Any] = Field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Declarative legend
    # -------------------------------------------------------------------------
    # The legend is optional so simple charts do not need to define it.
    legend: Optional[LegendConfig] = None
