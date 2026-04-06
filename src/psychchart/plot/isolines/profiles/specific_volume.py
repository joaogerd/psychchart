"""
Semantic profile for specific-volume isolines (v = const).

This module defines the canonical semantic profile for rendering
specific-volume isolines on a psychrometric chart.

Specific volume expresses the volume occupied by a unit mass of dry air
and is a useful thermodynamic variable for airflow analysis, duct design,
and state interpretation in moist-air systems. On a psychrometric chart,
these isolines are usually represented as:

steeply sloped auxiliary lines,

visually de-emphasized compared with RH or enthalpy curves,

labeled in m³/kg,

clipped at the saturation curve.

Because specific-volume lines are often consulted less frequently than
relative humidity, dry-bulb temperature, or enthalpy, this profile gives
them a restrained visual weight while still preserving semantic clarity.

Notes
-----
Specific-volume isolines typically have a steeper inclination than many
other psychrometric families. Because of this geometry, excessive visual
emphasis can quickly make the chart difficult to read. The reduced alpha,
thinner linewidth, and lower z-order are deliberate design decisions.
Examples
--------
>>> from psychchart.profiles.specific_volume import SPECIFIC_VOLUME_PROFILE
>>> SPECIFIC_VOLUME_PROFILE.name
'specific_volume'
>>> SPECIFIC_VOLUME_PROFILE.values
[0.75, 0.8, 0.85, 0.9, 0.95]
>>> SPECIFIC_VOLUME_PROFILE.clip_to_saturation
True

"""

from .base import IsolineProfile

# =============================================================================
# Specific Volume (v) semantic profile
# =============================================================================
SPECIFIC_VOLUME_PROFILE = IsolineProfile(
    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    # Canonical semantic identifier for specific-volume isolines.
    # Must match the family name recognized by the chart renderer.
    name="specific_volume",
    
    # -------------------------------------------------------------------------
    # Default numerical levels
    # -------------------------------------------------------------------------
    # Typical specific-volume values expressed in cubic meters per kilogram
    # of dry air (m³/kg).
    #
    # These values are suitable as a compact default range for many standard
    # psychrometric plotting domains.
    values=[0.75, 0.80, 0.85, 0.90, 0.95],
    
    # -------------------------------------------------------------------------
    # Visual style defaults
    # -------------------------------------------------------------------------
    # A muted warm-gray/brown tone is intentionally used so these lines remain
    # informative but do not dominate the chart.
    #
    # The long-dash custom pattern reduces visual noise and helps distinguish
    # the family from both dotted and dashed isolines already present.
    color="#707070",
    linewidth=0.5,
    linestyle=(0, (5, 10)),  # Long sparse dashes for minimal clutter
    alpha=0.5,
    
    # -------------------------------------------------------------------------
    # Labeling behavior
    # -------------------------------------------------------------------------
    labels=True,
    label_fontsize=6,
    # Two decimals are enough for practical reading while avoiding overly
    # long labels on a dense plot.
    label_fmt="%.2f m³/kg",
    
    # -------------------------------------------------------------------------
    # Rendering hints
    # -------------------------------------------------------------------------
    # Lowest emphasis among the thermodynamic isoline families in this group.
    zorder=10,
    
    # Clipping preserves physical validity within the chart domain.
    clip_to_saturation=True,
)
