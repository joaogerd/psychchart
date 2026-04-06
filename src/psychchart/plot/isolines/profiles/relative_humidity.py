"""
Semantic profile for relative humidity isolines (RH = const).

This module defines the **canonical semantic profile** for rendering
relative humidity (RH) isolines on a psychrometric chart.

Relative humidity isolines are among the most recognizable elements
of a psychrometric diagram. They are typically represented as:
- dashed curves,
- light gray color,
- labeled with percentages,
- clipped at the saturation curve (RH = 100%).

This profile centralizes these visual conventions in a single,
declarative object, avoiding duplicated styling logic across renderers.
"""

from .base import IsolineProfile


# =============================================================================
# Relative Humidity (RH) semantic profile
# =============================================================================
RH_PROFILE = IsolineProfile(
    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    # Must match the isoline family key expected by the renderer and IsoSet.
    # This string is used as the semantic identifier throughout the plotting
    # pipeline.
    name="relative_humidity",

    # -------------------------------------------------------------------------
    # Default numerical levels
    # -------------------------------------------------------------------------
    # Typical relative humidity levels used in classical psychrometric charts.
    #
    # Values are expressed as fractions (0–1), not percentages.
    # RH = 1.0 (100%) is intentionally excluded here, as it corresponds
    # to the saturation curve, which is handled separately.
    values=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],

    # -------------------------------------------------------------------------
    # Visual style defaults
    # -------------------------------------------------------------------------
    # Light gray dashed lines follow long-established psychrometric
    # chart conventions and avoid visual competition with primary curves
    # such as saturation or comfort zones.
    color="#000000",
    linewidth=0.8,
    linestyle="-",
    alpha=0.5,

    # -------------------------------------------------------------------------
    # Labeling behavior
    # -------------------------------------------------------------------------
    # Relative humidity curves are commonly labeled directly on the chart.
    labels=True,
    label_fontsize=6,

    # Label format:
    # The renderer is expected to receive RH values either as:
    # - fractions (0–1), in which case it should multiply by 100 before formatting
    # - or already scaled to percentage, depending on implementation.
    #
    # This format string assumes percentage values at labeling time.
    label_fmt="%.0f%%",

    # -------------------------------------------------------------------------
    # Rendering hints
    # -------------------------------------------------------------------------
    # Z-order is chosen to sit:
    # - above background grids (T–W grid),
    # - below the saturation curve and emphasized overlays.
    zorder=20,

    # Relative humidity isolines must always be clipped below
    # the saturation curve to avoid physically meaningless regions.
    clip_to_saturation=True,
)

