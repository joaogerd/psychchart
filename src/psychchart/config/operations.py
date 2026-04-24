"""
Pydantic configuration models for operational cooling overlays.

These models make the operational policy fully declarative and compatible
with AppConfig validation. They are intentionally separate from the runtime
decision engine to preserve clean boundaries between configuration,
calculation, and rendering.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ActionCode = Literal["O0", "O1", "O2", "O3", "O4", "O5"]
TrendCode = Literal["falling", "steady", "rising"]

DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME = "dairy_cooling_default"

DEFAULT_DAIRY_OPERATIONAL_PROFILE: dict[str, Any] = {
    "name": DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME,
    "itu_classes": [
        {"name": "I0", "min": None, "max": 72.0},
        {"name": "I1", "min": 72.0, "max": 78.0},
        {"name": "I2", "min": 78.0, "max": 84.0},
        {"name": "I3", "min": 84.0, "max": 90.0},
        {"name": "I4", "min": 90.0, "max": None},
    ],
    "humidity_classes": [
        {"name": "H0", "min": 0.00, "max": 0.60},
        {"name": "H1", "min": 0.60, "max": 0.75},
        {"name": "H2", "min": 0.75, "max": 1.01},
    ],
    "load_classes": [
        {"name": "A0", "min": 0.000, "max": 0.005, "floor_action": "O0", "representative": 0.0025},
        {"name": "A1", "min": 0.005, "max": 0.010, "floor_action": "O1", "representative": 0.0075},
        {"name": "A2", "min": 0.010, "max": 0.015, "floor_action": "O2", "representative": 0.0125},
        {"name": "A3", "min": 0.015, "max": 0.025, "floor_action": "O3", "representative": 0.0200},
        {"name": "A4", "min": 0.025, "max": None, "floor_action": "O5", "representative": 0.0300},
    ],
    "base_matrix": {
        "I0": {"H0": "O0", "H1": "O0", "H2": "O0"},
        "I1": {"H0": "O1", "H1": "O2", "H2": "O3"},
        "I2": {"H0": "O2", "H1": "O3", "H2": "O4"},
        "I3": {"H0": "O3", "H1": "O4", "H2": "O4"},
        "I4": {"H0": "O5", "H1": "O5", "H2": "O5"},
    },
    "action_styles": {
        "O0": {"label": "Monitoramento", "facecolor": "#d9f0d3"},
        "O1": {"label": "Ventilação básica", "facecolor": "#78c679"},
        "O2": {"label": "Ventilação reforçada", "facecolor": "#ffd92f"},
        "O3": {"label": "Ventilação + aspersão", "facecolor": "#fdae61"},
        "O4": {"label": "Resfriamento máximo", "facecolor": "#f46d43"},
        "O5": {"label": "Emergência", "facecolor": "#d73027"},
    },
    "modifiers": {
        "high_temp_humidity": {"temp_ge": 30.0, "rh_ge": 0.75, "add_levels": 1},
        "high_temp_itu": {"temp_ge": 30.0, "itu_ge": 84.0, "add_levels": 1},
        "rising_load": {"dca_dt_gt": 0.001, "add_levels": 1},
        "recovery": {"dca_dt_lt": -0.001, "ca_lt": 0.010, "itu_lt": 78.0, "add_levels": -1},
    },
}


def default_dairy_operational_profile() -> dict[str, Any]:
    """Return an isolated copy of the default dairy cooling profile mapping."""
    return deepcopy(DEFAULT_DAIRY_OPERATIONAL_PROFILE)


class IntervalClassConfig(BaseModel):
    """Named half-open interval [min, max)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    min: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "IntervalClassConfig":
        if self.min is not None and self.max is not None and self.min >= self.max:
            raise ValueError(
                f"Invalid interval for class {self.name!r}: "
                f"min ({self.min}) must be smaller than max ({self.max})."
            )
        return self


class AccumulatedLoadClassConfig(IntervalClassConfig):
    """Accumulated-load class with enforced minimum action."""

    floor_action: ActionCode
    representative: float | None = None


class OperationalActionStyleConfig(BaseModel):
    """Visual style for one operational action class."""

    model_config = ConfigDict(extra="forbid")

    label: str
    facecolor: str
    edgecolor: str = "none"
    hatch: str | None = None


class HighTempHumidityModifierConfig(BaseModel):
    """Escalation when temperature and humidity are simultaneously high."""

    model_config = ConfigDict(extra="forbid")

    temp_ge: float = 30.0
    rh_ge: float = 0.75
    add_levels: int = 1


class HighTempITUModifierConfig(BaseModel):
    """Escalation when temperature and ITU are simultaneously high."""

    model_config = ConfigDict(extra="forbid")

    temp_ge: float = 30.0
    itu_ge: float = 84.0
    add_levels: int = 1


class RisingLoadModifierConfig(BaseModel):
    """Escalation when accumulated load is rising."""

    model_config = ConfigDict(extra="forbid")

    dca_dt_gt: float = 0.001
    add_levels: int = 1


class RecoveryModifierConfig(BaseModel):
    """De-escalation in genuine recovery conditions."""

    model_config = ConfigDict(extra="forbid")

    dca_dt_lt: float = -0.001
    ca_lt: float = 0.010
    itu_lt: float = 78.0
    add_levels: int = -1


class OperationalModifiersConfig(BaseModel):
    """Grouped operational modifiers."""

    model_config = ConfigDict(extra="forbid")

    high_temp_humidity: HighTempHumidityModifierConfig | None = None
    high_temp_itu: HighTempITUModifierConfig | None = None
    rising_load: RisingLoadModifierConfig | None = None
    recovery: RecoveryModifierConfig | None = None


class OperationalProfileConfig(BaseModel):
    """
    Declarative operational policy.

    The base matrix is indexed as:

        base_matrix[itu_class_name][humidity_class_name] -> action code
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    itu_classes: list[IntervalClassConfig]
    humidity_classes: list[IntervalClassConfig]
    load_classes: list[AccumulatedLoadClassConfig]
    base_matrix: dict[str, dict[str, ActionCode]]
    action_styles: dict[ActionCode, OperationalActionStyleConfig]
    modifiers: OperationalModifiersConfig = Field(default_factory=OperationalModifiersConfig)

    @model_validator(mode="after")
    def validate_matrix_and_styles(self) -> "OperationalProfileConfig":
        itu_names = {item.name for item in self.itu_classes}
        rh_names = {item.name for item in self.humidity_classes}
        load_names = [item.name for item in self.load_classes]

        if len(load_names) != len(set(load_names)):
            raise ValueError("Duplicated accumulated-load class names are not allowed.")

        if set(self.base_matrix.keys()) != itu_names:
            raise ValueError(
                "Operational base_matrix ITU keys do not match declared itu_classes. "
                f"Expected {sorted(itu_names)}, got {sorted(self.base_matrix.keys())}."
            )

        for itu_name, row in self.base_matrix.items():
            if set(row.keys()) != rh_names:
                raise ValueError(
                    f"Operational base_matrix RH keys for ITU class {itu_name!r} do not "
                    f"match declared humidity_classes. Expected {sorted(rh_names)}, "
                    f"got {sorted(row.keys())}."
                )

        expected_actions = {"O0", "O1", "O2", "O3", "O4", "O5"}
        if set(self.action_styles.keys()) != expected_actions:
            raise ValueError("action_styles must define exactly O0, O1, O2, O3, O4, O5.")

        return self

    def to_runtime(self):
        """Convert this config model into the runtime operational profile."""
        from psychchart.operations.profile import OperationalProfile

        return OperationalProfile.from_mapping(self.model_dump())


class OperationalOverlayConfig(BaseModel):
    """
    Rendering configuration for one operational overlay.

    Each overlay projects the operational policy for one accumulated-load class.
    """

    model_config = ConfigDict(extra="forbid")

    profile: str = DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME
    load_class: str
    trend: TrendCode = "steady"

    n_t: int = 220
    n_rh: int = 180

    alpha: float = 0.22
    zorder: float = 0.55

    show_colorbar: bool = False
    show_legend: bool = False
    show_boundaries: bool = True

    boundary_color: str = "black"
    boundary_alpha: float = 0.25
    boundary_linewidth: float = 0.35

    colorbar_label: str = "Ação operacional"
    label: str | None = None
