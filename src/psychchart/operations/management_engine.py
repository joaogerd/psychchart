"""
Bovine thermal-management decision engine.

The functions in this module convert environmental and accumulated thermal-load
states into discrete operational actions. They are intentionally separated from
plotting so the same rules can be used by static charts, interactive apps, and
future data-processing pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class ManagementAction:
    """Semantic description of one thermal-management action."""

    code: int
    key: str
    label: str
    color: str


ACTIONS: tuple[ManagementAction, ...] = (
    ManagementAction(0, "monitoring", "Monitoring / no active cooling", "#2c7bb6"),
    ManagementAction(1, "natural_ventilation", "Natural ventilation", "#abd9e9"),
    ManagementAction(2, "shade_ventilation", "Shade + ventilation", "#ffffbf"),
    ManagementAction(3, "forced_ventilation", "Forced ventilation", "#fdae61"),
    ManagementAction(4, "sprinkling_ventilation", "Sprinkling + ventilation", "#f46d43"),
    ManagementAction(5, "intensive_cooling", "Intensive cooling", "#d73027"),
    ManagementAction(6, "emergency_response", "Emergency heat response", "#7f0000"),
)

ACTION_BY_CODE: Mapping[int, ManagementAction] = {item.code: item for item in ACTIONS}


def action_labels() -> dict[int, str]:
    """Return action labels indexed by numeric action code."""
    return {item.code: item.label for item in ACTIONS}


def action_colors() -> dict[int, str]:
    """Return action colors indexed by numeric action code."""
    return {item.code: item.color for item in ACTIONS}


def classify_management(
    T,
    RH,
    ITU,
    CTA=0.0,
    trend: str = "steady",
):
    """
    Classify bovine thermal-management action.

    Parameters
    ----------
    T, RH, ITU, CTA : scalar or array-like
        Environmental state and accumulated thermal load. ``RH`` is expected as
        a fraction in ``[0, 1]``. ``CTA`` may be scalar or array-like.
    trend : {"falling", "steady", "rising"}, default="steady"
        Thermal-load trend. A rising trend escalates one action level, while a
        falling trend de-escalates one level.

    Returns
    -------
    ndarray or int
        Encoded action code. Scalars return ``int``; arrays return ``ndarray``.
    """
    if trend not in {"falling", "steady", "rising"}:
        raise ValueError("'trend' must be one of: 'falling', 'steady', 'rising'.")

    T_arr, RH_arr, ITU_arr, CTA_arr = np.broadcast_arrays(
        np.asarray(T, dtype=float),
        np.asarray(RH, dtype=float),
        np.asarray(ITU, dtype=float),
        np.asarray(CTA, dtype=float),
    )

    action = np.zeros_like(ITU_arr, dtype=int)

    mild = ITU_arr < 72.0
    moderate = (ITU_arr >= 72.0) & (ITU_arr < 78.0)
    severe = (ITU_arr >= 78.0) & (ITU_arr < 84.0)
    extreme = ITU_arr >= 84.0

    dry_or_moderate_air = RH_arr < 0.70
    humid_air = RH_arr >= 0.70
    high_temperature = T_arr >= 30.0

    low_load = CTA_arr < 20.0
    medium_load = (CTA_arr >= 20.0) & (CTA_arr < 50.0)
    high_load = CTA_arr >= 50.0

    action[mild & low_load] = 0
    action[mild & ~low_load] = 1

    action[moderate & low_load] = 1
    action[moderate & medium_load] = 2
    action[moderate & high_load] = 3

    action[severe & low_load] = 3
    action[severe & medium_load & dry_or_moderate_air] = 4
    action[severe & medium_load & humid_air] = 5
    action[severe & high_load] = 5

    action[extreme] = 6
    action[high_temperature & humid_air & high_load] = 6

    if trend == "rising":
        action = np.minimum(action + 1, max(ACTION_BY_CODE))
    elif trend == "falling":
        action = np.maximum(action - 1, 0)

    if action.ndim == 0:
        return int(action)
    return action


def describe_action(code: int) -> str:
    """Return a human-readable label for one action code."""
    return ACTION_BY_CODE[int(code)].label
