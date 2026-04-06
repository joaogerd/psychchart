"""
Temperature-Humidity Index (ITI / THI).

This module implements the Temperature-Humidity Index (ITI),
lso known internationally as the Temperature-Humidity Index (THI).

The ITI is one of the most widely used empirical indexes for
assessing thermal comfort and heat stress, especially in
livestock (cattle, dairy cows, beef cattle) and, historically,
in human biometeorology.

Scientific background
---------------------
The ITI combines air temperature and relative humidity to
approximate the reduction in evaporative heat loss under
humid conditions.

Typical formulation (Thom, 1959; adapted forms widely used):

    ITI = 0.8 * T + rh_percent * (T - 14.3)/100 + 46.3

Where:
- T           : dry-bulb air temperature [°C]
- RH_percent : relative humidity [%]

This formulation assumes:
- moderate wind conditions,
- shaded environment (no explicit solar radiation term),
- steady-state conditions.

Limitations
-----------
- Does not account explicitly for wind speed or solar radiation.
- Accuracy decreases under extreme radiation or ventilation.
- Best interpreted as a *screening index*, not a full heat balance.
"""
from __future__ import annotations
from typing import Dict, Any

import numpy as np
from .base import BaseIndex


class ITI(BaseIndex):
    """
    Temperature-Humidity Index (ITI).

    This class implements the ITI as a scalar thermal comfort
    or heat-stress diagnostic derived from air temperature and
    relative humidity.

    Attributes
    ----------
    name : str
        Short name identifier of the index ("ITI").

    Notes
    -----
    - This implementation follows the classic Thom-type formulation,
      commonly used in livestock heat stress studies.
    - Relative humidity is provided as a fraction (0–1) at the API
      level for consistency with modern scientific software, but
      internally converted to percentage.
    """

    #: Human-readable identifier for the index
    name = "ITI"
    required_fields = {"T", "RH"}

    @staticmethod
    def compute_vectorized(context: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute the Temperature-Humidity Index (ITI).

        Parameters
        ----------
        context : dict
            Must contain:
        
                - T : float
                      Dry-bulb air temperature in degrees Celsius (°C).
        
                - RH : float
                       Relative humidity as a fraction (0–1).

        Returns
        -------
        ITI : float
            Computed Temperature-Humidity Index value (dimensionless).

        Raises
        ------
        ValueError
            If relative humidity is outside the physical range [0, 1].

        Notes
        -----
        - Internally, relative humidity is converted to percentage
          following the original empirical formulation.
        - This function performs a deterministic, side-effect-free
          calculation.

        Examples
        --------
        Basic usage with scalar inputs::

            from psychchart.indexes import ITI

            ITI = ITI.compute(T=30.0, RH=0.60)
            print(f"ITI = {ITI:.2f}")

        Typical interpretation in livestock studies::

            ITI < 72   : thermal comfort
            72–78      : mild heat stress
            78–84      : moderate heat stress
            > 84       : severe heat stress

        Example in a loop over observations::

            temperatures = [28.0, 30.0, 32.0]
            humidities   = [0.50, 0.60, 0.70]

            for T, RH in zip(temperatures, humidities):
                ITI = ITI.compute(T=T, RH=RH)
                print(T, RH, ITI)
        """
        # ------------------------------------------------------------------
        # Input validation
        # ------------------------------------------------------------------
        # Accept both scalars and arrays
        T = float(context["T"])
        RH = float(context["RH"])

        if np.any((RH < 0.0) | (RH > 1.0)):
            raise ValueError(
                "Relative humidity (RH) must be given as a fraction "
                "between 0 and 1."
            )

        # ------------------------------------------------------------------
        # Convert relative humidity from fraction to percentage
        # (required by the classical ITI formulation)
        # ------------------------------------------------------------------
        rh_percent = RH * 100.0

        # ------------------------------------------------------------------
        # ITI empirical formulation
        # ------------------------------------------------------------------
        ITI = 0.8 * T + rh_percent * (T - 14.3)/100 + 46.3
        return ITI

    @staticmethod
    def compute_vectorized(context: Dict[str, np.ndarray]) -> np.ndarray:
        T = np.asarray(context["T"], dtype=float)
        RH = np.asarray(context["RH"], dtype=float)

        rh_percent = RH * 100.0
        return 0.8 * T + rh_percent * (T - 14.3) / 100 + 46.3
