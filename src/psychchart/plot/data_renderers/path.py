"""
Renderer for ordered paths derived from processed data layers.

This module implements dataset-driven psychrometric trajectory rendering.

Supported modes
---------------
1. Plain ordered path
2. Scalar-colored path (per-segment coloring via ``LineCollection``)

The renderer operates strictly on processed runtime layers and never performs
psychrometric conversion or index computation.

Notes
-----
This module assumes that the upstream processing pipeline has already produced
a dataframe containing psychrometric coordinates stored in the canonical
columns:

- ``"_T"`` for dry-bulb temperature
- ``"_W"`` for humidity ratio

If scalar-colored rendering is requested, the scalar field used for coloring
must also already exist in the processed dataframe.

Examples
--------
The public entry point of the module is ``draw_path``:

>>> # Typical usage inside the chart drawing pipeline
>>> # handles = draw_path(ax, processed_layer, render_cfg)
>>> # The returned handles can then be passed to centralized legend assembly.
"""

from __future__ import annotations

import numpy as np
from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

from psychchart.data.layer_runtime import ProcessedDataLayer


def _resolve_order_by(layer: ProcessedDataLayer, cfg) -> str | None:
    """
    Resolve the ordering column used for trajectory rendering.

    The renderer may need to sort the processed dataframe before drawing the
    path. This helper determines which column should be used for that ordering,
    following an explicit precedence rule.

    Priority
    --------
    1. ``cfg.order_by``
    2. ``layer.config.temporal.time_col``
    3. ``None``

    Parameters
    ----------
    layer : ProcessedDataLayer
        Processed runtime layer containing the data and original layer
        configuration.
    cfg : Any
        Path renderer configuration object.

        The object is expected to expose an ``order_by`` attribute. If it does
        not, the function falls back to the temporal configuration stored in
        the processed layer.

    Returns
    -------
    str or None
        Name of the column that should be used for ordering, or ``None`` if no
        ordering column is available.

    Notes
    -----
    The separation of this logic into a helper keeps the precedence rule
    centralized and easy to change without touching the rendering code itself.

    See Also
    --------
    draw_path
        Public renderer entry point that uses this helper before requesting an
        ordered dataframe.

    Examples
    --------
    The precedence rule is:

    - explicit renderer configuration first
    - temporal layer configuration second
    - no ordering as final fallback
    """
    # Renderer-level explicit ordering has the highest priority because it is
    # the most local and intentional configuration source.
    if cfg.order_by is not None:
        return cfg.order_by

    # If the renderer does not specify an ordering column, try the temporal
    # metadata attached to the processed layer configuration.
    temporal = getattr(layer.config, "temporal", None)
    if temporal is not None:
        return getattr(temporal, "time_col", None)

    # No ordering information is available.
    return None


def _extract_plain_arrays(df) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract finite psychrometric coordinate arrays for plain path rendering.

    Parameters
    ----------
    df : pandas.DataFrame
        Processed dataframe expected to contain the canonical coordinate
        columns ``"_T"`` and ``"_W"``.

    Returns
    -------
    tuple of numpy.ndarray
        Two one-dimensional arrays ``(t, w)`` containing only finite values.

    Notes
    -----
    Non-finite values are filtered out before rendering so the plotting layer
    receives clean coordinate arrays and does not create broken or undefined
    segments.

    The returned arrays preserve the original ordering of valid rows.

    See Also
    --------
    _extract_colored_arrays
        Equivalent extractor for scalar-colored path rendering.

    Examples
    --------
    Conceptually, the function transforms a processed dataframe into two clean
    arrays suitable for ``Axes.plot``.
    """
    # Extract canonical temperature and humidity-ratio coordinates from the
    # processed dataframe as floating-point NumPy arrays.
    t = df["_T"].to_numpy(dtype=float)
    w = df["_W"].to_numpy(dtype=float)

    # Keep only rows where both coordinates are finite. This avoids rendering
    # undefined path segments due to NaN or infinite values.
    mask = np.isfinite(t) & np.isfinite(w)
    return t[mask], w[mask]


def _extract_colored_arrays(
    df,
    color_by: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract finite coordinate arrays plus scalar values for colored paths.

    Parameters
    ----------
    df : pandas.DataFrame
        Processed dataframe expected to contain the canonical coordinate
        columns ``"_T"`` and ``"_W"``, plus the scalar column referenced by
        ``color_by``.
    color_by : str
        Name of the scalar column used to color the trajectory segments.

    Returns
    -------
    tuple of numpy.ndarray
        Three one-dimensional arrays ``(t, w, values)`` containing only rows
        where all required fields are finite.

    Raises
    ------
    KeyError
        If the requested ``color_by`` column is not present in the processed
        dataframe.

    Notes
    -----
    This function performs strict validation of scalar availability before
    rendering. That is preferable to silently skipping coloring, because a
    missing scalar field usually indicates a configuration or pipeline error.

    See Also
    --------
    _draw_colored_path
        Consumer of the arrays produced by this helper.

    Examples
    --------
    Conceptually, this function prepares the data required by
    ``LineCollection`` to render a segment-colored psychrometric path.
    """
    # Colored path rendering requires a scalar column already computed and
    # present in the processed dataframe. Fail fast if it is missing.
    if color_by not in df.columns:
        available = ", ".join(map(str, df.columns))
        raise KeyError(
            f"Path renderer requested color_by={color_by!r}, but this column "
            f"is not present in the processed dataframe. "
            f"Available columns: {available}"
        )

    # Extract coordinates and scalar values as floating-point NumPy arrays.
    t = df["_T"].to_numpy(dtype=float)
    w = df["_W"].to_numpy(dtype=float)
    values = df[color_by].to_numpy(dtype=float)

    # Keep only rows where the full tuple (T, W, scalar) is finite so segment
    # coloring remains numerically well-defined.
    mask = np.isfinite(t) & np.isfinite(w) & np.isfinite(values)
    return t[mask], w[mask], values[mask]


def _draw_plain_path(
    ax: Axes,
    t: np.ndarray,
    w: np.ndarray,
    cfg,
) -> None:
    """
    Draw a plain ordered psychrometric path.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes where the path will be drawn.
    t : numpy.ndarray
        One-dimensional array of dry-bulb temperatures.
    w : numpy.ndarray
        One-dimensional array of humidity-ratio coordinates.
    cfg : Any
        Path renderer configuration object.

        The object is expected to expose standard line-style attributes such as
        ``color``, ``alpha``, ``linewidth``, ``linestyle``, ``zorder``, and
        ``label``.

    Returns
    -------
    None
        The path is drawn in-place on the provided axes.

    Notes
    -----
    If the input array is empty, the function returns immediately without
    attempting any plotting call.

    Rounded cap and join styles are used to produce a visually smoother
    trajectory.

    See Also
    --------
    _draw_colored_path
        Alternative renderer for scalar-colored trajectories.

    Examples
    --------
    This helper is typically called internally by ``draw_path`` when no
    ``color_by`` scalar is configured.
    """
    # If no valid points remain after preprocessing, there is nothing to draw.
    if t.size == 0:
        return

    # Draw a single continuous line representing the ordered psychrometric
    # trajectory.
    ax.plot(
        t,
        w,
        color=cfg.color,
        alpha=cfg.alpha,
        linewidth=cfg.linewidth,
        linestyle=cfg.linestyle,
        zorder=cfg.zorder,
        label=cfg.label,
        solid_capstyle="round",
        solid_joinstyle="round",
    )


def _draw_colored_path(
    ax: Axes,
    t: np.ndarray,
    w: np.ndarray,
    values: np.ndarray,
    cfg,
) -> None:
    """
    Draw a segmented path colored by a scalar field.

    Each path segment is colored according to the scalar value associated with
    its starting vertex. Therefore, a path with ``N`` vertices produces
    ``N - 1`` segments and the scalar array attached to the collection is
    ``values[:-1]``.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes where the path will be drawn.
    t : numpy.ndarray
        One-dimensional array of dry-bulb temperatures.
    w : numpy.ndarray
        One-dimensional array of humidity-ratio coordinates.
    values : numpy.ndarray
        One-dimensional scalar array used to color the trajectory segments.
    cfg : Any
        Path renderer configuration object.

        The object is expected to expose colormap and line styling attributes
        such as ``cmap``, ``linewidth``, ``linestyle``, ``alpha``, ``zorder``,
        ``vmin``, ``vmax``, and ``label``.

    Returns
    -------
    None
        The path is drawn in-place on the provided axes.

    Notes
    -----
    If fewer than two valid vertices are available, the function falls back to
    plain-path rendering because no colored segments can be formed.

    The renderer uses ``matplotlib.collections.LineCollection`` for efficient
    segment-wise coloring.

    See Also
    --------
    matplotlib.collections.LineCollection
        Matplotlib class used for segment-wise colored paths.
    _draw_plain_path
        Fallback renderer for degenerate cases.

    Examples
    --------
    This helper is typically called internally by ``draw_path`` when a
    ``color_by`` scalar field is configured.
    """
    # No valid vertices remain after preprocessing.
    if t.size == 0:
        return

    # Segment-colored rendering requires at least two vertices. With only one
    # point, the most sensible behavior is to fall back to the plain path
    # renderer.
    if t.size < 2:
        _draw_plain_path(ax, t, w, cfg)
        return

    # Build the segment array expected by LineCollection:
    # - points has shape (N, 1, 2)
    # - segments has shape (N-1, 2, 2)
    points = np.column_stack([t, w]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create the segment collection with the configured visual styling.
    collection = LineCollection(
        segments,
        cmap=cfg.cmap,
        linewidths=cfg.linewidth,
        linestyles=cfg.linestyle,
        alpha=cfg.alpha,
        zorder=cfg.zorder,
        capstyle="round",
        joinstyle="round",
    )

    # Segment i receives the scalar associated with vertex i. This is the most
    # common and stable convention for ordered trajectory coloring.
    collection.set_array(values[:-1])

    # Apply explicit scalar normalization bounds when provided.
    if cfg.vmin is not None or cfg.vmax is not None:
        collection.set_clim(cfg.vmin, cfg.vmax)

    # Preserve the semantic label so the collection can still participate in
    # legend handling if needed.
    if cfg.label is not None:
        collection.set_label(cfg.label)

    # Add the collection to the axes.
    ax.add_collection(collection)


def _build_path_legend_handle(cfg):
    """
    Build a proxy legend handle for the path renderer.

    For scalar-colored paths, the legend uses the midpoint color of the
    configured colormap. The colorbar remains the canonical element that
    communicates the full scalar scale.

    Parameters
    ----------
    cfg : Any
        Path renderer configuration object.

        The object is expected to expose ``label`` and the styling attributes
        needed to build the proxy line handle.

    Returns
    -------
    matplotlib.lines.Line2D or None
        A proxy legend handle if the path has a visible label, otherwise
        ``None``.

    Notes
    -----
    The proxy handle is necessary because ``LineCollection`` is not always the
    most convenient object for producing a simple, readable legend entry.

    For scalar-colored paths, a single representative color is chosen from the
    midpoint of the configured colormap. This is a legend compromise; the
    colorbar is still the correct place to interpret the scalar mapping.

    See Also
    --------
    draw_path
        Public renderer entry point that returns this proxy handle.

    Examples
    --------
    This helper is used internally after rendering to create a semantic legend
    entry for the drawn path.
    """
    # Without a label, there is no reason to create a legend handle.
    if cfg.label is None:
        return None

    # For plain paths, the legend should reflect the configured fixed color.
    # For scalar-colored paths, use the midpoint color of the colormap as a
    # representative visual proxy.
    if cfg.color_by is None:
        color = cfg.color
    else:
        color = colormaps[cfg.cmap](0.5)

    return Line2D(
        [0],
        [0],
        color=color,
        alpha=cfg.alpha,
        linewidth=cfg.linewidth,
        linestyle=cfg.linestyle,
        label=cfg.label,
    )


def draw_path(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> list:
    """
    Render one ordered path from a processed data layer.

    This is the public entry point of the module. It retrieves the processed
    dataframe in the appropriate order, extracts valid coordinate arrays, draws
    either a plain or scalar-colored psychrometric trajectory, and returns any
    legend proxy handles produced by the renderer.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes where the path will be rendered.
    layer : ProcessedDataLayer
        Processed runtime layer containing the ordered observational data and
        associated configuration metadata.
    cfg : Any
        Path renderer configuration object.

        The object is expected to expose the attributes used throughout the
        helper functions, including ordering options, color mapping options,
        and line styling.

    Returns
    -------
    list
        List of proxy legend handles produced by this renderer.

        The list contains either:

        - one proxy handle when a visible label is configured
        - an empty list when no legend entry should be produced

    Raises
    ------
    KeyError
        If ``cfg.color_by`` references a scalar column that is not present in
        the processed dataframe.

    Notes
    -----
    This renderer operates strictly on processed runtime data. It never:

    - computes psychrometric variables,
    - evaluates indexes,
    - performs raw data ingestion,
    - mutates the runtime layer.

    All those responsibilities must be completed upstream.

    See Also
    --------
    _resolve_order_by
        Resolve the ordering column for the trajectory.
    _extract_plain_arrays
        Extract clean arrays for plain rendering.
    _extract_colored_arrays
        Extract clean arrays for scalar-colored rendering.
    _build_path_legend_handle
        Create the returned proxy legend handle.

    Examples
    --------
    The function is typically invoked by the data-layer dispatcher during chart
    rendering:

    >>> # handles = draw_path(ax, processed_layer, render_cfg)
    >>> # legend_handles.extend(handles)
    """
    # Resolve which column should determine the ordering of the trajectory.
    order_by = _resolve_order_by(layer, cfg)

    # Request the processed dataframe already ordered according to the chosen
    # column. The ProcessedDataLayer owns the details of that ordering logic.
    df = layer.ordered_frame(order_by)

    # Choose the rendering mode based on whether a scalar field was configured
    # for color mapping.
    if cfg.color_by is None:
        t, w = _extract_plain_arrays(df)
        _draw_plain_path(ax, t, w, cfg)
    else:
        t, w, values = _extract_colored_arrays(df, cfg.color_by)
        _draw_colored_path(ax, t, w, values, cfg)

    # Build a proxy legend handle so the centralized legend assembler can add a
    # clean semantic entry for the rendered path.
    handle = _build_path_legend_handle(cfg)
    return [handle] if handle is not None else []
