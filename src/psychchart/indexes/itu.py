# src/psychchart/indexes/itu.py

from __future__ import annotations
from typing import Dict, Any
import numpy as np

from .base import BaseIndex


class ITU(BaseIndex):
    """
    Temperature-Humidity Index (ITU / THI).

    Overview
    --------
    The Temperature-Humidity Index (ITU) combines dry-bulb temperature and
    relative humidity into a dimensionless indicator of thermal challenge.

    Mathematical Definition
    ------------------------
    The formulation implemented here is the Kelly & Bond (1971) expression
    used by Azevedo et al. (2005):

        ITU = TF - 0.55 * (1 - RH) * (TF - 58)

    where:

        TF : dry-bulb temperature in degrees Fahrenheit
        RH : relative humidity as a fraction in [0, 1]

    With temperature supplied in degrees Celsius:

        TF = 1.8 * T + 32

    and therefore:

        ITU = (1.8*T + 32) - (0.55 - 0.0055*RH_percent) * (1.8*T - 26)

    Inputs
    ------
    - T must be provided in degrees Celsius (°C).
    - RH must be provided as a fraction in the interval [0, 1].

    The ITU is dimensionless.

    Scientific Background
    ---------------------
    In Azevedo et al. (2005), this formulation was used to estimate upper
    critical ITU values for lactating 1/2, 3/4 and 7/8 Holstein-Zebu cows.
    Based on respiratory rate, the reported upper critical values were 79,
    77 and 76, respectively.

    Examples
    --------
    >>> ctx = {"T": 30.0, "RH": 0.60}
    >>> round(ITU.compute(ctx), 2)
    79.84

    >>> ctx = {"T": 30.0, "RH": 0.80}
    >>> round(ITU.compute(ctx), 2)
    82.92

    Notes
    -----
    - This implementation is deterministic and stateless.
    - RH is validated in both scalar and vectorized execution paths.
    - No clipping of ITU values is applied.
    """

    name = "ITU"
    required_fields = {"T", "RH"}

    @staticmethod
    def compute(context: Dict[str, Any]) -> float:
        """Compute ITU from temperature in °C and relative humidity fraction."""
        T = float(context["T"])
        RH = float(context["RH"])

        if np.any((RH < 0.0) | (RH > 1.0)):
            raise ValueError(
                "Relative humidity (RH) must be given as a fraction "
                "between 0 and 1."
            )

        tf = 1.8 * T + 32.0
        itu = tf - 0.55 * (1.0 - RH) * (tf - 58.0)
        return itu

    @staticmethod
    def compute_vectorized(context: Dict[str, np.ndarray]) -> np.ndarray:
        """Vectorized ITU over arrays of temperature and relative humidity."""
        T = np.asarray(context["T"], dtype=float)
        RH = np.asarray(context["RH"], dtype=float)

        if np.any((RH < 0.0) | (RH > 1.0)):
            raise ValueError(
                "Relative humidity (RH) must be given as a fraction "
                "between 0 and 1."
            )

        tf = 1.8 * T + 32.0
        return tf - 0.55 * (1.0 - RH) * (tf - 58.0)
