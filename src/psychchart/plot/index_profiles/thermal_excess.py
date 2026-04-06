# psychchart/plot/index_profiles/thermal_excess.py

"""
Semantic profile for the Thermal Excess Index (TE).

This module defines the canonical semantic and visual profile for the
Thermal Excess index used in psychrometric and thermal-stress charts.

The purpose of this module is strictly declarative: it specifies how
Thermal Excess values should be classified and visualized, without
including any numerical computation logic. In other words, this file
answers the question:

    "Once Thermal Excess has been computed, how should it be interpreted
    and rendered on the chart?"

The profile centralizes three essential visualization components:

- classification thresholds (numeric levels),
- interval colors,
- human-readable labels.

This approach improves consistency across the plotting pipeline by
avoiding duplicated styling decisions in renderers, legends, and report
generators.

Notes
-----
- This module contains no formula for Thermal Excess.
- It only defines semantic and visual conventions.
- The profile is intended to be consumed by the plotting layer and
  related configuration/registry mechanisms.
- The semantic identifier defined here must remain compatible with the
  identifier used by the index registry and plotting configuration.

See Also
--------
IndexProfile
    Base declarative structure used to describe semantic visualization
    profiles for chart indexes.
psychchart.indexes.thermal_excess.ThermalExcess
    Numerical implementation of the Thermal Excess index.
"""

from .base import IndexProfile


# =============================================================================
# Thermal Excess semantic profile
# =============================================================================
#
# This object acts as the canonical visualization profile for the
# Thermal Excess index. The plotting system can use it to:
#
# 1. infer default contour/classification levels;
# 2. build categorical legends;
# 3. choose consistent colors for risk intervals;
# 4. keep semantic meaning decoupled from rendering code.
#
# By concentrating these defaults here, the charting pipeline becomes
# more maintainable and easier to extend.
TE_PROFILE = IndexProfile(
    # ------------------------------------------------------------------
    # Index identifier
    # ------------------------------------------------------------------
    # This is the semantic name used by the visualization/profile layer.
    #
    # IMPORTANT:
    # This value must be compatible with the identifier expected by the
    # rest of the system, especially:
    #
    # - configuration files (e.g., YAML index references),
    # - the registry used to resolve indexes,
    # - plot components that associate values with a profile.
    #
    # If the computational backend uses a different canonical name
    # (for example, "THERMAL_EXCESS"), this identifier should be kept
    # synchronized or mapped explicitly by the registry/config layer.
    name="TE",

    # ------------------------------------------------------------------
    # Classification thresholds
    # ------------------------------------------------------------------
    # These values define the interval boundaries used to interpret
    # Thermal Excess magnitudes.
    #
    # Conceptually, the index measures how much the environment exceeds
    # a chosen thermal threshold. Therefore:
    #
    # - near-zero values indicate little or no excess;
    # - moderate values indicate increasing stress potential;
    # - large values indicate severe instantaneous thermal load.
    #
    # Interval interpretation used here:
    #
    #   [0.0,  1.5)  -> Comfort / negligible excess
    #   [1.5,  5.5)  -> Warning / mild excess
    #   [5.5, 11.0)  -> Danger / substantial excess
    #   [11.0, 25.0) -> Fatigue / very strong excess
    #   [25.0, 200]  -> Upper safety cap for visualization coverage
    #
    # Even though extremely large values may be rare in realistic
    # applications, the final upper bound is intentionally extended
    # to guarantee that contouring and categorical rendering always
    # have a closed final interval.
    levels=[0, 1.5, 5.5, 11.0, 25, 200],

    # ------------------------------------------------------------------
    # Colors associated with each interval
    # ------------------------------------------------------------------
    # One color is provided for each interval defined by the levels above.
    #
    # Since there are N level boundaries, there must be N-1 colors.
    # Here:
    #
    #   len(levels)  = 6
    #   len(colors)  = 5
    #
    # The palette follows a progressive thermal-risk logic:
    #
    # - light green      -> safe / comfortable
    # - pale yellow      -> caution
    # - light orange     -> increasing risk
    # - light red        -> strong stress
    # - darker red       -> extreme condition
    #
    # Soft pastel tones were chosen instead of highly saturated colors
    # to keep the background readable when overlaid with isolines,
    # annotations, and other psychrometric elements.
    colors=[
        "#eafaf1",  # Comfort: very low or null excess
        "#fef5e7",  # Warning: mild excess above threshold
        "#fbeee6",  # Danger: moderate-to-high excess
        "#f2d7d5",  # Fatigue: strong excess / pronounced stress
        "#d98880",  # Extreme: upper categorical interval
    ],

    # ------------------------------------------------------------------
    # Human-readable labels
    # ------------------------------------------------------------------
    # These labels can be reused by:
    #
    # - legends,
    # - report summaries,
    # - automatic captions,
    # - plot annotations,
    # - exported metadata.
    #
    # The labels are intentionally concise so they remain readable in
    # figure legends and compact interfaces.
    #
    # As with colors, the number of labels must match the number of
    # intervals defined by the levels.
    labels=[
        "Comfort",
        "Warning",
        "Danger",
        "Fatigue",
        "Extreme",
    ],
)
