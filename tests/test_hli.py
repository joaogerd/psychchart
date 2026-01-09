"""
Unit tests for the Heat Load Index (HLI).

These tests validate the expected physical behavior of the HLI
under controlled changes of its input variables.

Test philosophy
---------------
The Heat Load Index is an empirical bioclimatic index designed
to increase or decrease consistently with environmental drivers
of heat stress in cattle.

Therefore, the tests focus on monotonic relationships:

- HLI must increase with air temperature.
- HLI must decrease with wind speed (enhanced convective cooling).
- HLI must increase with solar radiation (radiant heat load).

This approach ensures robustness and long-term stability of the tests,
even if coefficients are slightly adjusted in future versions.
"""

from psychchart.indexes.hli import HLI


def test_hli_increases_with_temperature():
    """
    Test that HLI increases monotonically with air temperature.

    For fixed humidity, solar radiation, and wind speed, increasing
    air temperature must result in a higher HLI value, reflecting
    increased thermal load on the animal.
    """
    # Reference conditions
    v1 = HLI.compute(T=25.0, RH=0.5, SR=600.0, WS=2.0)
    v2 = HLI.compute(T=35.0, RH=0.5, SR=600.0, WS=2.0)

    # Higher temperature must yield higher HLI
    assert v2 > v1


def test_hli_decreases_with_wind():
    """
    Test that HLI decreases with increasing wind speed.

    Wind enhances convective heat loss in cattle. Therefore,
    for fixed temperature, humidity, and solar radiation,
    increasing wind speed must reduce the HLI value.
    """
    # Low wind speed
    v1 = HLI.compute(T=35.0, RH=0.6, SR=700.0, WS=1.0)

    # High wind speed
    v2 = HLI.compute(T=35.0, RH=0.6, SR=700.0, WS=4.0)

    # Stronger wind must reduce HLI
    assert v2 < v1


def test_hli_increases_with_radiation():
    """
    Test that HLI increases monotonically with solar radiation.

    Solar radiation contributes directly to radiant heat gain.
    For fixed temperature, humidity, and wind speed, higher
    incoming radiation must result in a higher HLI.
    """
    # Lower solar radiation
    v1 = HLI.compute(T=30.0, RH=0.5, SR=300.0, WS=2.0)

    # Higher solar radiation
    v2 = HLI.compute(T=30.0, RH=0.5, SR=800.0, WS=2.0)

    # Higher radiation must increase HLI
    assert v2 > v1

