from __future__ import annotations

from typing import Type

import numpy as np

from psychchart.config import ChartConfig
from psychchart.indexes.base import BaseIndex
from psychchart.psychrometrics import Psychrometrics

from .geometry import ScalarFieldLayer


def build_index_field(
    index_cls: Type[BaseIndex],
    cfg: ChartConfig,
    psych: Psychrometrics,
    resolution: int = 700,
) -> ScalarFieldLayer:
    """
    Build a continuous index field over the physical psychrometric domain.

    The field is built in (T, W), then converted to RH because unified
    indexes are evaluated from context dictionaries and thermodynamic
    indexes typically require {"T", "RH"}.

    Parameters
    ----------
    index_cls : type[BaseIndex]
        Index class to evaluate.
    cfg : ChartConfig
        Chart configuration.
    psych : Psychrometrics
        Psychrometric helper.
    resolution : int, optional
        Grid resolution in both directions.

    Returns
    -------
    ScalarFieldLayer
        Scalar field layer ready to be rendered.

    Raises
    ------
    ValueError
        If the index cannot be evaluated on a thermodynamic grid.
    """
    if not {"T", "RH"}.issubset(index_cls.required_fields):
        raise ValueError(
            f"Index '{index_cls.name}' cannot be evaluated on a psychrometric grid."
        )

    # Build physical grid in (T, W)
    T = np.linspace(cfg.t_min, cfg.t_max, resolution)
    W = np.linspace(cfg.y_min, cfg.y_max, resolution)
    TT, WW = np.meshgrid(T, W)

    # Saturation boundary and physical mask
    W_sat = psych.saturation_humidity_ratio(TT)
    mask = WW <= W_sat

    # Convert W -> RH only after defining the physical domain
    RH = psych.relative_humidity_from_W(TT, WW)

    context = {
        "T": TT,
        "RH": RH,
    }

    Z = index_cls.evaluate(context)
    Z = np.where(mask, Z, np.nan)

    return ScalarFieldLayer(
        name=index_cls.name,
        X=TT,
        Y=WW,
        Z=Z,
        levels=20,
        cmap="Spectral_r",
        alpha=1.0,
    )
