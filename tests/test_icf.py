"""
Unit tests for the Functional Comfort Index (ICF).

This module contains a comprehensive test suite validating the numerical,
physical, and conceptual behavior of the :class:`psychchart.indexes.icf.ICF`
index.

Testing philosophy
------------------
The tests are designed to ensure that:

- The mathematical formulation of the ICF is correctly implemented.
- The index respects its theoretical bounds [0, 1].
- Undefined behavioral states are handled gracefully.
- Physically impossible inputs are explicitly rejected.

The tests intentionally focus on **behavioral edge cases**, since the ICF
is a purely behavioral index and does not depend on environmental variables
(e.g., temperature or humidity).

All tests assume **instantaneous observations** (single time step).
"""

import math

import pytest

from psychchart.indexes.icf import ICF


def test_icf_basic():
    """
    Test the ICF under balanced behavioral contributions.

    This test verifies the nominal case where productive behaviors
    (feeding + rumination) and compensatory behavior (panting)
    contribute equally.

    Given:
        rumination = 20
        panting    = 20

    Expected:
        ICF = (20) / (20 + 20) = 20 / 40 = 0.5

    This test validates:
    - correct arithmetic implementation,
    - correct handling of typical mixed-behavior scenarios.
    """
    icf = ICF()
    obs = {"rumination": 20, "panting": 20}

    val = icf.compute(obs)

    assert val == pytest.approx(0.5)


def test_icf_upper_bound():
    """
    Test the upper theoretical bound of the ICF.

    This scenario represents a fully functional behavioral state,
    with no compensatory thermoregulatory response (panting).

    Given:
        feeding    > 0
        rumination > 0
        panting    = 0

    Expected:
        ICF = 1.0

    This test ensures that:
    - the index correctly reaches its maximum value,
    - no numerical artifacts reduce the upper bound.
    """
    icf = ICF()
    obs = {"rumination": 10, "panting": 0}

    assert icf.compute(obs) == 1.0


def test_icf_lower_bound():
    """
    Test the lower theoretical bound of the ICF.

    This scenario represents extreme thermal stress, where all observable
    behavior is compensatory (panting), and no productive behavior occurs.

    Given:
        rumination = 0
        panting    > 0

    Expected:
        ICF = 0.0

    This test validates:
    - correct identification of complete functional loss,
    - numerical stability at the lower bound.
    """
    icf = ICF()
    obs = {"rumination": 0, "panting": 10}

    assert icf.compute(obs) == 0.0


def test_icf_undefined():
    """
    Test the undefined behavioral state.

    This case occurs when **no behavior is observed at all**, which may
    happen due to:
    - sensor failure,
    - missing data,
    - filtering or aggregation artifacts.

    Given:
        rumination = 0
        panting    = 0

    Expected:
        ICF = NaN

    Rationale:
    ----------
    In this situation, the denominator of the ICF formula is zero,
    making the index mathematically undefined. Returning NaN is the
    correct and explicit behavior, allowing downstream logic to decide
    how to handle such cases.
    """
    icf = ICF()
    obs = {"rumination": 0, "panting": 0}

    assert math.isnan(icf.compute(obs))


def test_icf_negative_input():
    """
    Test rejection of physically impossible input values.

    Behavioral durations or proportions **cannot be negative**.
    Any negative input represents:
    - corrupted data,
    - preprocessing errors,
    - unit conversion issues.

    Given:
        rumination < 0

    Expected:
        ValueError is raised.

    This test ensures that:
    - the ICF enforces physical plausibility,
    - invalid data does not silently propagate into analyses.
    """
    icf = ICF()
    obs = {"rumination": -10, "panting": 5}

    with pytest.raises(ValueError):
        icf.compute(obs)

