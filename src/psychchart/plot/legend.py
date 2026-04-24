"""
Centralized legend assembly for psychchart.

This module builds the final chart legend from two independent sources:

1. automatic renderer handles returned by low-level data renderers
2. declarative manual entries stored in ``ChartConfig.legend``

It supports both regular legend artists and grouped marker entries
representing colored observations.

The goal of this module is to keep legend construction centralized and
independent from low-level renderers. This preserves the architectural
separation between:

- data rendering
- semantic configuration
- final legend assembly

Notes
-----
This module is intentionally focused on legend composition only.

It is responsible for:

- converting declarative legend entries into Matplotlib proxy artists
- normalizing automatically collected renderer handles
- deduplicating legend items by label
- creating the final legend with consistent styling

It is not responsible for:

- drawing chart data
- collecting raw observational data
- computing psychrometric quantities
- evaluating thermal indexes

Examples
--------
Build a legend from automatic and manual entries:

>>> import matplotlib.pyplot as plt
>>> from matplotlib.lines import Line2D
>>> fig, ax = plt.subplots()
>>> auto = [Line2D([0], [0], color="red", label="Trajectory")]
>>> class DummyLegend:
...     show = True
...     entries = []
...     loc = "best"
...     title = None
...     frameon = True
...     fancybox = True
...     framealpha = 0.9
...     borderpad = 0.4
...     labelspacing = 0.5
...     handlelength = 2.0
...     handletextpad = 0.8
...     borderaxespad = 0.5
...     fontsize = 10
...     title_fontsize = 11
>>> class DummyCfg:
...     legend = DummyLegend()
>>> draw_chart_legend(ax, DummyCfg(), auto)
>>> ax.get_legend() is not None
True
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, List, Tuple

from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from psychchart.semantics.profiles import get_classification_profile

LegendItem = Tuple[object, str]

def _build_manual_legend_items(entry) -> List[LegendItem]:
    """
    Convert one declarative legend entry into a Matplotlib handle-label pair.

    This helper translates one validated manual legend entry into a proxy
    artist plus its visible label. The returned handle can then be passed to
    ``Axes.legend`` even when no corresponding plotted artist exists in the
    axes.

    Supported entry types are:

    - ``"patch"``
    - ``"line"``
    - ``"marker"``
    - ``"marker_scale"``

    Parameters
    ----------
    entry : LegendEntry
        One validated declarative legend entry.

        The object is expected to expose a ``type`` field and all attributes
        required by the corresponding legend-entry variant.

    Returns
    -------
    tuple of object and str
        A pair ``(handle, label)`` where ``handle`` is a Matplotlib-compatible
        legend proxy artist and ``label`` is the user-facing legend text.

        For ``"marker_scale"``, the handle is a tuple of multiple marker proxy
        artists grouped under a single label.

    Raises
    ------
    ValueError
        If the legend entry type is not supported.

    Notes
    -----
    Returning explicit ``(handle, label)`` pairs keeps legend assembly uniform
    for both automatic and declarative items. This is especially useful because
    grouped marker-scale entries do not rely on a single Matplotlib artist.

    See Also
    --------
    _normalize_auto_handles
        Normalize renderer-returned automatic handles into the same pair-based
        representation.
    draw_chart_legend
        Public function that assembles the final chart legend.

    Examples
    --------
    Create a patch legend item:

    >>> class Dummy:
    ...     type = "patch"
    ...     facecolor = "red"
    ...     edgecolor = "black"
    ...     label = "Danger zone"
    >>> handle, label = _build_manual_legend_item(Dummy())
    >>> label
    'Danger zone'

    Create a grouped marker-scale item:

    >>> class Dummy:
    ...     type = "marker_scale"
    ...     label = "Gradient"
    ...     cmap = "viridis"
    ...     samples = [0.1, 0.5, 0.9]
    ...     marker = "o"
    ...     markeredgecolor = "black"
    ...     markeredgewidth = 0.8
    ...     markersize = 7.0
    >>> handle, label = _build_manual_legend_item(Dummy())
    >>> isinstance(handle, tuple)
    True
    >>> label
    'Gradient'
    """
    # -------------------------------------------------------------------------
    # Filled semantic regions
    # -------------------------------------------------------------------------
    # Patch legend entries represent filled areas such as comfort zones,
    # warning envelopes, operational regions, or classified polygons.
    if entry.type == "patch":
        return [
            (
                Patch(
                    facecolor=entry.facecolor,
                    edgecolor=entry.edgecolor,
                ),
                entry.label,
            )
        ]
    
    # -------------------------------------------------------------------------
    # Stroke-based semantic entities
    # -------------------------------------------------------------------------
    # Line entries are used for trajectories, thresholds, isolines, envelopes,
    # and any other visual element whose meaning is primarily communicated by
    # a stroked path instead of a filled area.
    if entry.type == "line":
        return [
            (
                Line2D(
                    [0],
                    [0],
                    color=entry.color,
                    alpha=entry.alpha,
                    linewidth=entry.linewidth,
                    linestyle=entry.linestyle,
                ),
                entry.label,
            )
        ]
    
    # -------------------------------------------------------------------------
    # Point-like semantics
    # -------------------------------------------------------------------------
    # Marker entries are used when the legend should communicate a single,
    # fixed symbol representing stations, observations, events, or samples.
    if entry.type == "marker":
        return [
            (
                Line2D(
                    [0],
                    [0],
                    marker=entry.marker,
                    linestyle="None",
                    markerfacecolor=entry.markerfacecolor,
                    markeredgecolor=entry.markeredgecolor,
                    markeredgewidth=entry.markeredgewidth,
                    markersize=entry.markersize,
                ),
                entry.label,
            )
        ]
    
    # -------------------------------------------------------------------------
    # Semantic class expansion from a registered profile
    # -------------------------------------------------------------------------
    # This mode differs from the others because it does not return one legend
    # row. Instead, it expands a semantic profile into multiple rows, one per
    # classification rule, preserving the semantic granularity of the profile.
    if entry.type == "classes_from_profile":
        profile = get_classification_profile(entry.profile)
    
        return [
            (
                Patch(
                    facecolor=rule.color,
                    edgecolor="none",
                ),
                rule.label,
            )
            for rule in profile.rules
        ]
    
    # -------------------------------------------------------------------------
    # Defensive failure for unsupported configuration
    # -------------------------------------------------------------------------
    # Failing fast here is intentional: legend configuration errors should be
    # detected at render time with a clear message rather than silently ignored.
    raise ValueError(f"Unsupported legend entry type: {entry.type!r}")

def _normalize_auto_handles(auto_handles: Iterable | None) -> List[LegendItem]:
    """
    Normalize renderer-returned automatic handles into ``(handle, label)`` pairs.

    Low-level renderers usually return Matplotlib artists directly. This helper
    filters that raw sequence and converts it into a predictable representation
    that is compatible with the manual legend-item pipeline.

    A handle is retained only if:

    - it is not ``None``
    - it exposes a visible legend label
    - its label does not start with ``"_"``

    Parameters
    ----------
    auto_handles : iterable or None
        Raw handles returned by low-level renderers during the drawing
        pipeline.

    Returns
    -------
    list of tuple
        List of ``(handle, label)`` pairs ready to be merged with manual legend
        items.

    Notes
    -----
    This function does not deduplicate labels. It only filters invalid or
    intentionally hidden handles and standardizes the output shape.

    The underscore label rule follows normal Matplotlib legend behavior, where
    artists with labels beginning with ``"_"`` are hidden from legends.

    See Also
    --------
    _deduplicate_items
        Remove duplicated labels after normalization.
    draw_chart_legend
        Public function that assembles the final chart legend.

    Examples
    --------
    >>> h1 = Line2D([0], [0], color="red", label="Path")
    >>> h2 = Line2D([0], [0], color="blue", label="_hidden")
    >>> items = _normalize_auto_handles([h1, None, h2])
    >>> len(items)
    1
    >>> items[0][1]
    'Path'
    """
    # A missing automatic handle sequence is normalized to an empty list so the
    # rest of the legend pipeline can operate uniformly.
    if auto_handles is None:
        return []

    items: List[LegendItem] = []

    for handle in auto_handles:
        # Skip absent handles returned by optional renderer branches.
        if handle is None:
            continue

        # Retrieve the artist label safely, even if the object is only
        # partially Matplotlib-like.
        label = getattr(handle, "get_label", lambda: None)()
        if not label or str(label).startswith("_"):
            continue

        items.append((handle, str(label)))

    return items


def _deduplicate_items(items: Iterable[LegendItem]) -> List[LegendItem]:
    """
    Deduplicate legend items by label while preserving first-occurrence order.

    Parameters
    ----------
    items : iterable of tuple
        Sequence of ``(handle, label)`` pairs.

    Returns
    -------
    list of tuple
        Deduplicated list of ``(handle, label)`` pairs.

    Notes
    -----
    Deduplication is based only on the visible label, which is usually the
    desired behavior for legends. Multiple renderers may produce different
    artists that represent the same semantic concept, and in that situation the
    legend should normally show only the first occurrence.

    The use of ``OrderedDict`` preserves the insertion order, keeping legend
    output stable and readable.

    See Also
    --------
    _normalize_auto_handles
        Standardize automatic handles before deduplication.
    _build_manual_legend_item
        Build declarative legend items in the same pair-based format.

    Examples
    --------
    >>> h1 = Line2D([0], [0], color="red", label="Path")
    >>> h2 = Line2D([0], [0], color="blue", label="Path")
    >>> out = _deduplicate_items([(h1, "Path"), (h2, "Path")])
    >>> len(out)
    1
    >>> out[0][1]
    'Path'
    """
    unique: OrderedDict[str, object] = OrderedDict()
    for handle, label in items:
        # Preserve only the first occurrence of each visible label so legend
        # order remains stable and semantically clean.
        if label not in unique:
            unique[label] = handle

    return [(handle, label) for label, handle in unique.items()]


def draw_chart_legend(ax: Axes, cfg, auto_handles: Iterable | None = None) -> None:
    """
    Draw the final chart legend from automatic handles plus manual entries.

    This is the public entry point of the module. It combines low-level
    renderer handles with declarative legend entries stored in
    ``ChartConfig.legend`` and builds the final Matplotlib legend.

    The function performs the following steps:

    1. reads the validated legend configuration
    2. exits early if the legend is disabled
    3. normalizes automatic renderer handles
    4. appends manual legend items declared in configuration
    5. deduplicates the final item list by label
    6. creates the Matplotlib legend
    7. applies consistent styling to the legend frame

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes where the legend should be drawn.
    cfg : ChartConfig
        Validated chart configuration.

        The object is expected to expose a ``legend`` attribute containing a
        validated ``LegendConfig`` instance or ``None``.
    auto_handles : iterable, optional
        Raw handles returned by renderers during the drawing pipeline.

    Returns
    -------
    None
        The legend is drawn in-place on the target axes.

    Notes
    -----
    Grouped marker-scale entries are supported through ``HandlerTuple`` so a
    tuple of colored marker artists can be displayed as a single legend row.

    This function intentionally does not decide legend semantics by itself. It
    only assembles legend items already defined either by renderer output or by
    declarative configuration.

    See Also
    --------
    _build_manual_legend_item
        Convert manual legend entries into proxy artists.
    _normalize_auto_handles
        Convert automatic renderer handles into a pair-based format.
    _deduplicate_items
        Remove duplicate legend labels before final rendering.
    matplotlib.legend_handler.HandlerTuple
        Handler used to render grouped marker tuples in one legend entry.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> auto = [Line2D([0], [0], color="red", label="Trajectory")]
    >>> class DummyLegend:
    ...     show = True
    ...     entries = []
    ...     loc = "best"
    ...     title = None
    ...     frameon = True
    ...     fancybox = True
    ...     framealpha = 0.9
    ...     borderpad = 0.4
    ...     labelspacing = 0.5
    ...     handlelength = 2.0
    ...     handletextpad = 0.8
    ...     borderaxespad = 0.5
    ...     fontsize = 10
    ...     title_fontsize = 11
    >>> class DummyCfg:
    ...     legend = DummyLegend()
    >>> draw_chart_legend(ax, DummyCfg(), auto)
    >>> ax.get_legend() is not None
    True
    """
    # Retrieve the legend configuration from the validated chart config. If the
    # legend block is absent or explicitly disabled, there is nothing to draw.
    legend_cfg = getattr(cfg, "legend", None)
    if legend_cfg is None or not legend_cfg.show:
        return

    # Normalize automatically returned handles from low-level renderers.
    items = _normalize_auto_handles(auto_handles)

    # Append declarative manual legend items after the automatic ones. This
    # ordering preserves runtime-first semantics while still allowing explicit
    # user additions.
    if legend_cfg.entries:
        for entry in legend_cfg.entries:
            items.extend(_build_manual_legend_items(entry))

    # Remove duplicated labels while preserving first-occurrence order.
    items = _deduplicate_items(items)
    if not items:
        return

    # Split the normalized items back into the separate structures expected by
    # Matplotlib's legend API.
    handles = [handle for handle, _label in items]
    labels = [_label for _handle, _label in items]

    # Grouped marker-scale entries are represented as tuples of proxy markers.
    # ``HandlerTuple`` tells Matplotlib how to draw them as one legend row.
#    handler_map = {tuple: HandlerTuple(ndivide=None, pad=0.4)}

    # Build the final legend using the validated layout and typography options.
    legend = ax.legend(
        handles,
        labels,
        loc=legend_cfg.loc,
        title=legend_cfg.title,
        frameon=legend_cfg.frameon,
        fancybox=legend_cfg.fancybox,
        framealpha=legend_cfg.framealpha,
        borderpad=legend_cfg.borderpad,
        labelspacing=legend_cfg.labelspacing,
        handlelength=legend_cfg.handlelength,
        handletextpad=legend_cfg.handletextpad,
        borderaxespad=legend_cfg.borderaxespad,
        fontsize=legend_cfg.fontsize,
        title_fontsize=legend_cfg.title_fontsize,
#        handler_map=handler_map,
    )

    # Apply a consistent visual frame style so legends remain coherent across
    # figures regardless of Matplotlib defaults.
    frame = legend.get_frame()
    frame.set_linewidth(0.8)
    frame.set_edgecolor("0.75")
    frame.set_facecolor("white")
