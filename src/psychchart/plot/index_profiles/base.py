# src/psychchart/plot/index_profiles.py

"""
Semantic profiles for bioclimatic and thermal indexes.

This module defines **index visualization profiles**, i.e. declarative
descriptions of how a given bioclimatic or thermal index should be:

- classified (numeric boundaries),
- colored (visual semantics),
- labeled (human interpretation),
- rendered by default (isolines or filled regions).

The goal is to centralize *semantic meaning* in one place, avoiding
hard-coded thresholds and colors scattered throughout plotting code.
"""

from dataclasses import dataclass
from typing import List, Optional


# =============================================================================
# IndexProfile
# =============================================================================
@dataclass(frozen=True)
class IndexProfile:
    """
    Semantic and visual profile for a bioclimatic or thermal index.

    An ``IndexProfile`` describes **how an index should be interpreted
    and visualized**, independently of how it is computed.

    Think of this class as a *semantic contract* between:
    - scientific meaning (stress levels, comfort classes),
    - visualization (colors, labels),
    - plotting defaults.

    Responsibilities
    ----------------
    - Define canonical numeric boundaries (classification thresholds)
    - Associate colors with index intervals
    - Optionally define human-readable labels
    - Define the default rendering mode
    - Indicate whether clipping to saturation should be applied

    Non-responsibilities
    --------------------
    - Index computation (handled by index implementations, e.g. ITU, HLI)
    - Psychrometric transformations (T–RH → W)
    - Matplotlib rendering logic
    - Axis management or layout

    This strict separation ensures that:
    - scientific semantics are reusable,
    - plotting code remains generic,
    - changes in thresholds or colors do not require code refactoring.

    Parameters
    ----------
    name : str
        Index identifier. Must match the identifiers used by
        ``IndexConfig`` and ``IndexField`` (e.g., ``"ITU"``, ``"HLI"``).
    levels : list of float
        Monotonically increasing numeric boundaries defining
        classification intervals.

        Example:
            ``levels = [68, 72, 76, 80]``

        defines the intervals:
            - 68–72
            - 72–76
            - 76–80
    colors : list of str
        Colors associated with each interval.
        The list length **must be exactly** ``len(levels) - 1``.

        Example:
            ``colors = ["green", "yellow", "orange"]``
    labels : list of str, optional
        Optional human-readable labels associated with each interval.

        Example:
            ``labels = ["Comfort", "Alert", "Heat stress"]``

        If provided, the list length must match ``len(colors)``.
    mode : str, optional
        Default rendering mode for this index profile.

        Supported values:
        - ``"filled"``   : filled contours / zones
        - ``"isolines"`` : contour lines only

        Default is ``"filled"``.
    clip_to_saturation : bool, optional
        Whether visualizations derived from this profile should be
        clipped to the saturation curve (RH = 100%).

        Default is ``True``.

    Notes
    -----
    - This class is immutable (``frozen=True``) to ensure that
      semantic definitions cannot be modified at runtime.
    - Validation of list lengths and monotonicity should be
      performed externally (e.g., during configuration loading).
    """

    # ------------------------------------------------------------------
    # Index identifier (must match IndexConfig / IndexField.index)
    # ------------------------------------------------------------------
    name: str

    # ------------------------------------------------------------------
    # Classification boundaries
    # ------------------------------------------------------------------
    # These values define the numeric intervals used for
    # filled contours, zones or color mapping.
    levels: List[float]

    # ------------------------------------------------------------------
    # Colors for each interval
    # ------------------------------------------------------------------
    # Must have length = len(levels) - 1
    colors: List[str]

    # ------------------------------------------------------------------
    # Optional textual labels for interpretation
    # ------------------------------------------------------------------
    labels: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # Default visualization mode
    # ------------------------------------------------------------------
    # "filled"   → contourf / filled zones
    # "isolines" → contour lines only
    mode: str = "filled"

    # ------------------------------------------------------------------
    # Physical clipping flag
    # ------------------------------------------------------------------
    # If True, all visual elements derived from this profile
    # should be clipped to the saturation curve.
    clip_to_saturation: bool = True

