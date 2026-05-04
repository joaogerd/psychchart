"""Public plotting API."""

from __future__ import annotations

from matplotlib.axes import Axes

from .core import PsychChart as _BasePsychChart
from .intervention_zones import draw_intervention_zones


class PsychChart(_BasePsychChart):
    """Psychrometric chart renderer with app-level post-draw layers.

    The core renderer owns the established rendering pipeline. Explicit
    intervention zones are drawn immediately after that pipeline completes so
    they can use the finalized T-W axis domain.
    """

    def draw(self) -> Axes:
        ax = super().draw()
        draw_intervention_zones(
            ax,
            getattr(self, "intervention_zones", None),
            pressure=self.cfg.pressure,
        )
        return ax


__all__ = ["PsychChart"]
