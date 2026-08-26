"""Tests for the Temperature-Humidity Index (ITU)."""

import numpy as np
import pytest

from psychchart.indexes.itu import ITU


def test_itu_matches_kelly_bond_azevedo_reference_formula():
    """Check exact values from the Kelly & Bond form used by Azevedo et al. (2005)."""
    assert ITU.compute({"T": 30.0, "RH": 0.60}) == pytest.approx(79.84, abs=1e-12)
    assert ITU.compute({"T": 30.0, "RH": 0.80}) == pytest.approx(82.92, abs=1e-12)


def test_vectorized_itu_matches_scalar_reference_values():
    values = ITU.compute_vectorized(
        {
            "T": np.array([30.0, 30.0]),
            "RH": np.array([0.60, 0.80]),
        }
    )
    assert values == pytest.approx(np.array([79.84, 82.92]), abs=1e-12)


def test_itu_increases_with_temperature():
    rh = 0.5
    v1 = ITU.compute({"T": 25.0, "RH": rh})
    v2 = ITU.compute({"T": 30.0, "RH": rh})
    assert v2 > v1


def test_itu_increases_with_humidity():
    temperature = 30.0
    v1 = ITU.compute({"T": temperature, "RH": 0.4})
    v2 = ITU.compute({"T": temperature, "RH": 0.7})
    assert v2 > v1


def test_itu_rejects_invalid_rh():
    with pytest.raises(ValueError):
        ITU.compute({"T": 30.0, "RH": 1.2})

    with pytest.raises(ValueError):
        ITU.compute_vectorized(
            {"T": np.array([30.0]), "RH": np.array([1.2])}
        )
