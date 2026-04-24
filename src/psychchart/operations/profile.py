"""
Declarative profile for operational cooling policies.

The profile is deliberately external to the core psychrometric indexes.
It converts environmental and accumulated-load states into operational
actions by explicit, versionable policy rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .enums import OperationalAction


_ACTION_ALIASES: dict[str, OperationalAction] = {
    "O0": OperationalAction.MONITOR,
    "O1": OperationalAction.VENTILATION_BASIC,
    "O2": OperationalAction.VENTILATION_REINFORCED,
    "O3": OperationalAction.VENTILATION_SPRAY,
    "O4": OperationalAction.MAX_COOLING,
    "O5": OperationalAction.EMERGENCY,
}


def action_from_value(value: str | int | OperationalAction) -> OperationalAction:
    """Normalize different action representations to `OperationalAction`."""
    if isinstance(value, OperationalAction):
        return value
    if isinstance(value, int):
        return OperationalAction(value)
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _ACTION_ALIASES:
            return _ACTION_ALIASES[key]
    raise ValueError(f"Invalid operational action: {value!r}")


def _optional_modifier(mapping: Mapping[str, Any], key: str) -> dict[str, Any] | None:
    """
    Return an optional modifier mapping only when it is actually configured.

    Pydantic's ``model_dump()`` keeps optional fields with ``None`` values by
    default. Therefore a runtime mapping may contain keys such as
    ``"high_temp_itu": None``. Checking only ``key in mapping`` is not enough,
    because unpacking ``None`` with ``**None`` raises ``TypeError``. This helper
    treats both missing keys and explicit ``None`` values as disabled modifiers.
    """
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(
            f"Operational modifier {key!r} must be a mapping or None, "
            f"got {type(value).__name__}."
        )
    return dict(value)


@dataclass(frozen=True)
class IntervalClass:
    """
    Named half-open interval [min, max).

    Notes
    -----
    - `min=None` means open lower bound.
    - `max=None` means open upper bound.
    """

    name: str
    min: float | None = None
    max: float | None = None

    def contains(self, value: float) -> bool:
        """Return True if value belongs to this interval."""
        if self.min is not None and value < self.min:
            return False
        if self.max is not None and value >= self.max:
            return False
        return True


@dataclass(frozen=True)
class ITUClass(IntervalClass):
    """Interval class for ITU."""


@dataclass(frozen=True)
class HumidityClass(IntervalClass):
    """Interval class for relative humidity (fraction in [0, 1])."""


@dataclass(frozen=True)
class AccumulatedLoadClass(IntervalClass):
    """
    Interval class for accumulated thermal load.

    Parameters
    ----------
    floor_action:
        Minimum action level that must be enforced for this accumulated-load
        class, regardless of the instantaneous ITU/RH state.
    representative:
        Representative value used when generating static operational zones
        for this class.
    """

    floor_action: OperationalAction = OperationalAction.MONITOR
    representative: float | None = None

    def representative_value(self) -> float:
        """Return a stable representative value for zone generation."""
        if self.representative is not None:
            return self.representative
        if self.min is not None and self.max is not None:
            return 0.5 * (self.min + self.max)
        if self.min is not None:
            return self.min
        if self.max is not None:
            return self.max
        raise ValueError(
            f"Cannot infer representative value for load class {self.name!r}"
        )


@dataclass(frozen=True)
class OperationalActionStyle:
    """Visual style for one operational action class."""

    label: str
    facecolor: str
    edgecolor: str = "none"
    hatch: str | None = None


@dataclass(frozen=True)
class HighTempHumidityModifier:
    """Escalate when both temperature and RH are high."""

    temp_ge: float = 30.0
    rh_ge: float = 0.75
    add_levels: int = 1


@dataclass(frozen=True)
class HighTempITUModifier:
    """Escalate when both temperature and ITU are high."""

    temp_ge: float = 30.0
    itu_ge: float = 84.0
    add_levels: int = 1


@dataclass(frozen=True)
class RisingLoadModifier:
    """Escalate when accumulated load is increasing."""

    dca_dt_gt: float = 0.001
    add_levels: int = 1


@dataclass(frozen=True)
class RecoveryModifier:
    """
    De-escalate only in genuine recovery conditions.

    This modifier never overrides the minimum floor imposed by
    accumulated thermal load.
    """

    dca_dt_lt: float = -0.001
    ca_lt: float = 0.010
    itu_lt: float = 78.0
    add_levels: int = -1


@dataclass(frozen=True)
class OperationalModifiers:
    """Grouped operational modifiers."""

    high_temp_humidity: HighTempHumidityModifier | None = None
    high_temp_itu: HighTempITUModifier | None = None
    rising_load: RisingLoadModifier | None = None
    recovery: RecoveryModifier | None = None


@dataclass(frozen=True)
class OperationalProfile:
    """
    Full declarative operational policy.

    The base matrix is indexed by:
        base_matrix[itu_class_name][humidity_class_name] -> action
    """

    name: str
    itu_classes: tuple[ITUClass, ...]
    humidity_classes: tuple[HumidityClass, ...]
    load_classes: tuple[AccumulatedLoadClass, ...]
    base_matrix: dict[str, dict[str, OperationalAction]]
    action_styles: dict[OperationalAction, OperationalActionStyle]
    modifiers: OperationalModifiers = field(default_factory=OperationalModifiers)

    def find_itu_class(self, itu: float) -> ITUClass:
        """Return the ITU class containing `itu`."""
        for item in self.itu_classes:
            if item.contains(itu):
                return item
        raise ValueError(f"ITU value outside profile domain: {itu}")

    def find_humidity_class(self, rh: float) -> HumidityClass:
        """Return the RH class containing `rh`."""
        for item in self.humidity_classes:
            if item.contains(rh):
                return item
        raise ValueError(f"RH value outside profile domain: {rh}")

    def find_load_class(self, ca: float) -> AccumulatedLoadClass:
        """Return the accumulated-load class containing `ca`."""
        for item in self.load_classes:
            if item.contains(ca):
                return item
        raise ValueError(f"Accumulated load outside profile domain: {ca}")

    def get_load_class(self, name: str) -> AccumulatedLoadClass:
        """Return load class by name."""
        for item in self.load_classes:
            if item.name == name:
                return item
        raise KeyError(f"Unknown load class: {name!r}")

    def base_action(self, itu: float, rh: float) -> OperationalAction:
        """Return matrix action from instantaneous ITU × RH state."""
        itu_class = self.find_itu_class(itu)
        rh_class = self.find_humidity_class(rh)
        return self.base_matrix[itu_class.name][rh_class.name]

    def validate(self) -> None:
        """Validate internal consistency of the profile."""
        itu_names = {c.name for c in self.itu_classes}
        rh_names = {c.name for c in self.humidity_classes}

        if set(self.base_matrix) != itu_names:
            raise ValueError(
                "Base matrix ITU keys do not match declared ITU classes. "
                f"Expected {sorted(itu_names)}, got {sorted(self.base_matrix)}"
            )

        for itu_name, row in self.base_matrix.items():
            if set(row) != rh_names:
                raise ValueError(
                    f"Base matrix RH keys for {itu_name!r} do not match RH classes. "
                    f"Expected {sorted(rh_names)}, got {sorted(row)}"
                )

        for action in OperationalAction:
            if action not in self.action_styles:
                raise ValueError(f"Missing style for action {action.code}")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "OperationalProfile":
        """Build a profile from a YAML-like mapping."""
        itu_classes = tuple(
            ITUClass(
                name=item["name"],
                min=item.get("min"),
                max=item.get("max"),
            )
            for item in data["itu_classes"]
        )

        humidity_classes = tuple(
            HumidityClass(
                name=item["name"],
                min=item.get("min"),
                max=item.get("max"),
            )
            for item in data["humidity_classes"]
        )

        load_classes = tuple(
            AccumulatedLoadClass(
                name=item["name"],
                min=item.get("min"),
                max=item.get("max"),
                floor_action=action_from_value(item["floor_action"]),
                representative=item.get("representative"),
            )
            for item in data["load_classes"]
        )

        base_matrix = {
            itu_name: {
                rh_name: action_from_value(action_code)
                for rh_name, action_code in rh_row.items()
            }
            for itu_name, rh_row in data["base_matrix"].items()
        }

        action_styles = {
            action_from_value(action_code): OperationalActionStyle(
                label=style["label"],
                facecolor=style["facecolor"],
                edgecolor=style.get("edgecolor", "none"),
                hatch=style.get("hatch"),
            )
            for action_code, style in data["action_styles"].items()
        }

        mods_cfg = data.get("modifiers") or {}

        high_temp_humidity_cfg = _optional_modifier(
            mods_cfg,
            "high_temp_humidity",
        )
        high_temp_itu_cfg = _optional_modifier(
            mods_cfg,
            "high_temp_itu",
        )
        rising_load_cfg = _optional_modifier(
            mods_cfg,
            "rising_load",
        )
        recovery_cfg = _optional_modifier(
            mods_cfg,
            "recovery",
        )

        modifiers = OperationalModifiers(
            high_temp_humidity=(
                HighTempHumidityModifier(**high_temp_humidity_cfg)
                if high_temp_humidity_cfg is not None
                else None
            ),
            high_temp_itu=(
                HighTempITUModifier(**high_temp_itu_cfg)
                if high_temp_itu_cfg is not None
                else None
            ),
            rising_load=(
                RisingLoadModifier(**rising_load_cfg)
                if rising_load_cfg is not None
                else None
            ),
            recovery=(
                RecoveryModifier(**recovery_cfg)
                if recovery_cfg is not None
                else None
            ),
        )

        profile = cls(
            name=data["name"],
            itu_classes=itu_classes,
            humidity_classes=humidity_classes,
            load_classes=load_classes,
            base_matrix=base_matrix,
            action_styles=action_styles,
            modifiers=modifiers,
        )
        profile.validate()
        return profile


DEFAULT_DAIRY_COOLING_PROFILE = OperationalProfile.from_mapping(
    {
        "name": "dairy_cooling_default",
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
            {
                "name": "A0",
                "min": 0.000,
                "max": 0.005,
                "floor_action": "O0",
                "representative": 0.0025,
            },
            {
                "name": "A1",
                "min": 0.005,
                "max": 0.010,
                "floor_action": "O1",
                "representative": 0.0075,
            },
            {
                "name": "A2",
                "min": 0.010,
                "max": 0.015,
                "floor_action": "O2",
                "representative": 0.0125,
            },
            {
                "name": "A3",
                "min": 0.015,
                "max": 0.025,
                "floor_action": "O3",
                "representative": 0.0200,
            },
            {
                "name": "A4",
                "min": 0.025,
                "max": None,
                "floor_action": "O5",
                "representative": 0.0300,
            },
        ],
        "base_matrix": {
            "I0": {"H0": "O0", "H1": "O0", "H2": "O0"},
            "I1": {"H0": "O1", "H1": "O2", "H2": "O3"},
            "I2": {"H0": "O2", "H1": "O3", "H2": "O4"},
            "I3": {"H0": "O3", "H1": "O4", "H2": "O4"},
            "I4": {"H0": "O5", "H1": "O5", "H2": "O5"},
        },
        "action_styles": {
            "O0": {
                "label": "Monitoramento",
                "facecolor": "#d9f0d3",
            },
            "O1": {
                "label": "Ventilação básica",
                "facecolor": "#78c679",
            },
            "O2": {
                "label": "Ventilação reforçada",
                "facecolor": "#ffd92f",
            },
            "O3": {
                "label": "Ventilação + aspersão",
                "facecolor": "#fdae61",
            },
            "O4": {
                "label": "Resfriamento máximo",
                "facecolor": "#f46d43",
            },
            "O5": {
                "label": "Emergência",
                "facecolor": "#d73027",
            },
        },
        "modifiers": {
            "high_temp_humidity": {
                "temp_ge": 30.0,
                "rh_ge": 0.75,
                "add_levels": 1,
            },
            "high_temp_itu": {
                "temp_ge": 30.0,
                "itu_ge": 84.0,
                "add_levels": 1,
            },
            "rising_load": {
                "dca_dt_gt": 0.001,
                "add_levels": 1,
            },
            "recovery": {
                "dca_dt_lt": -0.001,
                "ca_lt": 0.010,
                "itu_lt": 78.0,
                "add_levels": -1,
            },
        },
    }
)
