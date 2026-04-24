import numpy as np
from matplotlib.axes import Axes

from psychchart.plot.layers import ZORDER


def draw_density_field(ax: Axes, chart) -> None:
    """
    Render psychrometric density fields as background layers.

    This function draws one or more **density fields** representing
    the frequency or probability distribution of observed
    psychrometric states over the chart domain.

    Each density field is rendered as a 2D heatmap in **(T, W) space**
    using ``matplotlib.pcolormesh``.

    Responsibilities
    ----------------
    - Render precomputed density data (no numerical computation)
    - Apply visual configuration (colormap, transparency, limits)
    - Manage colorbar creation when requested
    - Respect the canonical chart layering (z-order)

    Non-responsibilities
    --------------------
    - Computing histograms or densities
    - Converting RH → W
    - Clipping to the saturation curve
    - Managing legends or annotations

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes where the density fields will be drawn.
    chart : PsychChart
        Chart instance holding one or more density fields.
        Each entry in ``chart.density_fields`` is expected to provide:
        - ``data`` : DensityFieldData
        - ``cfg``  : DensityFieldConfig

    Notes
    -----
    - This function assumes that density values are already computed
      in psychrometric coordinates.
    - The orientation of ``data.values`` must be compatible with
      ``pcolormesh`` (i.e., transposed at computation time).
    - Multiple density fields are drawn sequentially in the order
      they appear in ``chart.density_fields``.
    - No automatic clipping to the saturation curve is applied here;
      this must be handled externally if required.

    Design considerations
    ---------------------
    - ``pcolormesh`` is preferred over ``imshow`` because:
        * axes are non-uniform,
        * physical units are preserved,
        * the grid does not need to be regular.
    - The density field is placed at the same layer as index fields
      (``ZORDER["index_field"]``), ensuring it remains behind
      zones, isolines, points, and paths.

    Examples
    --------
    Typical usage inside the chart rendering pipeline:

    >>> fig, ax = plt.subplots()
    >>> draw_density_field(ax, chart)

    Rendering a normalized density map beneath comfort zones:

    >>> chart.density_fields = [density_field]
    >>> chart.zones = comfort_zones
    >>> chart.draw()

    Overlaying density with indexed paths:

    >>> chart.density_fields = [density_field]
    >>> chart.paths = [obs.to_indexed_path(ITU)]
    >>> chart.draw()
    """

    # --------------------------------------------------------------
    # Iterate over all registered density fields
    # --------------------------------------------------------------
    for field in chart.density_fields:
        data = field.data
        cfg = field.cfg

        # ----------------------------------------------------------
        # Render density field using pcolormesh
        # ----------------------------------------------------------
        # data.T_edges : temperature bin edges (°C)
        # data.W_edges : humidity ratio bin edges (kg/kg)
        # data.values  : density or frequency values
        mesh = ax.pcolormesh(
            data.T_edges,
            data.W_edges,
            data.values,
            cmap=cfg.cmap,
            vmin=cfg.vmin,
            vmax=cfg.vmax,
            alpha=cfg.alpha,
            shading="auto",
            zorder=ZORDER["index_field"],
        )

        # ----------------------------------------------------------
        # Optional colorbar
        # ----------------------------------------------------------
        if cfg.colorbar:
            cbar = ax.figure.colorbar(mesh, ax=ax)
            cbar.set_label(
                "Probability density" if cfg.normalize else "Frequency"
            )

