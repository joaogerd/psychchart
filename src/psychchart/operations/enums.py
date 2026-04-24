"""
Enumerations for operational cooling decisions.

This module defines the stable public enums used by the operational policy
layer. The policy layer is intentionally separated from the psychrometric
index core so that operational recommendations remain explicit, auditable,
and externally configurable.
"""

from __future__ import annotations

from enum import Enum, IntEnum


class TrendMode(str, Enum):
    """Trend state for accumulated thermal load."""

    FALLING = "falling"
    STEADY = "steady"
    RISING = "rising"


class OperationalAction(IntEnum):
    """
    Ordered operational actions.

    The numeric ordering is intentional:
    higher values represent stronger cooling intervention.
    """

    MONITOR = 0
    VENTILATION_BASIC = 1
    VENTILATION_REINFORCED = 2
    VENTILATION_SPRAY = 3
    MAX_COOLING = 4
    EMERGENCY = 5

    @property
    def code(self) -> str:
        """Return the stable YAML-facing action code."""
        return f"O{int(self)}"
