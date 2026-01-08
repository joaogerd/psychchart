"""
Temperature-Humidity Index (ITU / THI).

This module implements the Temperature-Humidity Index (ITU),
also known internationally as the Temperature-Humidity Index (THI).

The ITU is one of the most widely used empirical indexes for
assessing thermal comfort and heat stress, especially in
livestock (cattle, dairy cows, beef cattle) and, historically,
in human biometeorology.

Scientific background
---------------------
The ITU combines air temperature and relative humidity to
approximate the reduction in evaporative heat loss under
humid conditions.

Typical formulation (Thom, 1959; adapted forms widely used):

    ITU = T - (0.55 - 0.0055 * RH_percent) * (T - 14.5)

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

from .base import ComfortIndex


class ITU(ComfortIndex):
    """
    Temperature-Humidity Index (ITU).

    This class implements the ITU as a scalar thermal comfort
    or heat-stress diagnostic derived from air temperature and
    relative humidity.

    Attributes
    ----------
    name : str
        Short name identifier of the index ("ITU").

    Notes
    -----
    - This implementation follows the classic Thom-type formulation,
      commonly used in livestock heat stress studies.
    - Relative humidity is provided as a fraction (0–1) at the API
      level for consistency with modern scientific software, but
      internally converted to percentage.
    """

    #: Human-readable identifier for the index
    name = "ITU"

    @staticmethod
    def compute(T: float, RH: float) -> float:
        """
        Compute the Temperature-Humidity Index (ITU).

        Parameters
        ----------
        T : float
            Dry-bulb air temperature in degrees Celsius (°C).

        RH : float
            Relative humidity as a fraction (0–1).

        Returns
        -------
        itu : float
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

            from psychchart.indexes import ITU

            itu = ITU.compute(T=30.0, RH=0.60)
            print(f"ITU = {itu:.2f}")

        Typical interpretation in livestock studies::

            ITU < 72   : thermal comfort
            72–78      : mild heat stress
            78–84      : moderate heat stress
            > 84       : severe heat stress

        Example in a loop over observations::

            temperatures = [28.0, 30.0, 32.0]
            humidities   = [0.50, 0.60, 0.70]

            for T, RH in zip(temperatures, humidities):
                itu = ITU.compute(T=T, RH=RH)
                print(T, RH, itu)
        """
        # ------------------------------------------------------------------
        # Input validation
        # ------------------------------------------------------------------
        if not (0.0 <= RH <= 1.0):
            raise ValueError(
                "Relative humidity (RH) must be given as a fraction "
                "between 0 and 1."
            )

        # ------------------------------------------------------------------
        # Convert relative humidity from fraction to percentage
        # (required by the classical ITU formulation)
        # ------------------------------------------------------------------
        rh_percent = RH * 100.0

        # ------------------------------------------------------------------
        # ITU empirical formulation
        # ------------------------------------------------------------------
        itu = T - (0.55 - 0.0055 * rh_percent) * (T - 14.5)

        return itu

