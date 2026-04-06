# src/psychchart/indexes/itu.py

from __future__ import annotations
from typing import Dict, Any
import numpy as np

from .base import BaseIndex


class ITU(BaseIndex):
    """
    Temperature–Humidity Index (ITU / THI).

    Overview
    --------
    The Temperature–Humidity Index (ITU) is a classical thermal
    comfort index widely used in animal science, biometeorology,
    and environmental physiology.

    It combines air temperature and relative humidity into a single
    scalar metric representing heat stress conditions.

    Mathematical Definition
    ------------------------
    The formulation implemented here is:

        ITU = (1.8T + 32) - (0.55 - 0.0055 RH) (1.8T - 26.8)

    where:

        T   : Air temperature in °C
        RH  : Relative humidity in %

    Units
    -----
    - T must be provided in degrees Celsius (°C)
    - RH must be provided as a fraction in the range [0, 1]

    RH is internally converted from fraction to percentage before applying
    the formula.

    The index has units equivalent to °C.

    Context Requirements
    --------------------
    Required context keys:

        {"T", "RH"}


    Scientific Background
    ---------------------
    The ITU (often referred to as THI in international literature)
    is historically derived from human comfort studies and later
    adapted for livestock applications.

    It is most commonly applied to:

    - Dairy cattle heat stress evaluation
    - Feedlot monitoring
    - Thermal environment classification

    References
    ----------
    Thom (1959)
    NOAA heat stress formulations
    Biometeorological livestock adaptations literature

    Examples
    --------
    Basic usage:

    >>> ctx = {"T": 30.0, "RH": 0.60}
    >>> ITU.compute(ctx)
    27.43

    Higher humidity:

    >>> ctx = {"T": 30.0, "RH": 0.80}
    >>> ITU.compute(ctx)
    28.73

    Notes
    -----
    - This implementation is deterministic and stateless.
    - No clipping is applied to inputs.
    - Minimal validation is performed:
      - RH must be in [0, 1]
    - The resulting value is returned as a scalar or NumPy array depending
      on the execution mode.
    """

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    name = "ITU"
    required_fields = {"T", "RH"}

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    @staticmethod
    def compute(context: Dict[str, Any]) -> float:
        """
        Compute ITU from temperature and relative humidity.

        Parameters
        ----------
        context : dict
            Dictionary containing:
                - "T"  : temperature in °C
                - "RH" : relative humidity in fraction

        Returns
        -------
        float
            Computed ITU value.

        Raises
        ------
        KeyError
            If required fields are missing.
        TypeError
            If inputs are not numeric.
        """

        # --------------------------------------------------------------
        # Extract required inputs
        # --------------------------------------------------------------
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

        # --------------------------------------------------------------
        # ITU formula
        # --------------------------------------------------------------
        itu = (1.8 * T + 32.0) - (0.55 - 0.0055 * rh_percent) * (1.8 * T - 26.8)
        return itu
    
    @staticmethod
    def compute_vectorized(context: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Vectorized ITU over arrays.

        Parameters
        ----------
        context : dict[str, ndarray]
            Must contain 2D arrays "T" and "RH".

        Returns
        -------
        ndarray
            2D ITU field.
        """
        T = np.asarray(context["T"], dtype=float)
        RH = np.asarray(context["RH"], dtype=float)
        rh_percent = RH * 100.0
        itu = (1.8 * T + 32.0) - (0.55 - 0.0055 * rh_percent) * (1.8 * T - 26.8)

        return itu
