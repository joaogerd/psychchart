# psychchart/plot/layers.py
"""
Semantic z-order definitions for psychrometric chart rendering.

This module defines the **canonical visual layering** (z-order)
of all graphical elements used in psychrometric charts.

Purpose
-------
In complex scientific plots, visual clarity depends not only on
*what* is drawn, but also on *in which order* elements are layered.

This module centralizes all z-order values in a single location,
ensuring that:
- visual hierarchy is consistent across the entire package,
- plotting logic remains readable and declarative,
- future changes to layering do not require code duplication.

Design principles
-----------------
- Dependency-free: can be imported anywhere without side effects
- Semantic naming: keys describe *meaning*, not implementation
- Stable ordering: higher values always appear above lower ones
- Single source of truth for z-order management

This module intentionally contains **no plotting code**.
It only provides numeric constants.
"""


# =============================================================================
# Canonical z-order map
# =============================================================================
ZORDER = {
    # ------------------------------------------------------------------
    # Background scalar fields (continuous heatmaps)
    # ------------------------------------------------------------------
    # Examples:
    # - ITU field
    # - HLI field
    # - UTCI field
    #
    # These layers must always remain in the background,
    # below any lines or annotations.
    "index_field": 0,

    # ------------------------------------------------------------------
    # Index-based categorical zones
    # ------------------------------------------------------------------
    # Examples:
    # - Heat stress zones
    # - Comfort classes based on index thresholds
    #
    # These zones overlay index fields but remain
    # below thermodynamic isolines.
    "index_zone": 1,

    # ------------------------------------------------------------------
    # Psychrometric isolines
    # ------------------------------------------------------------------
    # Examples:
    # - Relative humidity lines
    # - Enthalpy lines
    # - Wet-bulb temperature lines
    #
    # These are primary reference guides and should
    # appear above filled zones.
    "isolines": 2,

    # ------------------------------------------------------------------
    # Filled geometric zones (comfort regions, envelopes)
    # ------------------------------------------------------------------
    # Examples:
    # - Thermal comfort zones
    # - Design envelopes
    #
    # These are filled regions and must stay below
    # their own boundaries to avoid visual clutter.
    "zone_fill": 2.5,

    # ------------------------------------------------------------------
    # Zone boundaries (edges)
    # ------------------------------------------------------------------
    # The edges of zones must appear clearly on top
    # of the filled region itself.
    "zone_edge": 3,

    # ------------------------------------------------------------------
    # Discrete reference points
    # ------------------------------------------------------------------
    # Examples:
    # - Observations
    # - Design conditions
    # - Sensor measurements
    #
    # Points should always be clearly visible above
    # zones and isolines.
    "points": 4,

    # ------------------------------------------------------------------
    # Saturation curve (physical boundary)
    # ------------------------------------------------------------------
    # The saturation curve (RH = 100%) represents a
    # **physical limit** and must always be the top-most
    # element in the chart.
    "saturation": 5,
}

