from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from psychchart.data.layer_runtime import ProcessedDataLayer
from psychchart.semantics.profiles import get_classification_profile


def _resolve_order_by(layer: ProcessedDataLayer, cfg) -> str | None:
    """
    Resolve the ordering column for classified point rendering.

    This helper determines which column should be used to order the processed
    dataframe before plotting classified points. The ordering rule is shared
    with other temporal or trajectory-aware renderers so that point rendering
    remains consistent with the rest of the visualization pipeline.

    Priority
    --------
    1. ``cfg.order_by``
    2. ``layer.config.temporal.time_col``
    3. ``None``

    Parameters
    ----------
    layer : ProcessedDataLayer
        Processed runtime layer containing both the processed dataframe and the
        original layer configuration.
    cfg : Any
        Classified-points renderer configuration object.

        The object is expected to expose an ``order_by`` attribute. If it does
        not specify one, the helper attempts to fall back to the temporal
        configuration attached to the layer.
    Returns
    -------
    str or None
        Name of the column that should be used to order the dataframe prior to
        rendering, or ``None`` when no ordering information is available.

    Notes
    -----
    This function does not sort the dataframe itself. It only resolves the
    column name that should be used by ``layer.ordered_frame(...)``.

    Keeping this logic in a helper avoids duplicating precedence rules across
    different renderers.

    See Also
    --------
    draw_classified_points
        Public renderer entry point that uses this helper.
    ProcessedDataLayer.ordered_frame
        Method used to retrieve the dataframe already ordered according to the
        resolved column.

    Examples
    --------
    The precedence rule is:

    - explicit renderer configuration first
    - temporal configuration second
    - no ordering as final fallback
    """
    # Renderer-specific ordering has the highest priority because it is the
    # most explicit instruction provided for this concrete render operation.
    if cfg.order_by is not None:
        return cfg.order_by

    # If the renderer does not define an ordering column explicitly, try to use
    # the temporal metadata attached to the processed layer configuration.
    temporal = getattr(layer.config, "temporal", None)
    if temporal is not None:
        return getattr(temporal, "time_col", None)

    # No ordering information is available.
    return None


def _build_points_legend_handle(cfg):
    """
    Build a neutral proxy legend handle for classified observation points.

    This helper creates a legend proxy artist representing the observation
    points themselves, independently from the semantic classes used to color
    them. The intent is to separate two different kinds of legend information:

    - the observational point symbol
    - the semantic class colors

    In this design, class-color semantics are expected to be communicated
    elsewhere, for example through a declarative legend entry such as
    ``classes_from_profile``.

    Parameters
    ----------
    cfg : Any
        Classified-points renderer configuration object.

        The object is expected to expose at least the following attributes:

        - ``label``
        - ``marker``
        - ``edgecolor``
        - ``edgewidth``
        - ``legend_markersize``

    Returns
    -------
    matplotlib.lines.Line2D or None
        Proxy legend handle representing the point symbol, or ``None`` if no
        visible label is configured.

    Notes
    -----
    The proxy is intentionally neutral: it uses a white marker face so that the
    legend entry communicates the observational symbol without conflicting with
    the class-specific colors assigned during rendering.

    See Also
    --------
    draw_classified_points
        Public renderer that returns this proxy handle when applicable.

    Examples
    --------
    This helper is typically used internally after classified points have been
    rendered, so the centralized legend assembler can display a neutral
    observation marker entry.
    """
    # Without a visible label, there is no reason to create a proxy legend
    # handle for the observation points.
    if cfg.label is None:
        return None

    # Use a neutral white marker face because the semantic classes are expected
    # to be documented elsewhere in the legend. This entry represents only the
    # observation-point symbol itself.
    return Line2D(
        [0],
        [0],
        marker=cfg.marker,
        linestyle="None",
        markerfacecolor="white",
        markeredgecolor=cfg.edgecolor,
        markeredgewidth=cfg.edgewidth,
        markersize=cfg.legend_markersize,
        label=cfg.label,
    )


def draw_classified_points(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> list:
    """
    Render observation points classified by a semantic profile.

    This renderer draws point observations in psychrometric space using colors
    determined by a semantic classification profile. Each point receives a
    color according to the class returned by the selected profile for the
    scalar value stored in ``cfg.value_col``.

    The renderer assumes the upstream processing pipeline has already produced a
    dataframe containing:

    - ``"_T"`` for dry-bulb temperature
    - ``"_W"`` for humidity ratio
    - one scalar column referenced by ``cfg.value_col``

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes where the classified points will be drawn.
    layer : ProcessedDataLayer
        Processed runtime layer containing the ordered dataframe and original
        layer configuration.
    cfg : ClassifiedPointsRenderConfig
        Rendering configuration.

        The configuration is expected to expose at least:

        - ``order_by``
        - ``value_col``
        - ``profile``
        - ``size``
        - ``alpha``
        - ``marker``
        - ``edgecolor``
        - ``edgewidth``
        - ``zorder``
        - ``label``
        - ``legend_markersize``

    Returns
    -------
    list
        Proxy legend handles produced by this renderer.

        The returned list contains:

        - one neutral point-symbol handle when ``cfg.label`` is defined
        - an empty list otherwise

    Raises
    ------
    KeyError
        If ``cfg.value_col`` is not present in the processed dataframe.

    Notes
    -----
    This renderer operates strictly on processed runtime data. It does not:

    - compute psychrometric coordinates
    - evaluate raw index formulas
    - ingest raw files
    - define the semantic profile itself

    Instead, it delegates semantic classification to the profile registry via
    ``get_classification_profile``.

    The plotted points are filtered so that only rows with finite ``T``, ``W``,
    and scalar values are rendered.

    See Also
    --------
    get_classification_profile
        Resolve the semantic profile used to classify scalar values.
    _build_points_legend_handle
        Create the neutral legend handle returned by this renderer.
    _resolve_order_by
        Resolve the dataframe ordering column before rendering.

    Examples
    --------
    The renderer is typically invoked by the data-layer dispatcher:

    >>> # handles = draw_classified_points(ax, processed_layer, render_cfg)
    >>> # legend_handles.extend(handles)
    """
    # Resolve which column should define the ordering of the processed
    # dataframe. This is especially important when classified points are meant
    # to preserve temporal order consistency with other renderers.
    order_by = _resolve_order_by(layer, cfg)

    # Ask the processed layer for a dataframe already ordered according to the
    # resolved column. The ProcessedDataLayer owns the details of that logic.
    df = layer.ordered_frame(order_by)

    # The renderer requires one scalar column whose values will be converted
    # into semantic classes through the selected profile. Fail early with a
    # helpful message if that column is missing.
    if cfg.value_col not in df.columns:
        available = ", ".join(map(str, df.columns))
        raise KeyError(
            f"Classified points renderer requested value_col={cfg.value_col!r}, "
            f"but this column is not present in the processed dataframe. "
            f"Available columns: {available}"
        )

    # Resolve the semantic classification profile. The profile is responsible
    # for mapping numeric values to semantic classes, each of which is expected
    # to expose a display color.
    profile = get_classification_profile(cfg.profile)

    # Extract canonical psychrometric coordinates and the scalar values used
    # for semantic classification.
    t = df["_T"].to_numpy(dtype=float)
    w = df["_W"].to_numpy(dtype=float)
    values = df[cfg.value_col].to_numpy(dtype=float)

    # Keep only rows where all required quantities are finite. This prevents
    # invalid points from producing undefined rendering behavior.
    mask = np.isfinite(t) & np.isfinite(w) & np.isfinite(values)
    t = t[mask]
    w = w[mask]
    values = values[mask]

    # Convert each scalar value into a semantic class and extract the color
    # associated with that class. The profile defines the meaning and palette.
    colors = [profile.classify(value).color for value in values]

    # Draw the classified observations only when at least one valid point
    # remains after filtering.
    if t.size:
        ax.scatter(
            t,
            w,
            s=cfg.size,
            c=colors,
            alpha=cfg.alpha,
            marker=cfg.marker,
            edgecolors=cfg.edgecolor,
            linewidths=cfg.edgewidth,
            zorder=cfg.zorder,
        )

    # Build a neutral legend handle representing the observation-point symbol.
    # Semantic classes are expected to be documented separately.
    handle = _build_points_legend_handle(cfg)
    return [handle] if handle is not None else []
