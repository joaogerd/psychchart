"""
psychchart.plot
---------------------------------
API + CLI para plotagem de carta psicrométrica altamente customizável.
Autor: Dr. Cláudio Venturo
Licença: LGPL-3.0
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence, Dict, Any, List

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .psychrometrics import Psychrometrics
from .config import ChartConfig, IsoSet, Zone, Point


def _zone_polygon_rh(zone: Zone, pressure: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gera os vértices de um polígono seguindo curvas de umidade relativa
    entre T_min e T_max, fechando pelo lado esquerdo.

    Parâmetros:
        zone     : Zone com atributos t_range=(T_min, T_max) e rh_range=(RH_min, RH_max).
        pressure : Pressão total do ar (Pa).

    Retorna:
        Tuple (T_poly, W_poly) com as coordenadas do polígono.
    """
    t_lo, t_hi   = zone.t_range
    rh_lo, rh_hi = zone.rh_range

    # curva inferior (RH_min)
    t_fwd = np.linspace(t_lo, t_hi, 200)
    w_lo  = Psychrometrics.humidity_ratio(t_fwd, rh_lo, pressure)

    # curva superior (RH_max), reversa
    t_rev = t_fwd[::-1]
    w_hi  = Psychrometrics.humidity_ratio(t_rev, rh_hi, pressure)

    # fecha pelo ponto inicial
    T_poly = np.concatenate([t_fwd, t_rev, [t_lo]])
    W_poly = np.concatenate([w_lo,  w_hi,  [w_lo[0]]])

    return T_poly, W_poly


def _draw_isoline(ax: Axes, key: str, iso: IsoSet,
                  t: np.ndarray, cfg: ChartConfig) -> None:
    """
    Desenha isolinhas de acordo com a 'key' especificada.

    Parâmetros:
        ax   : Eixos Matplotlib onde desenhar.
        key  : 'relative_humidity', 'wet_bulb', 'enthalpy',
               'specific_volume' ou 'moisture_quantity'.
        iso  : IsoSet contendo valores (iso.values), estilo (iso.style),
               cor (iso.color) e opcional colormap (iso.cmap).
        t    : Array de temperaturas (°C).
        cfg  : ChartConfig com parâmetros de plotagem.
    """
    # curva de saturação para mascarar limites
    w_sat = Psychrometrics.humidity_ratio(t, np.ones_like(t), cfg.pressure)

    if key == "relative_humidity":
        for rh in iso.values:
            col = (plt.get_cmap(iso.cmap)(rh) if iso.cmap
                   else iso.color or "k")
            w = Psychrometrics.humidity_ratio(t, rh, cfg.pressure)
            ax.plot(t, w, iso.style, color=col, lw=0.8)

    elif key == "wet_bulb":
        for twb in iso.values:
            W_sat_twb = Psychrometrics.humidity_ratio(twb, 1.0, cfg.pressure)
            h_wb      = Psychrometrics.enthalpy(twb, W_sat_twb)
            W_line    = (h_wb - Psychrometrics.cp * t) \
                        / (Psychrometrics.Hfg + Psychrometrics.cp_v * t)
            mask      = W_line < w_sat
            ax.plot(t[mask], W_line[mask],
                    iso.style, color=iso.color or "gray", lw=0.8)

    elif key == "enthalpy":
        for h_val in iso.values:
            W_line = (h_val - Psychrometrics.cp * t) \
                     / (Psychrometrics.Hfg + Psychrometrics.cp_v * t)
            mask   = (W_line > 0) & (W_line < w_sat)
            ax.plot(t[mask], W_line[mask],
                    iso.style, color=iso.color or "steelblue", lw=0.8)

    elif key == "specific_volume":
        for v in iso.values:
            T_K    = t + 273.15
            W_line = (v * cfg.pressure / (Psychrometrics.Rd * T_K) - 1) \
                     / 1.6078
            mask   = (W_line > 0) & (W_line < w_sat)
            ax.plot(t[mask], W_line[mask],
                    iso.style, color=iso.color or "green", lw=0.8)

    elif key == "moisture_quantity":
        for w_val in iso.values:
            # hlines(y, xmin, xmax, colors=..., linestyles=...)
            ax.hlines(
                y=w_val,
                xmin=cfg.t_min,
                xmax=cfg.t_max,
                colors=iso.color or "green",
                linestyles=iso.style,
                lw=0.8,
                zorder=3  # garante visibilidade
            )


@dataclass
class PsychChart:
    """
    Gera um diagrama psicrométrico completo.

    Atributos:
        cfg       : ChartConfig com parâmetros de escala, pressão e estilo.
        isolines  : Dict[str, IsoSet] mapeando tipos de isolinhas para conjuntos.
        zones     : List[Zone] definindo regiões a destacar.
        points    : List[Point] marcando pontos individuais.
    """

    def __init__(self,
                 cfg: ChartConfig,
                 isolines: Dict[str, IsoSet] = None,
                 zones: List[Zone]       = None,
                 points: List[Point]     = None):
        self.cfg      = cfg
        self.isolines = isolines or {}
        self.zones    = zones or []
        self.points   = points or []
    # ────────────── MÉTODO PRINCIPAL ──────────────
    def draw(self) -> Axes:
        """
        Desenha o gráfico e retorna o objeto Axes.

        Retorna:
            ax: Matplotlib Axes com o diagrama completo.
        """
        if self.cfg.style:
            plt.style.use(self.cfg.style)

        t = np.linspace(self.cfg.t_min, self.cfg.t_max, 600)
        fig, ax = plt.subplots(figsize=(12, 7))

        # Saturation curve (100 % RH)
        w_sat = Psychrometrics.humidity_ratio(t, np.ones_like(t), self.cfg.pressure)
        ax.plot(t, w_sat, lw=2, color="orange", label="100 % UR")

        # Desenha isolinhas
        for key, iso in self.isolines.items():
            if not getattr(iso, "enabled", True):
                continue
            _draw_isoline(ax, key, iso, t, self.cfg)

        # Desenha zonas
        for z in self.zones:
            if z.vertices:
                verts   = np.asarray(z.vertices)
                t_poly  = verts[:, 0]
                rh_vals = verts[:, 1]
                w_poly  = Psychrometrics.humidity_ratio(t_poly, rh_vals, self.cfg.pressure)
                if not np.allclose(verts[0], verts[-1]):
                    t_poly = np.append(t_poly,  t_poly[0])
                    w_poly = np.append(w_poly, w_poly[0])
            elif z.follow_rh and z.t_range and z.rh_range:
                t_poly, w_poly = _zone_polygon_rh(z, self.cfg.pressure)
            elif z.t_range and z.rh_range:
                t_lo, t_hi   = z.t_range
                rh_lo, rh_hi = z.rh_range
                t_poly = [t_lo, t_hi, t_hi, t_lo, t_lo]
                w_poly = [
                    Psychrometrics.humidity_ratio(np.array([t_lo]), np.array([rh_lo]), self.cfg.pressure)[0],
                    Psychrometrics.humidity_ratio(np.array([t_hi]), np.array([rh_lo]), self.cfg.pressure)[0],
                    Psychrometrics.humidity_ratio(np.array([t_hi]), np.array([rh_hi]), self.cfg.pressure)[0],
                    Psychrometrics.humidity_ratio(np.array([t_lo]), np.array([rh_hi]), self.cfg.pressure)[0],
                    Psychrometrics.humidity_ratio(np.array([t_lo]), np.array([rh_lo]), self.cfg.pressure)[0],
                ]
            else:
                raise ValueError(f"Zona '{z.name}' mal definida.")

            ax.plot(t_poly, w_poly, lw=z.linewidth, color=z.edgecolor, label=z.name)
            if z.facecolor and z.facecolor.lower() != "none":
                ax.fill(t_poly, w_poly, facecolor=z.facecolor, alpha=0.20)

        # Desenha pontos
        for p in self.points:
            w_p = Psychrometrics.humidity_ratio(
                np.array([p.t]), np.array([p.rh]), self.cfg.pressure
            )[0]
            ax.scatter(p.t, w_p, marker=p.marker, color=p.color, zorder=5)
            ax.text(p.t, w_p, f" {p.label}",
                    va="center", ha="left", fontsize=9, color=p.color)

        # Labels e limites
        ax.set_xlabel("Temperatura de bulbo seco (°C)")
        ax.set_ylabel("Umidade absoluta (kg vapor / kg ar seco)")
        ax.set_xlim(self.cfg.t_min, self.cfg.t_max)

        y_min = self.cfg.y_min if self.cfg.y_min is not None else 0
        if self.cfg.y_max is not None:
            y_max = self.cfg.y_max
        else:
            # ligeiro sobredimensionamento acima da curva de saturação
            y_max = Psychrometrics.humidity_ratio(
                np.array([self.cfg.t_max]), np.array([1.0]), self.cfg.pressure
            )[0] * 1.05
        ax.set_ylim(y_min, y_max)

        ax.grid(True, ls="--", lw=0.5)
        ax.legend(loc="upper left")

        # Eixo Y direito duplicado
        ax2 = ax.twinx()
        ax2.set_ylim(ax.get_ylim())
        ax2.set_ylabel("Umidade absoluta (kg vapor / kg ar seco) — eixo direito")

        return ax
