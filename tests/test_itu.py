"""
Unit tests for the Temperature-Humidity Index (ITU).

These tests verify basic physical and empirical properties of the ITU,
rather than exact numerical values. This approach is recommended for
empirical thermal comfort indexes, whose formulations are often
approximate and subject to small variations across references.

Test philosophy
---------------
The tests below focus on *monotonic behavior*, ensuring that:

- ITU increases with increasing air temperature, all else being equal.
- ITU increases with increasing relative humidity, all else being equal.

Such properties are fundamental to the physical interpretation of
thermal comfort and heat stress.
"""

from psychchart.indexes.iti import ITU


def test_itu_increases_with_temperature():
    """
    Test that ITU increases monotonically with air temperature.

    For a fixed relative humidity, an increase in dry-bulb temperature
    must lead to a higher ITU value, reflecting increased thermal stress.

    This test does not validate absolute values, but rather checks
    the physical consistency of the index behavior.
    """
    # Fixed relative humidity (50%)
    rh = 0.5

    # Two temperatures, second higher than the first
    v1 = ITU.compute(T=25.0, RH=rh)
    v2 = ITU.compute(T=30.0, RH=rh)

    # Higher temperature must result in higher ITU
    assert v2 > v1


def test_itu_increases_with_humidity():
    """
    Test that ITU increases monotonically with relative humidity.

    For a fixed air temperature, an increase in relative humidity
    reduces evaporative cooling efficiency, which must be reflected
    as a higher ITU value.

    This test ensures the empirical formulation responds correctly
    to humidity changes.
    """
    # Fixed air temperature (30 °C)
    temperature = 30.0

    # Two humidity levels, second higher than the first
    v1 = ITU.compute(T=temperature, RH=0.4)
    v2 = ITU.compute(T=temperature, RH=0.7)

    # Higher humidity must result in higher ITU
    assert v2 > v1

