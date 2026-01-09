"""
Heat Load Index (HLI).

This module implements a simplified version of the Heat Load Index (HLI),
originally proposed by Gaughan et al. (2008), widely used to assess heat
stress in cattle under field conditions.

Scientific background
---------------------
The Heat Load Index was developed to better represent the combined effects
of:
- air temperature,
- humidity,
- solar radiation,
- wind speed,

on the thermal load experienced by cattle.

Unlike simpler indexes (e.g., ITU/THI), the HLI explicitly accounts for:
- solar radiation (radiant heat load),
- wind speed (convective cooling).

This makes HLI particularly suitable for:
- outdoor grazing systems,
- feedlots,
- tropical and subtropical environments.

Important note
--------------
The original formulation of HLI includes different regimes depending on
black globe temperature and other conditional terms. This implementation
represents a **simplified and linearized form**, intended primarily for:
- educational purposes,
- comparative studies,
- sensitivity analysis.

It should not be used for operational decision-making without validation
against the full original formulation.
"""

from .base import ComfortIndex


class HLI(ComfortIndex):
    """
    Heat Load Index (HLI).

    This class implements a simplified Heat Load Index as a scalar
    bioclimatic indicator of heat stress in cattle.

    Attributes
    ----------
    name : str
        Short identifier of the index ("HLI").

    Notes
    -----
    - Relative humidity is provided as a fraction (0–1) and internally
      converted to percentage.
    - Solar radiation is assumed to be global horizontal irradiance.
    - Wind speed represents near-animal or near-surface ventilation.
    """

    #: Human-readable identifier for the index
    name = "HLI"

    @staticmethod
    def compute(T: float, RH: float, SR: float, WS: float) -> float:
        """
        Compute the Heat Load Index (HLI).

        Parameters
        ----------
        T : float
            Air temperature in degrees Celsius (°C).

        RH : float
            Relative humidity as a fraction (0–1).

        SR : float
            Incoming solar radiation in watts per square meter (W m⁻²).

        WS : float
            Wind speed in meters per second (m s⁻¹).

        Returns
        -------
        hli : float
            Heat Load Index value (dimensionless).

        Raises
        ------
        ValueError
            If relative humidity is outside the physical range [0, 1].
        ValueError
            If wind speed or solar radiation is negative.

        Notes
        -----
        This simplified formulation follows the general empirical structure
        proposed by Gaughan et al. (2008):

        - HLI increases with:
            * air temperature,
            * relative humidity,
            * solar radiation.
        - HLI decreases with:
            * wind speed (enhanced convective cooling).

        The formulation used here is:

        ::

            HLI = 8.62
                  + 0.38 * RH_percent
                  + 1.55 * T
                  - 0.50 * WS
                  + 0.02 * SR

        where RH_percent = RH × 100.
        """

        # ------------------------------------------------------------------
        # Input validation
        # ------------------------------------------------------------------
        if not (0.0 <= RH <= 1.0):
            raise ValueError(
                "Relative humidity (RH) must be given as a fraction "
                "between 0 and 1."
            )

        if WS < 0.0:
            raise ValueError("Wind speed (WS) must be non-negative.")

        if SR < 0.0:
            raise ValueError("Solar radiation (SR) must be non-negative.")

        # ------------------------------------------------------------------
        # Convert relative humidity from fraction to percentage
        # ------------------------------------------------------------------
        rh_percent = RH * 100.0

        # ------------------------------------------------------------------
        # Simplified Heat Load Index formulation
        # ------------------------------------------------------------------
        hli = (
            8.62
            + 0.38 * rh_percent
            + 1.55 * T
            - 0.5 * WS
            + 0.02 * SR
        )

        return hli

