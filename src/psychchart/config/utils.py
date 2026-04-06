
"""
Configuration utilities for psychchart.

This module defines small utility helpers used by the configuration models of
the ``psychchart`` package.

Its functions support semantic normalization and lightweight validation tasks
that are shared across multiple configuration sections. The goal is to keep
these reusable helpers centralized, simple, and independent from both the
plotting layer and the higher-level configuration models that consume them.

The main purpose of this module is to provide low-level normalization utilities
that help maintain a consistent internal configuration representation.

Notes
-----
This module contains small shared helpers.

It is responsible for:
- normalizing configuration values reused across modules
- enforcing simple semantic constraints
- supporting cross-module consistency in the configuration layer

It is not responsible for:
- high-level model validation
- plotting
- psychrometric calculations beyond simple normalization rules
- runtime rendering behavior

See Also
--------
base
    Shared strict configuration base model.
isolines
    Isoline-family models that use normalization helpers.
points
    Point model that uses relative humidity normalization.
paths
    Path model that uses relative humidity normalization.
zones
    Zone models that normalize relative humidity intervals.

Examples
--------
Normalize fractional relative humidity:

>>> normalize_rh(0.65)
0.65

Normalize percentage relative humidity:

>>> normalize_rh(65)
0.65
"""


from __future__ import annotations

def normalize_rh(value: float) -> float:
    """
    Normalize a relative humidity value to the fractional domain ``[0, 1]``.

    This helper accepts relative humidity values expressed either as a
    fractional value (for example, ``0.65``) or as a percentage
    (for example, ``65``). If the input is greater than ``1.0``, it is
    interpreted as a percentage and converted by dividing by ``100``.

    The function validates the normalized result to ensure it lies in the
    physically meaningful interval for relative humidity.

    Parameters
    ----------
    value : float
        Relative humidity value to normalize.

        Accepted conventions are:

        - Fractional representation: ``0.0 <= value <= 1.0``
        - Percentage representation: ``0.0 <= value <= 100.0``

    Returns
    -------
    float
        Relative humidity expressed as a fraction in the interval ``[0, 1]``.

    Raises
    ------
    ValueError
        If the normalized value falls outside the valid interval ``[0, 1]``.
        This includes invalid negative values and values greater than ``100%``.

    Notes
    -----
    This function is intentionally small and strict because relative humidity
    is often provided in mixed conventions across scientific datasets,
    configuration files, user inputs, and plotting pipelines.

    The normalization rule is:

    - If ``value <= 1.0``, assume the input is already fractional.
    - If ``value > 1.0``, assume the input is given in percent and divide
      by ``100``.

    This behavior is convenient for scientific and engineering workflows,
    but it also means that values such as ``1.2`` are interpreted as
    ``1.2%`` rather than rejected as ambiguous input.

    See Also
    --------
    float
        Built-in Python numeric conversion used to coerce the input.
    round
        Useful when formatting normalized humidity values for display.

    Examples
    --------
    Fractional input is preserved:

    >>> normalize_rh(0.65)
    0.65

    Percentage input is converted to fraction:

    >>> normalize_rh(65)
    0.65

    Boundary values are accepted:

    >>> normalize_rh(0)
    0.0
    >>> normalize_rh(100)
    1.0

    Invalid values raise an exception:

    >>> normalize_rh(-5)
    Traceback (most recent call last):
        ...
    ValueError: Relative humidity out of range: -5.0
    """
    # Convert the input explicitly to float so the function behaves
    # consistently for integers, strings representing numbers, and other
    # numeric-like inputs accepted by Python's float constructor.
    value = float(value)

    # Scientific and operational datasets may encode RH either as fraction
    # (0.65) or percentage (65). The convention adopted here is simple:
    # any value greater than 1.0 is assumed to be in percent.
    if value > 1.0:
        value = value / 100.0

    # After normalization, RH must lie in the closed interval [0, 1].
    # Values outside this range are physically inconsistent for relative
    # humidity and therefore rejected early with a clear error message.
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"Relative humidity out of range: {value}")

    # Return the normalized fractional representation expected by the rest
    # of the psychrometric or scientific computation pipeline.
    return value
