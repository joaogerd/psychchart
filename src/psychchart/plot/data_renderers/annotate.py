"""
Renderer for periodic annotations over processed data layers.
"""

from __future__ import annotations

import numbers

from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def _format_alias_value(value):
    """Return cleaner scalar aliases for template formatting.

    Pandas row iteration may convert integer-like values to floats when a row
    mixes integer and float columns. For human-readable temporal labels, values
    like 0.0 and 1.0 are normalized back to 0 and 1.
    """
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        if float(value).is_integer():
            return int(value)
    return value


def _get_row_value(row, field_name: str):
    """Return a row value with a clear error when the field is missing."""
    if field_name not in row.index:
        available = ", ".join(map(str, row.index))
        raise KeyError(
            f"Annotation renderer requested field {field_name!r}, "
            f"but it is not present in the processed dataframe. "
            f"Available columns: {available}"
        )
    return row[field_name]


def _build_annotation_context(row, cfg) -> dict:
    """Build the formatting context used by the annotation template.

    The context exposes every dataframe column by its original name and adds the
    stable aliases ``time`` and ``value``. When ``value_field`` is configured,
    the alias ``cta`` is also populated for compatibility with old temporal
    overlay templates such as ``{time}h\n(CTA:{cta:.0f})``.
    """
    context = {str(key): value for key, value in row.items()}

    if cfg.time_field:
        context["time"] = _format_alias_value(_get_row_value(row, cfg.time_field))
    else:
        context.setdefault("time", "")

    if cfg.value_field:
        value = _get_row_value(row, cfg.value_field)
        context["value"] = value
        context["cta"] = value
    else:
        context.setdefault("value", "")
        context.setdefault("cta", "")

    return context


def draw_annotate(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> None:
    """
    Render periodic text annotations.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    layer : ProcessedDataLayer
        Processed runtime layer.
    cfg : AnnotateRenderConfig
        Rendering configuration.
    """
    if cfg.every <= 0:
        return

    order_by = None
    if layer.config.temporal is not None:
        order_by = layer.config.temporal.time_col

    df = layer.ordered_frame(order_by).reset_index(drop=True)

    for i, row in df.iterrows():
        if i % cfg.every != 0:
            continue

        context = _build_annotation_context(row, cfg)

        try:
            label = cfg.template.format(**context)
        except KeyError as exc:
            missing = exc.args[0]
            available = ", ".join(sorted(context))
            raise KeyError(
                f"Annotation template references unknown field {missing!r}. "
                f"Available template fields: {available}"
            ) from exc

        ax.text(
            row["_T"] + cfg.dx,
            row["_W"] + cfg.dy,
            label,
            fontsize=cfg.fontsize,
            fontweight=cfg.fontweight,
            color=cfg.color,
            zorder=cfg.zorder,
        )
