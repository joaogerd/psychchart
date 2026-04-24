"""
Decision engine for operational cooling policy.

The engine is deterministic and auditable:
it receives instantaneous state plus accumulated-load state and returns
an explicit operational action.
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import OperationalAction
from .profile import OperationalProfile


@dataclass(frozen=True)
class OperationalDecision:
    """Traceable output of the operational policy."""

    itu: float
    rh: float
    temperature: float
    accumulated_load: float
    dca_dt: float
    base_action: OperationalAction
    floor_action: OperationalAction
    final_action: OperationalAction
    itu_class: str
    humidity_class: str
    load_class: str
    applied_modifiers: tuple[str, ...]


def _clamp_action(value: int) -> OperationalAction:
    """Clamp integer level to the valid action range."""
    value = max(int(OperationalAction.MONITOR), value)
    value = min(int(OperationalAction.EMERGENCY), value)
    return OperationalAction(value)


def action(
    profile: OperationalProfile,
    *,
    T: float,
    RH: float,
    itu: float,
    ca: float,
    dca_dt: float,
) -> OperationalAction:
    """
    Return the final operational action.

    Parameters
    ----------
    profile:
        Declarative operational policy.
    T:
        Dry-bulb temperature in Celsius.
    RH:
        Relative humidity as fraction in [0, 1].
    itu:
        Instantaneous ITU.
    ca:
        Accumulated thermal load.
    dca_dt:
        Time derivative of accumulated load.
    """
    return action_details(
        profile,
        T=T,
        RH=RH,
        itu=itu,
        ca=ca,
        dca_dt=dca_dt,
    ).final_action


def action_details(
    profile: OperationalProfile,
    *,
    T: float,
    RH: float,
    itu: float,
    ca: float,
    dca_dt: float,
) -> OperationalDecision:
    """
    Return full decision details.

    The rule is:

        final = clamp(
            max(base_action, floor_action)
            + explicit modifiers
        )

    De-escalation is never allowed below the floor imposed by accumulated load.
    """
    itu_class = profile.find_itu_class(itu)
    rh_class = profile.find_humidity_class(RH)
    load_class = profile.find_load_class(ca)

    base_action = profile.base_action(itu, RH)
    floor_action = load_class.floor_action

    level = max(int(base_action), int(floor_action))
    applied: list[str] = []

    mods = profile.modifiers

    if (
        mods.high_temp_humidity is not None
        and T >= mods.high_temp_humidity.temp_ge
        and RH >= mods.high_temp_humidity.rh_ge
    ):
        level += mods.high_temp_humidity.add_levels
        applied.append("high_temp_humidity")

    if (
        mods.high_temp_itu is not None
        and T >= mods.high_temp_itu.temp_ge
        and itu >= mods.high_temp_itu.itu_ge
    ):
        level += mods.high_temp_itu.add_levels
        applied.append("high_temp_itu")

    if (
        mods.rising_load is not None
        and dca_dt > mods.rising_load.dca_dt_gt
    ):
        level += mods.rising_load.add_levels
        applied.append("rising_load")

    if (
        mods.recovery is not None
        and dca_dt < mods.recovery.dca_dt_lt
        and ca < mods.recovery.ca_lt
        and itu < mods.recovery.itu_lt
    ):
        level += mods.recovery.add_levels
        applied.append("recovery")

    # Never allow de-escalation below the accumulated-load floor.
    level = max(level, int(floor_action))
    final_action = _clamp_action(level)

    return OperationalDecision(
        itu=itu,
        rh=RH,
        temperature=T,
        accumulated_load=ca,
        dca_dt=dca_dt,
        base_action=base_action,
        floor_action=floor_action,
        final_action=final_action,
        itu_class=itu_class.name,
        humidity_class=rh_class.name,
        load_class=load_class.name,
        applied_modifiers=tuple(applied),
    )
