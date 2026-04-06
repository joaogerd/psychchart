from __future__ import annotations

import pandas as pd

from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from psychchart.temporal.registry import TEMPORAL_OVERLAY_REGISTRY
from psychchart.psychrometrics import Psychrometrics


def draw_temporal_overlays(chart, ax: Axes) -> None:
    """
    Draw all configured temporal overlays on top of the psychrometric chart.

    These overlays are independent from the instantaneous index system.
    They typically represent trajectories, temporal memory, or physiological
    history mapped onto psychrometric coordinates.
    """
    overlays = getattr(chart, "temporal_overlays", None)
    if not overlays:
        return

    for cfg in overlays:
        _draw_single_temporal_overlay(chart, ax, cfg)


def _draw_single_temporal_overlay_(chart, ax: Axes, cfg) -> None:
    """
    Draw one temporal overlay according to its registered evaluator.
    """
    overlay_type = str(cfg.type).upper()

    if overlay_type not in TEMPORAL_OVERLAY_REGISTRY:
        available = ", ".join(sorted(TEMPORAL_OVERLAY_REGISTRY))
        raise KeyError(
            f"Unknown temporal overlay '{cfg.type}'. Available: {available}"
        )

    evaluator = TEMPORAL_OVERLAY_REGISTRY[overlay_type]

    df = pd.read_csv(cfg.data)

    result = evaluator(
        df,
        t_col=cfg.t_col,
        rh_col=cfg.rh_col,
        time_col=cfg.time_col,
        cta_col=cfg.cta_col,
        sort=True,
    )

    data = result.data

    # --------------------------------------------------------------
    # Convert trajectory coordinates from (T, RH) to (T, W)
    # RH is expected as fraction [0, 1], matching your current index system.
    # --------------------------------------------------------------
    T = data[result.t_col].to_numpy()
    RH = data[result.rh_col].to_numpy()
    W = Psychrometrics.humidity_ratio(T, RH, P=chart.cfg.pressure)

    # --------------------------------------------------------------
    # Path
    # --------------------------------------------------------------
    if cfg.show_path:
        ax.plot(
            T,
            W,
            color=cfg.path_color,
            alpha=cfg.path_alpha,
            linewidth=cfg.path_linewidth,
            zorder=cfg.path_zorder,
        )

    # --------------------------------------------------------------
    # Markers + annotations
    # --------------------------------------------------------------
    for i, row in data.reset_index(drop=True).iterrows():
        x = row[result.t_col]
        y = Psychrometrics.humidity_ratio(
            row[result.t_col],
            row[result.rh_col],
            P=chart.cfg.pressure,
        )
        color = row[result.color_col]

        ax.scatter(
            [x],
            [y],
            s=cfg.point_size,
            color=color,
            edgecolors=cfg.point_edgecolor,
            linewidths=cfg.point_edgewidth,
            zorder=cfg.point_zorder,
        )

        if cfg.annotate_every is not None and cfg.annotate_every > 0:
            if i % cfg.annotate_every == 0:
                label = cfg.annotation_template.format(
                    time=row[result.time_col],
                    cta=row[result.cta_col],
                )
                ax.text(
                    x + cfg.annotation_dx,
                    y + cfg.annotation_dy,
                    label,
                    fontsize=cfg.annotation_fontsize,
                    fontweight=cfg.annotation_fontweight,
                    color=cfg.annotation_color,
                    zorder=cfg.annotation_zorder,
                )

    # --------------------------------------------------------------
    # Legend
    # --------------------------------------------------------------
    print(cfg)
    if cfg.show_legend:

        legend_elements = [
            Patch(facecolor='#a1d99b', label='ZONA VERDE: Recuperação / Eficiência Alta'),
            Patch(facecolor='#fdbb84', label='ALERTA: Início do Acúmulo (Acione Aspersão)'),
            Patch(facecolor='#fc8d59', label='CRÍTICO: Risco de Saturação em 12-15h'),
            Patch(facecolor='#d7301f', label='FADIGA TÉRMICA: Colapso da Resposta (Emergência)'),
            Line2D(
                [0], [0],
                color=cfg.path_color,
                alpha=cfg.path_alpha,
                linewidth=cfg.path_linewidth,
                label="Animal trajectory",
            ),

        ]
        ax.legend(handles=legend_elements, loc=cfg.legend_loc, title="Status Biológico (Previsão 15h)")



def _draw_single_temporal_overlay(chart, ax: Axes, cfg) -> None:
    """
    Draw one temporal overlay according to its registered evaluator.

    This renderer plots:
    - the temporal trajectory of one animal on the psychrometric chart,
    - colored points representing the biological/thermal state,
    - optional annotations,
    - a refined legend describing the thermal-state categories.

    Notes
    -----
    RH is expected as fraction [0, 1].
    The trajectory is converted from (T, RH) to (T, W) so that it matches
    the psychrometric chart coordinate system.
    """
    overlay_type = str(cfg.type).upper()

    if overlay_type not in TEMPORAL_OVERLAY_REGISTRY:
        available = ", ".join(sorted(TEMPORAL_OVERLAY_REGISTRY))
        raise KeyError(
            f"Unknown temporal overlay '{cfg.type}'. Available: {available}"
        )

    evaluator = TEMPORAL_OVERLAY_REGISTRY[overlay_type]

    df = pd.read_csv(cfg.data)

    result = evaluator(
        df,
        t_col=cfg.t_col,
        rh_col=cfg.rh_col,
        time_col=cfg.time_col,
        cta_col=cfg.cta_col,
        sort=True,
    )

    data = result.data

    # ------------------------------------------------------------------
    # Convert trajectory coordinates from (T, RH) to (T, W)
    # ------------------------------------------------------------------
    T = data[result.t_col].to_numpy()
    RH = data[result.rh_col].to_numpy()
    W = Psychrometrics.humidity_ratio(T, RH, P=chart.cfg.pressure)

    # ------------------------------------------------------------------
    # Draw temporal path
    # ------------------------------------------------------------------
    if cfg.show_path:
        ax.plot(
            T,
            W,
            color=cfg.path_color,
            alpha=cfg.path_alpha,
            linewidth=cfg.path_linewidth,
            zorder=cfg.path_zorder,
            solid_capstyle="round",
            solid_joinstyle="round",
        )

    # ------------------------------------------------------------------
    # Draw points + optional annotations
    # ------------------------------------------------------------------
    for i, row in data.reset_index(drop=True).iterrows():
        x = row[result.t_col]
        y = Psychrometrics.humidity_ratio(
            row[result.t_col],
            row[result.rh_col],
            P=chart.cfg.pressure,
        )
        color = row[result.color_col]

        ax.scatter(
            [x],
            [y],
            s=cfg.point_size,
            color=color,
            edgecolors=cfg.point_edgecolor,
            linewidths=cfg.point_edgewidth,
            zorder=cfg.point_zorder,
        )

        if cfg.annotate_every is not None and cfg.annotate_every > 0:
            if i % cfg.annotate_every == 0:
                label = cfg.annotation_template.format(
                    time=row[result.time_col],
                    cta=row[result.cta_col],
                )
                ax.text(
                    x + cfg.annotation_dx,
                    y + cfg.annotation_dy,
                    label,
                    fontsize=cfg.annotation_fontsize,
                    fontweight=cfg.annotation_fontweight,
                    color=cfg.annotation_color,
                    zorder=cfg.annotation_zorder,
                )

    # ------------------------------------------------------------------
    # Refined legend
    # ------------------------------------------------------------------
    if cfg.show_legend:
        legend_elements = [
            Line2D(
                [0], [0],
                color=cfg.path_color,
                alpha=cfg.path_alpha,
                linewidth=cfg.path_linewidth,
                label="Trajetória temporal",
            ),
            Line2D(
                [0], [0],
                marker="o",
                linestyle="None",
                markerfacecolor="white",
                markeredgecolor=cfg.point_edgecolor,
                markeredgewidth=cfg.point_edgewidth,
                markersize=7,
                label="Observações horárias",
            ),
            Patch(
                facecolor="#a1d99b",
                edgecolor="none",
                label="Recuperação",
            ),
            Patch(
                facecolor="#fdbb84",
                edgecolor="none",
                label="Alerta",
            ),
            Patch(
                facecolor="#fc8d59",
                edgecolor="none",
                label="Crítico",
            ),
            Patch(
                facecolor="#d7301f",
                edgecolor="none",
                label="Fadiga térmica",
            ),
        ]

        legend = ax.legend(
            handles=legend_elements,
            loc=cfg.legend_loc,
            title="Estado térmico acumulado",
            frameon=True,
            fancybox=True,
            framealpha=0.95,
            borderpad=0.8,
            labelspacing=0.6,
            handlelength=2.2,
            handletextpad=0.8,
            borderaxespad=0.8,
            fontsize=9,
            title_fontsize=10,
        )

        frame = legend.get_frame()
        frame.set_linewidth(0.8)
        frame.set_edgecolor("0.75")
        frame.set_facecolor("white")
