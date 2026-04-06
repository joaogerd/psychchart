"""
Semantic profile for wet-bulb temperature isolines (T_wb = const).

This module defines the canonical semantic profile for rendering
wet-bulb temperature isolines on a psychrometric chart.

Wet-bulb isolines are thermodynamically important because they represent
states associated with adiabatic saturation processes. In practical
psychrometric diagrams, these lines are often used as a visual proxy for
air-cooling behavior under evaporative processes and typically appear as:

dashed oblique lines,

visually distinct from relative humidity and dry-bulb axes,

labeled in degrees Celsius,

clipped at the saturation curve.

This profile centralizes these visual and semantic conventions in a
single declarative object, avoiding duplicated renderer-specific styling
logic across the plotting pipeline.

Notes
-----
This module intentionally contains only the semantic definition of the
wet-bulb profile. Numerical computation of isoline geometry is expected
to be handled elsewhere in the chart engine.
Examples
--------
>>> from psychchart.profiles.wet_bulb import WET_BULB_PROFILE
>>> WET_BULB_PROFILE.name
'wet_bulb'
>>> WET_BULB_PROFILE.values
[0, 5, 10, 15, 20, 25, 30, 35]
>>> WET_BULB_PROFILE.clip_to_saturation
True

"""

from .base import IsolineProfile


# =============================================================================
# Wet Bulb Temperature (T_wb) semantic profile
# =============================================================================
WET_BULB_PROFILE = IsolineProfile(
    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    # Must match the isoline family key expected by the renderer and IsoSet.
    # Essential for calculations involving adiabatic saturation processes.
    name="wet_bulb",

    # -------------------------------------------------------------------------
    # Default numerical levels
    # -------------------------------------------------------------------------
    # Standard wet-bulb levels commonly used in psychrometric charts.
    #
    # Values are expressed in degrees Celsius (°C).
    # The selected increment of 5 °C is a practical default because it balances:
    # - enough thermodynamic detail for interpretation,
    # - limited visual clutter in dense diagrams.
    values=[0, 5, 10, 15, 20, 25, 30, 35],
    
    # -------------------------------------------------------------------------
    # Visual style defaults
    # -------------------------------------------------------------------------
    # Cyan/teal is intentionally used to differentiate wet-bulb curves from:
    # - gray RH curves,
    # - orange enthalpy curves,
    # - green humidity-ratio curves.
    #
    # A dashed linestyle is appropriate because wet-bulb lines act more as
    # a thermodynamic reference family than as a primary boundary.
    color="#505050",
    linewidth=0.7,
    linestyle="--",
    alpha=0.8,
    
    # -------------------------------------------------------------------------
    # Labeling behavior
    # -------------------------------------------------------------------------
    # Wet-bulb isolines are usually labeled because their numerical values
    # are not directly inferable from the primary chart axes.
    labels=True,
    label_fontsize=6,
    # Include an explicit "wb" suffix to avoid confusion with dry-bulb
    # temperature values already present on the X axis.
    label_fmt="%.0f°C wb",
    
    # -------------------------------------------------------------------------
    # Rendering hints
    # -------------------------------------------------------------------------
    # The z-order places wet-bulb lines:
    # - above the background grid,
    # - below emphasized overlays such as comfort regions or saturation.
    zorder=20,
    
    # Wet-bulb lines must be clipped to the saturation curve because
    # at RH = 100% the wet-bulb and dry-bulb temperatures coincide.
    # Extending them beyond saturation would enter a non-physical region
    # for a standard psychrometric chart representation.
    clip_to_saturation=True,
)
