"""
Semantic profiles for psychrometric isolines (isopleths).

This module defines **semantic visualization profiles** for classical
psychrometric isoline families (isopleths), such as:

- relative humidity (RH),
- wet-bulb temperature (Tw),
- specific volume (v),
- enthalpy (h),
- dry-bulb temperature (T, auxiliary grids).

A profile represents a **visual and semantic contract**, centralizing
default styling, labeling behavior, and rendering hints for each isoline
family.

Design philosophy
-----------------
This module is strictly **declarative**.

It:
- defines default visual semantics (color, linewidth, linestyle),
- defines default labeling behavior and formatting,
- provides rendering hints (z-order, clipping).

It does NOT:
- compute psychrometric relationships,
- generate isoline coordinates,
- interact with Matplotlib directly,
- validate user configuration.

All numerical computation and drawing logic is delegated to:
- low-level renderers (imperative drawing routines),
- higher-level orchestration code.

This separation ensures:
- consistent visual identity across charts,
- easier theming and customization,
- no hard-coded styles scattered across renderers.
"""

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class IsolineProfile:
    """
    Semantic and visual profile for a psychrometric isoline family.

    This class defines **default visualization semantics** for one
    family of psychrometric isolines (e.g., RH, enthalpy, wet-bulb).

    An ``IsolineProfile`` acts as a *visual defaults contract* between:
    - declarative configuration objects (e.g., ``IsoSet``),
    - low-level rendering routines.

    It does **not** compute isolines or perform plotting. Instead, it
    provides default values that can be:
    - used directly by the renderer,
    - overridden partially or fully by user configuration.

    Parameters
    ----------
    name : str
        Canonical name of the isoline family.

        This **must match** the key used by the renderer and by
        configuration objects (e.g., ``"rh"``, ``"enthalpy"``,
        ``"wet_bulb"``).

    values : sequence of float, optional
        Default numerical levels for this isoline family.

        Examples:
        - Relative humidity: ``[0.1, 0.2, ..., 1.0]``
        - Enthalpy: ``[20, 30, 40, 50]`` (kJ/kg)
        - Specific volume: ``[0.8, 0.9, 1.0]`` (m³/kg)

        If ``None``, the renderer or configuration layer is expected
        to define the levels explicitly.

    color : str, optional
        Default line color.

        This can be any Matplotlib-compatible color specification:
        - named color (e.g., ``"black"``),
        - hex string (e.g., ``"#555555"``),
        - RGB tuple (if supported upstream).

    linewidth : float, default=1.0
        Default line width for the isolines.

    linestyle : str, default="-"
        Default line style (Matplotlib convention).

        Common examples:
        - ``"-"``  : solid
        - ``"--"`` : dashed
        - ``":"``  : dotted
        - ``"-."`` : dash-dot

    labels : bool, default=False
        Whether labels should be drawn by default for this isoline
        family.

        This is only a *default hint*; labeling logic is handled by
        the renderer.

    label_fontsize : int, default=6
        Default font size for isoline labels.

    label_fmt : str, optional
        Default label formatting string.

        This is typically a Python format string applied to the
        isoline value, for example:
        - ``"{:.0f}%"`` for relative humidity,
        - ``"{:.1f}"`` for temperatures,
        - ``"{:.0f} kJ/kg"`` for enthalpy.

    zorder : int, default=20
        Default Matplotlib z-order for this isoline family.

        Higher values are drawn on top of lower ones.

    clip_to_saturation : bool, default=True
        Whether isolines should be clipped at the saturation curve
        by default.

        This is relevant for isolines that may extend into
        physically invalid regions if not clipped.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    name: str

    # ------------------------------------------------------------------
    # Default numerical definition
    # ------------------------------------------------------------------
    values: Optional[Sequence[float]] = None

    # ------------------------------------------------------------------
    # Visual style defaults
    # ------------------------------------------------------------------
    color: Optional[str] = None
    linewidth: float = 1.0
    linestyle: str = "-"
    alpha: float = 1.0

    # ------------------------------------------------------------------
    # Labeling defaults
    # ------------------------------------------------------------------
    labels: bool = False
    label_fontsize: int = 6
    label_fmt: Optional[str] = None

    # ------------------------------------------------------------------
    # Rendering hints
    # ------------------------------------------------------------------
    zorder: int = 20
    clip_to_saturation: bool = True

