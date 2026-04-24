"""
Pydantic configuration models for operational cooling overlays.

These models make the operational policy fully declarative and compatible
with AppConfig validation. They are intentionally separate from the runtime
decision engine to preserve clean boundaries between configuration,
calculation, and rendering.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ActionCode = Literal["O0", "O1", "O2", "O3", "O4", "O5"]
TrendCode = Literal["falling", "steady", "rising"]


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
    modifiers: OperationalModifiersConfig = Field(
        default_factory=OperationalModifiersConfig
    )

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
            raise ValueError(
                "action_styles must define exactly O0, O1, O2, O3, O4, O5."
            )

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

    profile: str
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
