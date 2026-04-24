#!/usr/bin/env python3
"""
Standalone operational-zones plotter for dairy cooling policy.

This script does NOT depend on psychChart internals.
It computes:
- humidity ratio W from T and RH
- ITU from T and RH
- operational action = f(T, RH, itu, ca, dca_dt)
- gridded operational zones for one accumulated-load class and trend

Usage examples
--------------
python plot_operational_zones_standalone.py
python plot_operational_zones_standalone.py --load-class A2 --trend steady
python plot_operational_zones_standalone.py --load-class A3 --trend rising --show-colorbar
python plot_operational_zones_standalone.py --output zones_A2.png --dpi 200
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch


# =============================================================================
# Enumerations
# =============================================================================


class TrendMode(str, Enum):
    """Trend state for accumulated thermal load."""

    FALLING = "falling"
    STEADY = "steady"
    RISING = "rising"


class OperationalAction(IntEnum):
    """Ordered operational actions."""

    MONITOR = 0
    VENTILATION_BASIC = 1
    VENTILATION_REINFORCED = 2
    VENTILATION_SPRAY = 3
    MAX_COOLING = 4
    EMERGENCY = 5

    @property
    def code(self) -> str:
        """Return stable action code."""
        return f"O{int(self)}"


# =============================================================================
# Declarative runtime profile
# =============================================================================


_ACTION_ALIASES: dict[str, OperationalAction] = {
    "O0": OperationalAction.MONITOR,
    "O1": OperationalAction.VENTILATION_BASIC,
    "O2": OperationalAction.VENTILATION_REINFORCED,
    "O3": OperationalAction.VENTILATION_SPRAY,
    "O4": OperationalAction.MAX_COOLING,
    "O5": OperationalAction.EMERGENCY,
}


def action_from_value(value: str | int | OperationalAction) -> OperationalAction:
    """Normalize action representation."""
    if isinstance(value, OperationalAction):
        return value
    if isinstance(value, int):
        return OperationalAction(value)
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _ACTION_ALIASES:
            return _ACTION_ALIASES[key]
    raise ValueError(f"Invalid operational action: {value!r}")


@dataclass(frozen=True)
class IntervalClass:
    """Named half-open interval [min, max)."""

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
    """Interval class for RH."""


@dataclass(frozen=True)
class AccumulatedLoadClass(IntervalClass):
    """Interval class for accumulated thermal load."""

    floor_action: OperationalAction = OperationalAction.MONITOR
    representative: float | None = None

    def representative_value(self) -> float:
        """Return representative value used for static zone projection."""
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
    """Visual style for one operational action."""

    label: str
    facecolor: str
    edgecolor: str = "none"
    hatch: str | None = None


@dataclass(frozen=True)
class HighTempHumidityModifier:
    """Escalate when temperature and RH are simultaneously high."""

    temp_ge: float = 30.0
    rh_ge: float = 0.75
    add_levels: int = 1


@dataclass(frozen=True)
class HighTempITUModifier:
    """Escalate when temperature and ITU are simultaneously high."""

    temp_ge: float = 30.0
    itu_ge: float = 84.0
    add_levels: int = 1


@dataclass(frozen=True)
class RisingLoadModifier:
    """Escalate when accumulated load is rising."""

    dca_dt_gt: float = 0.001
    add_levels: int = 1


@dataclass(frozen=True)
class RecoveryModifier:
    """De-escalate in genuine recovery conditions."""

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
    Full runtime operational profile.

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
        """Return ITU class containing the value."""
        for item in self.itu_classes:
            if item.contains(itu):
                return item
        raise ValueError(f"ITU value outside profile domain: {itu}")

    def find_humidity_class(self, rh: float) -> HumidityClass:
        """Return RH class containing the value."""
        for item in self.humidity_classes:
            if item.contains(rh):
                return item
        raise ValueError(f"RH value outside profile domain: {rh}")

    def find_load_class(self, ca: float) -> AccumulatedLoadClass:
        """Return accumulated-load class containing the value."""
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

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "OperationalProfile":
        """Build runtime profile from a plain mapping."""
        itu_classes = tuple(
            ITUClass(name=item["name"], min=item.get("min"), max=item.get("max"))
            for item in data["itu_classes"]
        )
        humidity_classes = tuple(
            HumidityClass(name=item["name"], min=item.get("min"), max=item.get("max"))
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
                rh_name: action_from_value(code)
                for rh_name, code in row.items()
            }
            for itu_name, row in data["base_matrix"].items()
        }

        action_styles = {
            action_from_value(code): OperationalActionStyle(
                label=style["label"],
                facecolor=style["facecolor"],
                edgecolor=style.get("edgecolor", "none"),
                hatch=style.get("hatch"),
            )
            for code, style in data["action_styles"].items()
        }

        mods_cfg = data.get("modifiers", {})
        modifiers = OperationalModifiers(
            high_temp_humidity=(
                HighTempHumidityModifier(**mods_cfg["high_temp_humidity"])
                if "high_temp_humidity" in mods_cfg
                else None
            ),
            high_temp_itu=(
                HighTempITUModifier(**mods_cfg["high_temp_itu"])
                if "high_temp_itu" in mods_cfg
                else None
            ),
            rising_load=(
                RisingLoadModifier(**mods_cfg["rising_load"])
                if "rising_load" in mods_cfg
                else None
            ),
            recovery=(
                RecoveryModifier(**mods_cfg["recovery"])
                if "recovery" in mods_cfg
                else None
            ),
        )

        return cls(
            name=data["name"],
            itu_classes=itu_classes,
            humidity_classes=humidity_classes,
            load_classes=load_classes,
            base_matrix=base_matrix,
            action_styles=action_styles,
            modifiers=modifiers,
        )


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
            "O0": {"label": "Monitoramento", "facecolor": "#d9f0d3"},
            "O1": {"label": "Ventilação básica", "facecolor": "#78c679"},
            "O2": {"label": "Ventilação reforçada", "facecolor": "#ffd92f"},
            "O3": {"label": "Ventilação + aspersão", "facecolor": "#fdae61"},
            "O4": {"label": "Resfriamento máximo", "facecolor": "#f46d43"},
            "O5": {"label": "Emergência", "facecolor": "#d73027"},
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


# =============================================================================
# Psychrometric helpers
# =============================================================================


def saturation_vapor_pressure_pa(T_c: np.ndarray) -> np.ndarray:
    """
    Saturation vapor pressure over liquid water in Pa.

    Magnus-type approximation, suitable for plotting purposes.
    """
    return 610.94 * np.exp((17.625 * T_c) / (T_c + 243.04))


def humidity_ratio_from_rh(
    T_c: np.ndarray,
    RH: np.ndarray,
    pressure_pa: float = 101325.0,
) -> np.ndarray:
    """
    Compute humidity ratio W [kg/kg dry air] from dry-bulb temperature and RH.
    """
    e_s = saturation_vapor_pressure_pa(T_c)
    e = RH * e_s
    with np.errstate(divide="ignore", invalid="ignore"):
        W = 0.62198 * e / (pressure_pa - e)
    return W


def saturation_humidity_ratio(
    T_c: np.ndarray,
    pressure_pa: float = 101325.0,
) -> np.ndarray:
    """Compute saturation humidity ratio for plotting the saturation curve."""
    e_s = saturation_vapor_pressure_pa(T_c)
    with np.errstate(divide="ignore", invalid="ignore"):
        W_sat = 0.62198 * e_s / (pressure_pa - e_s)
    return W_sat


def itu_from_t_rh(T_c: np.ndarray, RH: np.ndarray) -> np.ndarray:
    """
    Compute THI/ITU from dry-bulb temperature and relative humidity.

    RH must be provided as fraction in [0, 1].
    Formula used:
        ITU = (1.8*T + 32) - (0.55 - 0.55*RH) * (1.8*T - 26)
    """
    return (1.8 * T_c + 32.0) - (0.55 - 0.55 * RH) * (1.8 * T_c - 26.0)


# =============================================================================
# Operational engine
# =============================================================================


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
    """Clamp integer level into valid action range."""
    value = max(int(OperationalAction.MONITOR), value)
    value = min(int(OperationalAction.EMERGENCY), value)
    return OperationalAction(value)


def action_details(
    profile: OperationalProfile,
    *,
    T: float,
    RH: float,
    itu: float,
    ca: float,
    dca_dt: float,
) -> OperationalDecision:
    """Return full operational decision details."""
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

    if mods.rising_load is not None and dca_dt > mods.rising_load.dca_dt_gt:
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


def action(
    profile: OperationalProfile,
    *,
    T: float,
    RH: float,
    itu: float,
    ca: float,
    dca_dt: float,
) -> OperationalAction:
    """Final public decision function: action = f(T, RH, itu, ca, dca_dt)."""
    return action_details(
        profile,
        T=T,
        RH=RH,
        itu=itu,
        ca=ca,
        dca_dt=dca_dt,
    ).final_action


# =============================================================================
# Zone field generation
# =============================================================================


@dataclass(frozen=True)
class OperationalZoneField:
    """Gridded operational field in psychrometric space."""

    T_grid: np.ndarray
    RH_grid: np.ndarray
    W_grid: np.ndarray
    ITU_grid: np.ndarray
    action_grid: np.ma.MaskedArray
    load_class_name: str
    trend: TrendMode
    representative_ca: float
    representative_dca_dt: float


def representative_dca_dt(
    profile: OperationalProfile,
    trend: TrendMode,
) -> float:
    """Return representative dCA/dt for one trend state."""
    if trend is TrendMode.RISING:
        if profile.modifiers.rising_load is not None:
            return profile.modifiers.rising_load.dca_dt_gt + 1e-6
        return 0.002

    if trend is TrendMode.FALLING:
        if profile.modifiers.recovery is not None:
            return profile.modifiers.recovery.dca_dt_lt - 1e-6
        return -0.002

    return 0.0


def build_operational_zone_field(
    *,
    profile: OperationalProfile,
    load_class_name: str,
    trend: TrendMode,
    t_min: float,
    t_max: float,
    pressure_pa: float = 101325.0,
    y_min: float = 0.0,
    y_max: float = 0.030,
    n_t: int = 260,
    n_rh: int = 180,
) -> OperationalZoneField:
    """Build operational zones for one accumulated-load class and trend."""
    t_values = np.linspace(t_min, t_max, n_t)
    rh_values = np.linspace(0.0, 1.0, n_rh)

    T_grid, RH_grid = np.meshgrid(t_values, rh_values)
    ITU_grid = itu_from_t_rh(T_grid, RH_grid)
    W_grid = humidity_ratio_from_rh(T_grid, RH_grid, pressure_pa=pressure_pa)

    load_class = profile.get_load_class(load_class_name)
    representative_ca = load_class.representative_value()
    representative_rate = representative_dca_dt(profile, trend)

    raw_actions = np.zeros_like(ITU_grid, dtype=int)

    for i in range(T_grid.shape[0]):
        for j in range(T_grid.shape[1]):
            raw_actions[i, j] = int(
                action(
                    profile,
                    T=float(T_grid[i, j]),
                    RH=float(RH_grid[i, j]),
                    itu=float(ITU_grid[i, j]),
                    ca=representative_ca,
                    dca_dt=representative_rate,
                )
            )

    W_sat = saturation_humidity_ratio(T_grid, pressure_pa=pressure_pa)
    mask = ~np.isfinite(W_grid)
    mask |= W_grid < y_min
    mask |= W_grid > y_max
    mask |= W_grid > W_sat

    action_grid = np.ma.masked_array(raw_actions, mask=mask)

    return OperationalZoneField(
        T_grid=T_grid,
        RH_grid=RH_grid,
        W_grid=W_grid,
        ITU_grid=ITU_grid,
        action_grid=action_grid,
        load_class_name=load_class_name,
        trend=trend,
        representative_ca=representative_ca,
        representative_dca_dt=representative_rate,
    )


# =============================================================================
# Plotting
# =============================================================================


def build_action_colormap(profile: OperationalProfile):
    """Build categorical colormap and norm for action classes."""
    ordered_actions = list(OperationalAction)
    colors = [profile.action_styles[action].facecolor for action in ordered_actions]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(-0.5, len(ordered_actions) + 0.5, 1.0), cmap.N)
    return cmap, norm


def legend_handles(profile: OperationalProfile) -> list[Patch]:
    """Build legend handles for operational actions."""
    handles: list[Patch] = []
    for action_value in OperationalAction:
        style = profile.action_styles[action_value]
        handles.append(
            Patch(
                facecolor=style.facecolor,
                edgecolor=style.edgecolor,
                hatch=style.hatch,
                label=f"{action_value.code} — {style.label}",
            )
        )
    return handles


def plot_operational_zone_field(
    field: OperationalZoneField,
    profile: OperationalProfile,
    *,
    pressure_pa: float = 101325.0,
    t_min: float = 0.0,
    t_max: float = 45.0,
    y_min: float = 0.0,
    y_max: float = 0.030,
    alpha: float = 0.85,
    show_boundaries: bool = True,
    show_colorbar: bool = False,
    figsize: tuple[float, float] = (12.0, 7.0),
) -> tuple[plt.Figure, plt.Axes]:
    """Render one standalone operational-zones plot."""
    fig, ax = plt.subplots(figsize=figsize)

    cmap, norm = build_action_colormap(profile)

    mesh = ax.pcolormesh(
        field.T_grid,
        field.W_grid,
        field.action_grid,
        cmap=cmap,
        norm=norm,
        shading="auto",
        alpha=alpha,
        zorder=1.0,
    )

    if show_boundaries:
        ax.contour(
            field.T_grid,
            field.W_grid,
            field.action_grid,
            levels=np.arange(0.5, len(OperationalAction), 1.0),
            colors="black",
            linewidths=0.45,
            alpha=0.45,
            zorder=1.2,
        )

    t_line = np.linspace(t_min, t_max, 500)
    w_sat = saturation_humidity_ratio(t_line, pressure_pa=pressure_pa)
    ax.plot(t_line, w_sat, color="black", linewidth=1.2, zorder=2.0, label="Saturação")

    ax.set_xlim(t_min, t_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Temperatura de bulbo seco (°C)")
    ax.set_ylabel("Razão de umidade W (kg/kg)")
    ax.set_title(
        "Operational zones\n"
        f"Load class={field.load_class_name} | trend={field.trend.value} | "
        f"CA≈{field.representative_ca:.4f} | dCA/dt≈{field.representative_dca_dt:.4f}"
    )

    ax.grid(True, alpha=0.2, linewidth=0.5)

    handles = legend_handles(profile)
    ax.legend(handles=handles, loc="upper left", frameon=True)

    if show_colorbar:
        cbar = plt.colorbar(mesh, ax=ax, pad=0.02)
        cbar.set_ticks(np.arange(len(OperationalAction)))
        cbar.set_ticklabels(
            [profile.action_styles[action_value].label for action_value in OperationalAction]
        )
        cbar.set_label("Ação operacional")

    fig.tight_layout()
    return fig, ax


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Standalone operational-zones plotter."
    )
    parser.add_argument(
        "--load-class",
        default="A2",
        choices=["A0", "A1", "A2", "A3", "A4"],
        help="Accumulated-load class to project.",
    )
    parser.add_argument(
        "--trend",
        default="steady",
        choices=[item.value for item in TrendMode],
        help="Representative trend for dCA/dt.",
    )
    parser.add_argument("--t-min", type=float, default=0.0)
    parser.add_argument("--t-max", type=float, default=45.0)
    parser.add_argument("--y-min", type=float, default=0.0)
    parser.add_argument("--y-max", type=float, default=0.030)
    parser.add_argument("--pressure", type=float, default=101325.0)
    parser.add_argument("--n-t", type=int, default=260)
    parser.add_argument("--n-rh", type=int, default=180)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--output", type=str, default="")
    parser.add_argument(
        "--show-colorbar",
        action="store_true",
        help="Display categorical colorbar.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the standalone plotter."""
    args = parse_args()

    profile = DEFAULT_DAIRY_COOLING_PROFILE
    trend = TrendMode(args.trend)

    field = build_operational_zone_field(
        profile=profile,
        load_class_name=args.load_class,
        trend=trend,
        t_min=args.t_min,
        t_max=args.t_max,
        pressure_pa=args.pressure,
        y_min=args.y_min,
        y_max=args.y_max,
        n_t=args.n_t,
        n_rh=args.n_rh,
    )

    fig, _ = plot_operational_zone_field(
        field,
        profile,
        pressure_pa=args.pressure,
        t_min=args.t_min,
        t_max=args.t_max,
        y_min=args.y_min,
        y_max=args.y_max,
        show_colorbar=args.show_colorbar,
    )

    if args.output:
        fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
        print(f"[INFO] Figure saved to: {args.output}")

    plt.show()


if __name__ == "__main__":
    main()
