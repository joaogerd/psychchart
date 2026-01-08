"""
Validation tests for psychrometric humidity ratio calculations.

This test module verifies that the humidity ratio computed by
:class:`psychchart.psychrometrics.Psychrometrics` is consistent
with reference values commonly found in the literature
(e.g., ASHRAE Fundamentals).

The goal is NOT high-precision HVAC validation, but to ensure
that the implemented formulations are physically consistent
and suitable for psychrometric chart construction.

An acceptable relative error of up to 3% is allowed, which is
consistent with:
- approximations in saturation pressure formulas
- rounding in reference tables
- typical accuracy requirements for diagrammatic use
"""

import math
from psychchart.psychrometrics import Psychrometrics


# =============================================================================
# Reference values
# =============================================================================
# Reference points are approximate values obtained from
# ASHRAE psychrometric charts and standard literature.
#
# Units:
# - Temperature: °C
# - Relative humidity: fraction (0–1)
# - Humidity ratio: kg_vapor / kg_dry_air
#
# These values are intentionally rounded, reflecting the
# resolution typically found in printed psychrometric charts.

REFERENCE_POINTS = [
    # (Dry-bulb temperature [°C], Relative humidity [-], W_ref [kg/kg])
    (20.0, 0.50, 0.0073),
    (25.0, 0.50, 0.0099),
    (30.0, 0.60, 0.0160),
]


# =============================================================================
# Utility functions
# =============================================================================
def relative_error(a: float, b: float) -> float:
    """
    Compute the relative error between two values.

    Parameters
    ----------
    a : float
        Computed value.
    b : float
        Reference value.

    Returns
    -------
    err : float
        Relative error defined as |a - b| / b.

    Notes
    -----
    Relative error is preferred here over absolute error because
    humidity ratio varies by more than one order of magnitude
    across the psychrometric chart.
    """
    return abs(a - b) / b


# =============================================================================
# Tests
# =============================================================================
def test_reference_humidity_ratio_points():
    """
    Validate humidity ratio against reference psychrometric values.

    For each reference point (T, RH), this test computes the
    humidity ratio using the implemented formulation and compares
    it to a literature-based reference value.

    The test passes if the relative error is less than 3%.

    Rationale for the 3% tolerance
    ------------------------------
    - The Magnus–Tetens saturation pressure formula is an
      approximation.
    - Reference psychrometric charts are discretized and rounded.
    - The goal of psychchart is diagram construction and
      comparative analysis, not HVAC-grade precision.

    A tighter tolerance would be misleading given these
    constraints.
    """
    for T, RH, W_ref in REFERENCE_POINTS:
        # Compute humidity ratio using the implemented method
        W = Psychrometrics.humidity_ratio(T, RH)

        # Compute relative error
        err = relative_error(W, W_ref)

        # Assert physical consistency within acceptable tolerance
        assert err < 0.03, (
            f"T={T} °C, RH={RH}: "
            f"W={W:.5f}, ref={W_ref:.5f}, "
            f"relative error={err:.3%}"
        )

