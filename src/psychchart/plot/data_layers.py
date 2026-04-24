"""
Unified dispatcher for canonical data-layer renderers.

This module centralizes the runtime dispatch logic responsible for drawing
processed data layers on top of the psychrometric chart.

The dispatcher receives already processed runtime layers and forwards each
configured render block to the appropriate low-level renderer. In addition to
drawing the visual content, it also collects legend handles returned by those
renderers so that legend construction can be performed later by a dedicated
legend assembly module.

Architecture
------------
This module intentionally separates concerns as follows:

- low-level renderer modules:
  responsible for drawing one specific visual representation
- this dispatcher:
  responsible for selecting which renderer to call at runtime
- legend assembly module:
  responsible for combining renderer-returned handles into the final legend

This keeps rendering extensible while avoiding duplicated dispatch logic across
the plotting pipeline.

Notes
-----
This module does not:

- compute psychrometric coordinates
- process raw observational data
- evaluate indexes
- assemble the final chart legend

It only dispatches already processed layers to the appropriate canonical
renderer.

Examples
--------
The dispatcher is typically called from the chart core:

>>> # legend_handles = draw_data_layers(chart, ax)
>>> # draw_chart_legend(ax, chart.cfg, legend_handles)
"""

from __future__ import annotations

from matplotlib.axes import Axes

from .data_renderers.annotate import draw_annotate
from .data_renderers.density import draw_density
from .data_renderers.path import draw_path
from .data_renderers.points import draw_points
from .data_renderers.scalar_field import draw_scalar_field
from .data_renderers.scatter import draw_scatter
from .data_renderers.classified_points import draw_classified_points

def _normalize_renderer_result(result) -> list:
    """
    Normalize renderer return values into a clean legend-handle list.

    Different low-level renderers may return their legend contributions in
    slightly different shapes, such as:

    - ``None`` when no legend entry is produced
    - a single handle object
    - a list of handles

    This helper converts all supported cases into a predictable list-based
    representation and removes any ``None`` entries.

    Parameters
    ----------
    result : Any
        Raw value returned by a low-level renderer.

    Returns
    -------
    list
        Normalized list of legend handles.

    Notes
    -----
    This function does not validate whether the returned objects are valid
    Matplotlib legend handles. It only normalizes the container shape.

    See Also
    --------
    draw_data_layers
        Main dispatcher function that uses this helper to collect legend
        handles consistently.

    Examples
    --------
    Normalize a missing renderer result:

    >>> _normalize_renderer_result(None)
    []

    Normalize a list with empty entries:

    >>> _normalize_renderer_result([1, None, 2])
    [1, 2]

    Normalize a single handle:

    >>> _normalize_renderer_result("handle")
    ['handle']
    """
    # A renderer may explicitly return ``None`` to signal that it produced no
    # legend contribution. Convert that into an empty list so the collector can
    # operate uniformly.
    if result is None:
        return []

    # If the renderer already returned a list, keep only the non-empty entries.
    # This is useful when some renderer branches conditionally return handles.
    if isinstance(result, list):
        return [item for item in result if item is not None]

    # For scalar return values, wrap them in a list so the downstream collector
    # always works with one consistent container type.
    return [result]


def draw_data_layers(chart, ax: Axes) -> list:
    """
    Draw all processed canonical data layers and collect legend handles.

    This function is the runtime dispatcher for processed data layers. It
    iterates over all processed layers stored on the chart instance, then
    iterates over each render configuration attached to each layer, and calls
    the appropriate low-level renderer according to the render type.

    During this process, it also collects any legend handles returned by the
    renderers so that the caller can later assemble a centralized chart legend.

    Parameters
    ----------
    chart : PsychChart
        Parent chart instance.

        The chart is expected to expose a ``data_layers`` attribute containing
        processed runtime layers.
    ax : matplotlib.axes.Axes
        Target axes where the renderers should draw their graphical elements.

    Returns
    -------
    list
        Flat list of legend handles returned by the low-level renderers.

        If no data layers are available, an empty list is returned.

    Raises
    ------
    ValueError
        If a render block specifies an unknown canonical render type.

    Notes
    -----
    Supported canonical render types currently include:

    - ``"points"``
    - ``"scatter"``
    - ``"path"``
    - ``"annotate"``
    - ``"density"``
    - ``"scalar_field"``

    The dispatch logic is intentionally explicit rather than dynamic so the
    supported renderer surface remains clear, readable, and easy to maintain.

    The function assumes all layers are already processed. It does not mutate
    the chart, the axes state beyond drawing, or the layer configuration.

    See Also
    --------
    _normalize_renderer_result
        Helper used to normalize renderer return values.
    draw_points
        Low-level renderer for point-based layers.
    draw_scatter
        Low-level renderer for scatter layers.
    draw_path
        Low-level renderer for ordered path layers.
    draw_annotate
        Low-level renderer for annotation layers.
    draw_density
        Low-level renderer for density fields.
    draw_scalar_field
        Low-level renderer for scalar-field layers.
    draw_classified_points
    

    Examples
    --------
    The dispatcher is typically invoked by the chart core:

    >>> # legend_handles = draw_data_layers(chart, ax)
    >>> # if legend_handles:
    >>> #     draw_chart_legend(ax, chart.cfg, legend_handles)
    """
    # Retrieve processed runtime data layers from the chart. If the attribute is
    # missing or empty, there is nothing to draw and no legend handles to
    # collect.
    layers = getattr(chart, "data_layers", None)
    if not layers:
        return []

    # Accumulate legend handles produced by the individual low-level renderers.
    legend_handles: list = []

    # Iterate through each processed layer and through each render block
    # declared for that layer.
    for layer in layers:
        for render_cfg in layer.config.render:
            render_type = render_cfg.type

            # Dispatch explicitly based on the canonical renderer name.
            # This keeps the supported render surface obvious and fail-fast.
            if render_type == "points":
                result = draw_points(ax, layer, render_cfg)
            elif render_type == "scatter":
                result = draw_scatter(ax, layer, render_cfg)
            elif render_type == "path":
                result = draw_path(ax, layer, render_cfg)
            elif render_type == "annotate":
                result = draw_annotate(ax, layer, render_cfg)
            elif render_type == "density":
                result = draw_density(ax, chart, layer, render_cfg)
            elif render_type == "scalar_field":
                result = draw_scalar_field(ax, layer, render_cfg)
            elif render_type == "classified_points":
                result = draw_classified_points(ax, layer, render_cfg)
            else:
                # Unknown render types are configuration/runtime errors and
                # should fail immediately with a clear message.
                raise ValueError(
                    f"Unknown data-layer render type: {render_type!r}"
                )

            # Normalize the renderer result and merge it into the flat legend
            # handle collection.
            legend_handles.extend(_normalize_renderer_result(result))

    return legend_handles
