"""
Semantic profile for humidity-ratio isolines (w = const).

This module defines the canonical semantic profile for rendering
humidity-ratio isolines on a psychrometric chart.

Humidity ratio, also called moisture content or absolute humidity in many
engineering contexts, represents the mass of water vapor per unit mass of
dry air. On a psychrometric chart, these isolines provide direct insight
into the moisture state of the air and are commonly represented as:

light secondary reference lines,

labeled with small decimal values,

clipped at the saturation curve,

visually distinct from temperature- and energy-related isolines.

This profile centralizes the semantic conventions for humidity-ratio
rendering in a single declarative object so that renderers can remain
simple, consistent, and free of duplicated style decisions.


Notes
-----
The meaning of "moisture_quantity" here is specifically humidity ratio
(w), not relative humidity. The two variables are distinct:
- relative humidity: fraction of saturation at a given temperature
- humidity ratio: mass ratio of vapor to dry air
Keeping a dedicated semantic profile prevents ambiguity in renderer code.
Examples
--------
>>> from psychchart.profiles.moisture_profile import MOISTURE_PROFILE
>>> MOISTURE_PROFILE.name
'moisture_quantity'
>>> MOISTURE_PROFILE.label_fmt
'%.3f kg/kg'
>>> MOISTURE_PROFILE.values[0]
0.005
"""

from .base import IsolineProfile

# =============================================================================
# Moisture Content (Humidity Ratio) semantic profile
# =============================================================================
MOISTURE_PROFILE = IsolineProfile(
    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    # Canonical semantic identifier for the humidity-ratio family.
    # The chosen name must match the key expected by IsoSet and downstream
    # rendering components.
    name="moisture_quantity",
    # -------------------------------------------------------------------------
    # Default numerical levels
    # -------------------------------------------------------------------------
    # Typical humidity-ratio values used in standard-pressure charts.
    #
    # Units:
    #     kg water vapor / kg dry air
    #
    # These defaults are intentionally modest and evenly spaced to provide
    # useful moisture references without saturating the figure with labels.
    values=[0.005, 0.010, 0.015, 0.020, 0.025, 0.030],
    
    # -------------------------------------------------------------------------
    # Visual style defaults
    # -------------------------------------------------------------------------
    # Green is semantically appropriate because it often conveys moisture,
    # water content, or environmental quantity in scientific graphics.
    #
    # A dotted line is chosen to keep these isolines visually secondary
    # relative to major thermodynamic boundaries.
    color="#404040",
    linewidth=0.7,
    linestyle=":",
    alpha=0.7,
    
    # -------------------------------------------------------------------------
    # Labeling behavior
    # -------------------------------------------------------------------------
    # These lines are usually labeled because the values are small and not
    # easily inferred from the axes alone.
    labels=True,
    label_fontsize=6,
    # Three decimals are used because humidity ratio is numerically small
    # and lower precision would often hide meaningful differences.
    label_fmt="%.3f kg/kg",
    
    # -------------------------------------------------------------------------
    # Rendering hints
    # -------------------------------------------------------------------------
    # Humidity-ratio lines behave as a secondary reference family, so they
    # are placed slightly below more visually important thermodynamic curves.
    zorder=15,
    
    # Clipping avoids drawing in the supersaturated region, which is outside
    # the valid domain of a conventional psychrometric chart.
    clip_to_saturation=True,
)
