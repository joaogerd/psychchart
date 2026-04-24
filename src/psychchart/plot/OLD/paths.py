from matplotlib.collections import LineCollection
import numpy as np

from psychchart.psychrometrics import Psychrometrics
from psychchart.layers import ZORDER


def draw_paths(ax, chart):
    """
    Draw psychrometric paths (trajectories) on the chart.

    This function renders all paths defined in ``chart.paths``.
    A path represents an ordered trajectory in psychrometric
    space (T–RH), optionally enriched with an index value
    used for color encoding.

    Two rendering modes are supported automatically:

    1. Plain path (no index values)
       - Rendered as a simple Matplotlib line
       - Suitable for trajectories, cycles, and process outlines

    2. Indexed / colored path
       - Rendered using ``LineCollection``
       - Each segment is colored according to an index value
       - Suitable for visualizing thermal stress evolution,
         comfort transitions, or process intensity

    Responsibilities
    ----------------
    - Convert (T, RH) to (T, W) using psychrometric relations
    - Build line segments preserving path ordering
    - Apply visual style defined in :class:`PathConfig`
    - Respect global z-order semantics

    Non-responsibilities
    --------------------
    - Index computation (already done upstream)
    - Colorbar creation
    - Path validation (lengths, NaNs, bounds)
    - Legend management for indexed paths

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes where the paths will be drawn.
    chart : PsychChart
        Chart instance containing:
        - configuration (pressure),
        - a list of ``PathConfig`` objects in ``chart.paths``.

    Notes
    -----
    - Relative humidity is converted internally to humidity ratio
      using :meth:`Psychrometrics.humidity_ratio`.
    - Indexed paths use ``LineCollection`` because standard ``plot``
      does not support per-segment coloring.
    - Z-order is fixed to ``ZORDER["points"]`` to ensure paths appear
      above zones and isolines but below annotations if any.

    Design considerations
    ---------------------
    - This function intentionally performs no branching on index type;
      the presence of ``path.values`` fully determines rendering mode.
    - All paths are drawn in data coordinates (T–W).
    - Color scaling (vmin/vmax) is delegated to ``PathConfig``.

    Examples
    --------
    Draw a simple trajectory:

    >>> path = obs.to_path(label="Daily cycle")
    >>> chart.paths = [path]
    >>> chart.draw()

    Draw an indexed trajectory colored by ITU:

    >>> path = obs.to_indexed_path(
    ...     ITU,
    ...     label="ITU evolution",
    ...     cmap="inferno",
    ...     linewidth=2.0,
    ... )
    >>> chart.paths = [path]
    >>> chart.draw()
    """

    # ------------------------------------------------------------------
    # Loop over all declared paths
    # ------------------------------------------------------------------
    for path in chart.paths:

        # --------------------------------------------------------------
        # Convert T–RH to T–W (psychrometric space)
        # --------------------------------------------------------------
        T = np.asarray(path.T, dtype=float)

        W = Psychrometrics.humidity_ratio(
            T,
            path.RH,
            chart.cfg.pressure
        )

        # --------------------------------------------------------------
        # Case 1: Plain path (no index values)
        # --------------------------------------------------------------
        if path.values is None:
            ax.plot(
                T,
                W,
                lw=path.linewidth,
                linestyle=path.linestyle,
                alpha=path.alpha,
                zorder=ZORDER["points"],
                label=path.label,
            )
            continue

        # --------------------------------------------------------------
        # Case 2: Indexed / colored path
        # --------------------------------------------------------------
        # Build line segments: [(T0,W0)-(T1,W1), (T1,W1)-(T2,W2), ...]
        points = np.column_stack([T, W]).reshape(-1, 1, 2)
        segments = np.concatenate(
            [points[:-1], points[1:]],
            axis=1
        )

        # Create a LineCollection for per-segment coloring
        lc = LineCollection(
            segments,
            cmap=path.cmap,
            linewidth=path.linewidth,
            alpha=path.alpha,
        )

        # Associate scalar values with segments
        # (one value per segment → len(values) - 1)
        lc.set_array(np.asarray(path.values[:-1], dtype=float))

        # Optional explicit color limits
        if hasattr(path, "vmin") or hasattr(path, "vmax"):
            lc.set_clim(
                getattr(path, "vmin", None),
                getattr(path, "vmax", None),
            )

        # Add collection to axes
        ax.add_collection(lc)

