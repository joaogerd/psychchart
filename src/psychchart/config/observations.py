"""
Observation configuration models for psychchart.

This module defines the typed configuration models used to describe
observational datasets and their visualization settings in the ``psychchart``
package.

It supports dataset-oriented configuration for scatter plots, density fields,
and data-driven scalar variables associated with observations in psychrometric
space. The models in this module allow observational content to be described
declaratively and validated independently from the data-processing and plotting
layers.

The main purpose of this module is to provide a structured and extensible
configuration contract for observation-based chart elements.

Notes
-----
This module is part of the configuration layer.

It is responsible for:
- validating observational dataset settings
- storing density-field configuration
- storing data-driven index visualization options
- organizing dataset-level plotting metadata

It is not responsible for:
- reading datasets from disk
- computing densities
- interpolation or gridding
- rendering points or scalar fields

See Also
--------
app
    Root configuration model that aggregates observation sections.
base
    Shared strict configuration base model.
indexes
    Computed-index configuration models for chart-wide derived quantities.
overlays
    Temporal trajectory configuration related to time-evolving observations.

Examples
--------
Configure a density field for an observational dataset:

>>> density = DensityFieldConfig(bins=(80, 80), cmap="magma", alpha=0.4)
>>> density.bins
(80, 80)

Configure an observational dataset:

>>> cfg = ObservationsConfig(
...     data="observations.csv",
...     t_col="T",
...     rh_col="RH",
... )
>>> cfg.data
'observations.csv'
>>> cfg.t_col
'T'
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import Field

from .base import StrictModel


class DensityFieldConfig(StrictModel):
    """
    Configuration for density field visualization.

    This model defines the rendering parameters used when observational data
    are transformed into a 2D density field over the psychrometric domain.
    Such density maps are useful to visualize the concentration of points,
    reveal preferred environmental regimes, and summarize large observational
    datasets without plotting every individual sample.

    Parameters
    ----------
    bins : tuple of int, default=(60, 60)
        Resolution of the 2D histogram used to compute the density field.

        The tuple is interpreted as ``(n_x_bins, n_y_bins)``. Higher values
        provide finer spatial detail but may also produce noisier fields when
        data are sparse.
    cmap : str, default="viridis"
        Matplotlib colormap name used to render the density field.
    vmin : float or None, optional
        Lower bound of the color normalization.

        If ``None``, the plotting layer may infer the lower limit from the
        computed density values.
    vmax : float or None, optional
        Upper bound of the color normalization.

        If ``None``, the plotting layer may infer the upper limit from the
        computed density values.
    alpha : float, default=0.6
        Opacity of the rendered density field.

        This is especially useful when the density field must coexist with
        isolines, zones, trajectories, or point overlays.
    colorbar : bool, default=True
        Whether a colorbar should be displayed for the density field.
    normalize : bool, default=True
        Whether the density values should be normalized before rendering.

        The exact normalization semantics are handled by the plotting or data
        processing layer, but this flag allows the configuration to express the
        intended behavior declaratively.

    Returns
    -------
    DensityFieldConfig
        Validated density field configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported keys
        are provided.

    Notes
    -----
    This class only describes configuration. It does not compute the histogram,
    normalize densities, or render the final field.

    Choosing ``bins`` is often a trade-off:

    - fewer bins produce smoother, more aggregated density maps
    - more bins preserve local structure but require more observations

    See Also
    --------
    DataIndexConfig
        Configuration for data-driven index visualization associated with an
        observational dataset.
    ObservationsConfig
        Higher-level model that groups density and index visualization options
        for a dataset.

    Examples
    --------
    Create a default density field configuration:

    >>> cfg = DensityFieldConfig()
    >>> cfg.bins
    (60, 60)
    >>> cfg.colorbar
    True

    Create a denser and more transparent field:

    >>> cfg = DensityFieldConfig(
    ...     bins=(80, 80),
    ...     cmap="magma",
    ...     alpha=0.4,
    ...     normalize=False,
    ... )
    >>> cfg.cmap
    'magma'
    >>> cfg.normalize
    False
    """

    # ``bins`` controls the spatial discretization used to summarize point
    # density. A 2D histogram is typically built over the psychrometric plane.
    bins: Tuple[int, int] = (60, 60)

    # Colormap used to convert density magnitudes into visible colors.
    cmap: str = "viridis"

    # Optional lower and upper bounds for color normalization. Leaving them as
    # ``None`` allows the runtime to infer appropriate limits from the data.
    vmin: Optional[float] = None
    vmax: Optional[float] = None

    # Opacity of the density layer. Partial transparency is often desirable so
    # additional chart elements remain readable.
    alpha: float = 0.6

    # Whether the renderer should attach a colorbar for quantitative reading of
    # density magnitude.
    colorbar: bool = True

    # Whether the computed density should be normalized before plotting.
    normalize: bool = True


class DataIndexConfig(StrictModel):
    """
    Configuration of a data-driven index visualization.

    This model defines how a scalar variable associated with an observational
    dataset should be visualized on the chart. Typical examples include
    thermal indices computed for each observation, animal response metrics, or
    any derived quantity that can be mapped onto the psychrometric domain.

    Parameters
    ----------
    index : str
        Name of the data-driven index.

        This identifier is typically used to select the corresponding column
        from the observational dataset.
    scatter : bool, default=True
        Whether individual scatter points should be displayed.
    scalar_field : bool, default=False
        Whether the data-driven index should also be rendered as a scalar
        field.

        This usually implies some gridding, interpolation, or binned
        aggregation step performed by the plotting layer.
    bins : tuple of int, default=(40, 40)
        Resolution of the binning used when ``scalar_field`` is enabled.
    cmap : str, default="viridis"
        Matplotlib colormap name used to render the index values.
    alpha : float, default=0.6
        Opacity of the rendered scatter points or scalar field.
    colorbar : bool, default=True
        Whether a colorbar should be displayed for the index visualization.

    Returns
    -------
    DataIndexConfig
        Validated data-driven index visualization configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported keys
        are provided.

    Notes
    -----
    This model does not compute the index itself. It only describes how an
    already available data variable should be visualized.

    The ``scatter`` and ``scalar_field`` flags are intentionally independent.
    This allows flexible combinations such as:

    - scatter only
    - scalar field only
    - both representations together

    See Also
    --------
    DensityFieldConfig
        Configuration for density visualization of observational datasets.
    ObservationsConfig
        Dataset-level configuration that groups multiple data-driven index
        visualizations.

    Examples
    --------
    Visualize an index as scatter points:

    >>> cfg = DataIndexConfig(index="THI")
    >>> cfg.scatter
    True
    >>> cfg.scalar_field
    False

    Visualize an index as both scatter and scalar field:

    >>> cfg = DataIndexConfig(
    ...     index="CTA",
    ...     scatter=True,
    ...     scalar_field=True,
    ...     bins=(50, 50),
    ...     cmap="plasma",
    ... )
    >>> cfg.scalar_field
    True
    >>> cfg.bins
    (50, 50)
    """

    # Name of the variable or derived index to be visualized from the dataset.
    index: str

    # Whether to plot raw observations as scatter points.
    scatter: bool = True

    # Whether to also summarize or interpolate the variable into a scalar field.
    scalar_field: bool = False

    # Resolution of the binning used for field-based representations.
    bins: Tuple[int, int] = (40, 40)

    # Colormap used to encode index magnitude.
    cmap: str = "viridis"

    # Opacity of the rendered representation.
    alpha: float = 0.6

    # Whether to display a colorbar for the index visualization.
    colorbar: bool = True


class ObservationsConfig(StrictModel):
    """
    Configuration for an observational dataset.

    This model describes one dataset to be loaded and visualized on the
    psychrometric chart. It combines the file-level metadata with optional
    visualization sub-configurations for density fields and data-driven
    indexes.

    Parameters
    ----------
    file : str
        Path to the dataset file.
    format : str, default="parquet"
        File format identifier.

        This field informs the loading layer how the dataset should be read.
        Typical examples may include ``"parquet"``, ``"csv"``, or other
        supported tabular formats.
    data_indexes : list of DataIndexConfig, optional
        Data-driven index visualizations associated with the dataset.

        Each entry describes how one scalar variable or derived observational
        metric should be rendered.
    density : DensityFieldConfig or None, optional
        Optional density field configuration for the dataset.

        When provided, the dataset may also be summarized as a density map over
        the chart domain.

    Returns
    -------
    ObservationsConfig
        Validated observational dataset configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported keys
        are provided.

    Notes
    -----
    This model does not read files or validate whether the referenced dataset
    actually exists on disk. It only stores the validated configuration needed
    by the I/O and plotting layers.

    The class is designed so one observational dataset can support multiple
    complementary visualizations at once, such as:

    - a point cloud
    - one or more data-driven indexes
    - a density field summary

    See Also
    --------
    DataIndexConfig
        Visualization configuration for scalar dataset variables or indices.
    DensityFieldConfig
        Configuration for density field rendering.

    Examples
    --------
    Define a minimal observational dataset:

    >>> cfg = ObservationsConfig(file="data/observations.parquet")
    >>> cfg.format
    'parquet'
    >>> cfg.data_indexes
    []

    Define a dataset with one index and a density field:

    >>> cfg = ObservationsConfig(
    ...     file="data/animals.parquet",
    ...     format="parquet",
    ...     data_indexes=[
    ...         DataIndexConfig(index="CTA", scatter=True, scalar_field=False)
    ...     ],
    ...     density=DensityFieldConfig(bins=(80, 80), alpha=0.5),
    ... )
    >>> cfg.file
    'data/animals.parquet'
    >>> len(cfg.data_indexes)
    1
    >>> cfg.density.alpha
    0.5
    """

    # Path to the observational dataset file. The actual file reading is
    # performed elsewhere; this model only stores the declarative reference.
    file: str

    # File format identifier used by the loading layer to choose the proper
    # reader implementation.
    format: str = "parquet"

    # Optional list of scalar variables or derived metrics to visualize from
    # this dataset.
    data_indexes: List[DataIndexConfig] = Field(default_factory=list)

    # Optional density field summary of the dataset.
    density: Optional[DensityFieldConfig] = None
