"""Explicit psychrometric intervention-zone renderer.

This module renders declarative intervention regions on top of an existing
psychrometric chart. The layer is intentionally separate from index rendering
and from the declarative accumulated-load operational policy engine.

It answers a geometric management question in T-W space:

    Which physical intervention tends to move this state toward comfort?

Examples include ventilation, dehumidification, mechanical cooling, evaporative
cooling, and hachured regions marking interventions that should be avoided.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import FancyArrow, Patch

from psychchart.config.intervention_zones import (
    InterventionConditionConfig,
    InterventionRuleConfig,
    InterventionZonesConfig,
)
from psychchart.psychrometrics import Psychrometrics


def axis_domain(ax: Axes) -> tuple[float, float, float, float]:
    """Return the current T-W plotting domain from an Axes object."""
    t_min, t_max = ax.get_xlim()
    w_min, w_max = ax.get_ylim()
    return float(t_min), float(t_max), float(w_min), float(w_max)


def condition_mask(
    T: np.ndarray,
    W: np.ndarray,
    condition: InterventionConditionConfig,
) -> np.ndarray:
    """Evaluate an intervention rule condition over a T-W grid."""
    mask = np.ones_like(T, dtype=bool)

    if condition.t_lt is not None:
        mask &= T < condition.t_lt
    if condition.t_lte is not None:
        mask &= T <= condition.t_lte
    if condition.t_gt is not None:
        mask &= T > condition.t_gt
    if condition.t_gte is not None:
        mask &= T >= condition.t_gte

    if condition.w_lt is not None:
        mask &= W < condition.w_lt
    if condition.w_lte is not None:
        mask &= W <= condition.w_lte
    if condition.w_gt is not None:
        mask &= W > condition.w_gt
    if condition.w_gte is not None:
        mask &= W >= condition.w_gte

    return mask


def rule_center_from_condition(
    rule: InterventionRuleConfig,
    *,
    t_min: float,
    t_max: float,
    w_min: float,
    w_max: float,
) -> tuple[float, float]:
    """Estimate a useful label/vector center for a threshold-defined region."""
    condition = rule.when

    left = t_min
    right = t_max
    bottom = w_min
    top = w_max

    if condition.t_gt is not None:
        left = max(left, condition.t_gt)
    if condition.t_gte is not None:
        left = max(left, condition.t_gte)
    if condition.t_lt is not None:
        right = min(right, condition.t_lt)
    if condition.t_lte is not None:
        right = min(right, condition.t_lte)

    if condition.w_gt is not None:
        bottom = max(bottom, condition.w_gt)
    if condition.w_gte is not None:
        bottom = max(bottom, condition.w_gte)
    if condition.w_lt is not None:
        top = min(top, condition.w_lt)
    if condition.w_lte is not None:
        top = min(top, condition.w_lte)

    x = 0.5 * (t_min + t_max) if left >= right else 0.5 * (left + right)
    y = 0.5 * (w_min + w_max) if bottom >= top else 0.5 * (bottom + top)

    return float(x), float(y)


def draw_label(
    ax: Axes,
    rule: InterventionRuleConfig,
    x: float,
    y: float,
    *,
    zorder: float,
) -> object | None:
    """Draw an optional rule label and return the text artist."""
    style = rule.label_style
    if not style.enabled:
        return None

    if style.position is not None:
        x, y = style.position

    text = rule.label
    if rule.kind == "inappropriate" and rule.reason:
        text = f"{rule.label}\n{rule.reason}"

    return ax.text(
        x,
        y,
        text,
        ha=style.ha,
        va=style.va,
        fontsize=style.fontsize,
        color=style.color,
        alpha=style.alpha,
        fontweight=style.fontweight,
        zorder=zorder,
        clip_on=True,
    )


def draw_vector(
    ax: Axes,
    rule: InterventionRuleConfig,
    x: float,
    y: float,
    *,
    zorder: float,
) -> FancyArrow | None:
    """Draw an optional physical displacement vector for a rule."""
    if rule.vector is None or not rule.vector_style.enabled:
        return None

    style = rule.vector_style
    if style.position is not None:
        x, y = style.position

    dx, dy = rule.vector
    return ax.arrow(
        x,
        y,
        dx,
        dy,
        color=style.color,
        alpha=style.alpha,
        linewidth=style.linewidth,
        width=style.width,
        head_width=style.head_width,
        head_length=style.head_length,
        length_includes_head=True,
        zorder=zorder,
        clip_on=True,
    )


def draw_rule_region(
    ax: Axes,
    T_grid: np.ndarray,
    W_grid: np.ndarray,
    rule: InterventionRuleConfig,
    config: InterventionZonesConfig,
    *,
    t_min: float,
    t_max: float,
    w_min: float,
    w_max: float,
) -> list[object]:
    """Draw one operational rule as a filled mask plus optional annotations."""
    artists: list[object] = []
    mask = condition_mask(T_grid, W_grid, rule.when)
    mask &= np.isfinite(T_grid) & np.isfinite(W_grid)
    if not np.any(mask):
        return artists

    field = np.where(mask, 1.0, np.nan)
    is_bad = rule.kind == "inappropriate"
    zorder = rule.zorder if rule.zorder is not None else (
        config.inappropriate_zorder if is_bad else config.zorder
    )

    contour = ax.contourf(
        T_grid,
        W_grid,
        field,
        levels=[0.5, 1.5],
        colors=[rule.facecolor],
        alpha=rule.alpha * config.alpha_scale,
        hatches=[rule.hatch] if rule.hatch else None,
        zorder=zorder,
    )
    artists.append(contour)

    if config.show_boundaries and rule.linewidth > 0:
        boundary = ax.contour(
            T_grid,
            W_grid,
            np.where(mask, 1.0, 0.0),
            levels=[0.5],
            colors=[rule.edgecolor],
            linewidths=[rule.linewidth],
            linestyles=[rule.linestyle],
            alpha=max(rule.alpha, 0.35),
            zorder=zorder + 0.05,
        )
        artists.append(boundary)

    x, y = rule_center_from_condition(
        rule,
        t_min=t_min,
        t_max=t_max,
        w_min=w_min,
        w_max=w_max,
    )

    if config.show_labels:
        label_artist = draw_label(ax, rule, x, y, zorder=config.label_zorder)
        if label_artist is not None:
            artists.append(label_artist)

    if config.show_vectors and not is_bad:
        arrow_artist = draw_vector(ax, rule, x, y, zorder=config.vector_zorder)
        if arrow_artist is not None:
            artists.append(arrow_artist)

    artists.append(
        Patch(
            facecolor=rule.facecolor,
            edgecolor=rule.edgecolor,
            alpha=min(rule.alpha * config.alpha_scale, 1.0),
            hatch=rule.hatch,
            label=rule.label,
        )
    )

    return artists


def physical_grid(
    *,
    t_min: float,
    t_max: float,
    w_min: float,
    w_max: float,
    pressure: float,
    n_t: int,
    n_w: int,
    clip_to_saturation: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Build a Cartesian T-W grid optionally masked above saturation."""
    t_values = np.linspace(t_min, t_max, n_t)
    w_values = np.linspace(w_min, w_max, n_w)
    T_grid, W_grid = np.meshgrid(t_values, w_values)

    if clip_to_saturation:
        W_sat = Psychrometrics.humidity_ratio(T_grid, np.ones_like(T_grid), pressure)
        W_grid = np.where(W_grid <= W_sat, W_grid, np.nan)

    return T_grid, W_grid


def draw_intervention_zones(
    ax: Axes,
    config: InterventionZonesConfig | None,
    *,
    pressure: float,
) -> list[object]:
    """Draw explicit intervention zones on an existing psychrometric axes."""
    if config is None or not config.enabled:
        return []

    rules: Iterable[InterventionRuleConfig] = config.all_rules
    if not rules:
        return []

    t_min, t_max, w_min, w_max = axis_domain(ax)
    T_grid, W_grid = physical_grid(
        t_min=t_min,
        t_max=t_max,
        w_min=w_min,
        w_max=w_max,
        pressure=pressure,
        n_t=config.n_t,
        n_w=config.n_w,
        clip_to_saturation=config.clip_to_saturation,
    )

    artists: list[object] = []
    for rule in rules:
        artists.extend(
            draw_rule_region(
                ax,
                T_grid,
                W_grid,
                rule,
                config,
                t_min=t_min,
                t_max=t_max,
                w_min=w_min,
                w_max=w_max,
            )
        )

    return artists
