"""
Psychrometric relationships and thermodynamic functions.

This module implements classical psychrometric relationships
used for constructing psychrometric charts and for educational
and scientific analysis of moist air.

All formulations assume:
- dry-bulb temperature in degrees Celsius (°C)
- pressure in Pascals (Pa)
- humidity ratios in kg_vapor / kg_dry_air

The implemented equations follow standard psychrometric theory
(e.g. ASHRAE Fundamentals) and are intended primarily for
diagram construction, analysis, and visualization rather than
high-precision HVAC engineering design.
"""

import numpy as np


class Psychrometrics:
    """
    Collection of psychrometric and thermodynamic relationships.

    This class groups static methods that compute properties of
    moist air assuming ideal-gas behavior for dry air and water vapor.

    All methods are vectorized through NumPy and accept scalars
    or arrays as inputs.

    Notes
    -----
    - Temperatures are expressed in °C unless otherwise stated.
    - Pressure is expressed in Pa.
    - Humidity ratio is expressed as kg_vapor / kg_dry_air.
    - Functions are designed for stability and clarity, not for
      sub-percent engineering accuracy.

    Constants
    ---------
    cp : float
        Specific heat of dry air at constant pressure (kJ kg⁻¹ °C⁻¹).
    Hfg : float
        Latent heat of vaporization of water (kJ kg⁻¹).
    Rd : float
        Gas constant for dry air (J kg⁻¹ K⁻¹).
    cp_v : float
        Specific heat of water vapor at constant pressure (kJ kg⁻¹ °C⁻¹).
    """

    # --- Thermodynamic constants ---
    cp   = 1.006       # kJ kg⁻¹ °C⁻¹ (dry air)
    Hfg  = 2501.0      # kJ kg⁻¹ (latent heat of vaporization)
    Rd   = 287.055     # J kg⁻¹ K⁻¹ (gas constant for dry air)
    cp_v = 1.86        # kJ kg⁻¹ °C⁻¹ (water vapor)

    # ------------------------------------------------------------------
    @staticmethod
    def saturation_pressure(T):
        """
        Saturation vapor pressure of water.

        Computes the saturation vapor pressure over liquid water
        using the Magnus–Tetens approximation.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature (°C).

        Returns
        -------
        p_sat : float or ndarray
            Saturation vapor pressure (Pa).

        Notes
        -----
        This formulation is valid for typical atmospheric
        temperatures encountered in psychrometric charts.
        """
        return 610.94 * np.exp((17.625 * T) / (T + 243.04))

    # ------------------------------------------------------------------
    @staticmethod
    def humidity_ratio(T, RH, P=101325.0):
        """
        Humidity ratio (mixing ratio) of moist air.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature (°C).
        RH : float or ndarray
            Relative humidity (0–1).
        P : float, optional
            Total air pressure (Pa). Default is 101325 Pa.

        Returns
        -------
        W : float or ndarray
            Humidity ratio (kg_vapor / kg_dry_air).
        """
        # Saturation vapor pressure
        p_sat = Psychrometrics.saturation_pressure(T)

        # Partial pressure of water vapor
        p_v = RH * p_sat

        # Standard psychrometric relationship
        return 0.622 * p_v / (P - p_v)

    # ------------------------------------------------------------------
    @staticmethod
    def enthalpy(T, W):
        """
        Specific enthalpy of moist air.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature (°C).
        W : float or ndarray
            Humidity ratio (kg_vapor / kg_dry_air).

        Returns
        -------
        h : float or ndarray
            Enthalpy of moist air (kJ kg_dry_air⁻¹).

        Notes
        -----
        The formulation follows:

        h = cp * T + W * (Hfg + cp_v * T)
        """
        return Psychrometrics.cp * T + W * (
            Psychrometrics.Hfg + Psychrometrics.cp_v * T
        )

    # ------------------------------------------------------------------
    @staticmethod
    def wet_bulb_line(T_db, T_wb, P=101325.0):
        """
        Constant wet-bulb temperature line.

        Computes the humidity ratio corresponding to a constant
        wet-bulb temperature along a range of dry-bulb temperatures.

        Parameters
        ----------
        T_db : ndarray
            Dry-bulb temperature array (°C).
        T_wb : float
            Wet-bulb temperature (°C).
        P : float, optional
            Total air pressure (Pa).

        Returns
        -------
        W_line : ndarray
            Humidity ratio along the wet-bulb line.
        """
        # Saturated humidity ratio at wet-bulb temperature
        W_sat_wb = Psychrometrics.humidity_ratio(T_wb, 1.0, P)

        # Linear approximation along the wet-bulb line
        return W_sat_wb - Psychrometrics.cp * (T_db - T_wb) / Psychrometrics.Hfg

    # ------------------------------------------------------------------
    @staticmethod
    def dew_point_temperature(RH, T, P=101325.0, tol=0.01, max_iter=100):
        """
        Dew-point temperature from dry-bulb temperature and RH.

        Solves the nonlinear equation:

        p_sat(T_dp) = RH * p_sat(T)

        using the Newton–Raphson iterative method.

        Parameters
        ----------
        RH : float or ndarray
            Relative humidity (0–1).
        T : float or ndarray
            Dry-bulb temperature (°C).
        P : float, optional
            Total air pressure (Pa).
        tol : float, optional
            Convergence tolerance in °C.
        max_iter : int, optional
            Maximum number of iterations.

        Returns
        -------
        T_dp : float or ndarray
            Dew-point temperature (°C).
        """
        # Actual vapor pressure
        p_v = RH * Psychrometrics.saturation_pressure(T)

        # Initial guess: dry-bulb temperature
        T_dp = np.array(T, dtype=float)

        for _ in range(max_iter):
            p_sat_dp = Psychrometrics.saturation_pressure(T_dp)

            # Residual
            f = p_sat_dp - p_v

            # Derivative dp_sat / dT
            dp_dT = p_sat_dp * 17.625 * 243.04 / (T_dp + 243.04) ** 2

            T_next = T_dp - f / dp_dT

            if np.allclose(T_next, T_dp, atol=tol):
                break

            T_dp = T_next

        return T_dp

    # ------------------------------------------------------------------
    @staticmethod
    def relative_humidity_from_W(T, W, P=101325.0):
        """
        Relative humidity from humidity ratio.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature (°C).
        W : float or ndarray
            Humidity ratio (kg_vapor / kg_dry_air).
        P : float, optional
            Total air pressure (Pa).

        Returns
        -------
        RH : float or ndarray
            Relative humidity (0–1).
        """
        p_v = W * P / (0.622 + W)
        return p_v / Psychrometrics.saturation_pressure(T)

    # ------------------------------------------------------------------
    @staticmethod
    def specific_humidity(W):
        """
        Specific humidity of moist air.

        Parameters
        ----------
        W : float or ndarray
            Humidity ratio (kg_vapor / kg_dry_air).

        Returns
        -------
        q : float or ndarray
            Specific humidity (kg_vapor / kg_moist_air).

        Notes
        -----
        q = W / (1 + W)
        """
        return W / (1.0 + W)

    # ------------------------------------------------------------------
    @staticmethod
    def specific_volume(T, W, P=101325.0):
        """
        Specific volume of moist air.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature (°C).
        W : float or ndarray
            Humidity ratio (kg_vapor / kg_dry_air).
        P : float, optional
            Total air pressure (Pa).

        Returns
        -------
        v : float or ndarray
            Specific volume (m³ kg_dry_air⁻¹).
        """
        T_K = T + 273.15
        return (Psychrometrics.Rd * T_K * (1 + 1.6078 * W)) / P

    # ------------------------------------------------------------------
    @staticmethod
    def density(T, W, P=101325.0):
        """
        Density of moist air.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature (°C).
        W : float or ndarray
            Humidity ratio (kg_vapor / kg_dry_air).
        P : float, optional
            Total air pressure (Pa).

        Returns
        -------
        rho : float or ndarray
            Air density (kg m⁻³).
        """
        return 1.0 / Psychrometrics.specific_volume(T, W, P)

    # ------------------------------------------------------------------
    @staticmethod
    def vapor_enthalpy(T):
        """
        Specific enthalpy of water vapor.

        Parameters
        ----------
        T : float or ndarray
            Temperature (°C).

        Returns
        -------
        h_v : float or ndarray
            Water vapor enthalpy (kJ kg⁻¹).

        Notes
        -----
        h_v = Hfg + cp_v * T
        """
        return Psychrometrics.Hfg + Psychrometrics.cp_v * T

    # ------------------------------------------------------------------
    @staticmethod
    def dew_point_line(T_db, RH, P=101325.0):
        """
        Dew-point temperature line for a constant relative humidity.

        Parameters
        ----------
        T_db : ndarray
            Dry-bulb temperature array (°C).
        RH : float
            Relative humidity (0–1).
        P : float, optional
            Total air pressure (Pa).

        Returns
        -------
        T_dp : ndarray
            Dew-point temperature array (°C).
        """
        return Psychrometrics.dew_point_temperature(RH, T_db, P)

