"""
Renderer for density fields derived from processed data layers.

This module provides the runtime renderer responsible for drawing
two-dimensional density fields derived from observational or processed
psychrometric data layers.

The density field is projected onto the psychrometric chart using
``matplotlib.axes.Axes.pcolormesh``, which is appropriate for gridded
cell-based data defined by bin edges in dry-bulb temperature and humidity
ratio space.

A key design decision in this renderer is the masking of empty bins
(i.e., bins with zero density or zero frequency). Without masking,
``pcolormesh`` would render those cells using the minimum value of the
colormap, which can visually suggest the existence of data where there is
none. By masking such cells, the plot preserves transparency in unsupported
regions and communicates observational coverage more honestly.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def draw_density(
    ax: Axes,
    chart: Any,
    layer: ProcessedDataLayer,
    cfg: Any,
) -> None:
    """
    Render a two-dimensional density field from a processed data layer.

    This function converts a processed observational layer into a gridded
    density representation and draws it on the target axes using
    :meth:`matplotlib.axes.Axes.pcolormesh`.

    The density field is expected to be defined over psychrometric coordinates,
    typically:
    - ``T_edges``: dry-bulb temperature bin edges
    - ``W_edges``: humidity ratio bin edges
    - ``values``: cell values representing either raw counts or normalized
      density, depending on the configuration

    Empty cells are masked before plotting so that regions without
    observational support remain transparent instead of being displayed with
    the lowest colormap value.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target Matplotlib axes where the density field will be rendered.
    chart : Any
        Parent chart instance that provides access to the chart configuration
        through ``chart.cfg``. The chart configuration is passed to the layer
        transformation routine so the density field can be built consistently
        with the chart domain and resolution.
    layer : ProcessedDataLayer
        Processed data layer containing the observational representation used
        to generate the density field. The object is expected to expose an
        ``observations`` attribute implementing
        ``to_density_field(cfg, chart.cfg)``.
    cfg : Any
        Density rendering configuration object. It is expected to provide at
        least the following attributes:

        - ``cmap`` : colormap name or Matplotlib colormap
        - ``vmin`` : optional lower value bound
        - ``vmax`` : optional upper value bound
        - ``alpha`` : transparency
        - ``zorder`` : drawing order
        - ``colorbar`` : whether to add a colorbar
        - ``normalize`` : whether the density values are normalized

    Returns
    -------
    None
        This function modifies the provided axes in place and does not return
        a value.

    Raises
    ------
    AttributeError
        If ``layer.observations`` does not provide the required
        ``to_density_field`` method, or if the returned density object does not
        expose the expected attributes.
    ValueError
        If the density field cannot be converted into a valid numeric array.
    TypeError
        If the density values are incompatible with NumPy masked-array
        operations or with Matplotlib ``pcolormesh``.

    Notes
    -----
    The renderer intentionally masks values ``<= 0.0``:

    - ``0.0`` usually means an empty bin when the field represents frequency
      or normalized density.
    - negative values are not physically meaningful for a density field and
      are therefore also excluded from rendering.

    This approach improves interpretability by avoiding misleading color
    patches in regions with no actual data support.

    The colorbar label is selected automatically based on ``cfg.normalize``:

    - ``True``  -> ``"Probability density"``
    - ``False`` -> ``"Frequency"``

    See Also
    --------
    matplotlib.axes.Axes.pcolormesh
        Matplotlib routine used to render cell-based gridded fields.
    numpy.ma.masked_less_equal
        Utility used to mask empty or non-positive cells.
    psychchart.data.layer_runtime.ProcessedDataLayer
        Runtime representation of processed data layers.

    Examples
    --------
    The example below illustrates the typical usage pattern inside a plotting
    pipeline where ``chart``, ``layer`` and ``cfg`` are already available.

    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> # draw_density(ax, chart, layer, cfg)
    >>> # The density field is rendered directly on ``ax``.
    >>> isinstance(ax, Axes)
    True
    """
    # ------------------------------------------------------------------
    # Convert the processed observational layer into a gridded density field.
    #
    # This transformation is delegated to the observation object because it
    # owns the raw/processed data and knows how to bin or project it according
    # to the current chart configuration.
    # ------------------------------------------------------------------
    density_data = layer.observations.to_density_field(cfg, chart.cfg)

    # ------------------------------------------------------------------
    # Convert field values to a floating-point NumPy array.
    #
    # Using float ensures compatibility with masked arrays and with
    # Matplotlib's pcolormesh, especially when the upstream data source
    # may provide integer counts or other numeric dtypes.
    # ------------------------------------------------------------------
    values = np.asarray(density_data.values, dtype=float)

    # ------------------------------------------------------------------
    # Mask empty or invalid bins.
    #
    # Why this matters:
    # pcolormesh will otherwise draw zero-valued cells using the first color
    # of the colormap, which visually implies "very low density" rather than
    # "no data". For observational coverage plots, this distinction is very
    # important.
    # ------------------------------------------------------------------
    masked_values = np.ma.masked_less_equal(values, 0.0)

    # ------------------------------------------------------------------
    # Draw the gridded density field.
    #
    # The edges define the rectangular cells in psychrometric coordinates:
    # - T_edges: x-axis bin boundaries
    # - W_edges: y-axis bin boundaries
    #
    # ``shading="auto"`` lets Matplotlib infer the appropriate cell handling
    # from the shape of the data and edge arrays, which makes the renderer
    # more robust to typical histogram-like outputs.
    # ------------------------------------------------------------------
    mesh = ax.pcolormesh(
        density_data.T_edges,
        density_data.W_edges,
        masked_values,
        cmap=cfg.cmap,
        vmin=cfg.vmin,
        vmax=cfg.vmax,
        shading="auto",
        alpha=cfg.alpha,
        zorder=cfg.zorder,
    )

    # ------------------------------------------------------------------
    # Optionally attach a colorbar.
    #
    # The semantic meaning of the plotted values depends on whether the field
    # was normalized:
    # - normalized field   -> probability density
    # - non-normalized     -> raw frequency / counts
    # ------------------------------------------------------------------
    if cfg.colorbar:
        cbar = ax.figure.colorbar(mesh, ax=ax)
        cbar.set_label("Probability density" if cfg.normalize else "Frequency")
