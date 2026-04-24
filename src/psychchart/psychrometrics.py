"""
Olá irei proceder com a documentacao completa: com docstrings numpy em ingles, com vários comentários e exemplos de uso
"""

from __future__ import annotations

import numpy as np


class PsychrometricError(ValueError):
    """
    Exception raised when psychrometric inputs are physically invalid.

    This exception is used to signal invalid thermodynamic states such as
    negative pressures, relative humidity outside the interval [0, 1], or
    water vapor partial pressure exceeding the total air pressure.

    Notes
    -----
    Using a dedicated exception type makes it easier for callers to distinguish
    psychrometric validation failures from generic ``ValueError`` conditions.

    Examples
    --------
    >>> raise PsychrometricError("Pressure must be greater than zero.")
    Traceback (most recent call last):
    ...
    PsychrometricError: Pressure must be greater than zero.
    """


class Psychrometrics:
    """
    Vectorized psychrometric and thermodynamic utility class.

    This class provides common psychrometric relationships for moist air using
    a NumPy-friendly API suitable for scientific computing, plotting, gridded
    analysis, and chart generation. The implementation is designed to preserve
    compatibility with an existing public interface while improving internal
    numerical robustness and physical validation.

    The methods accept either scalars or array-like values and return NumPy
    arrays or Python floats depending on the input shape. This behavior makes
    the class convenient for both single-point thermodynamic calculations and
    bulk processing of environmental datasets.

    Parameters
    ----------
    None
        This class is intended to be used through static methods and does not
        require instantiation.

    Notes
    -----
    Main conventions adopted by this module:

    - Dry-bulb temperature is expressed in degrees Celsius (°C).
    - Pressure is expressed in pascals (Pa).
    - Relative humidity is expressed as a fraction in the interval [0, 1].
    - Humidity ratio ``W`` is expressed in kg_vapor / kg_dry_air.
    - Specific humidity ``q`` is expressed in kg_vapor / kg_moist_air.
    - Enthalpy is expressed in kJ / kg_dry_air.

    The saturation vapor pressure formulation is based on ASHRAE-style
    piecewise logarithmic equations over ice and liquid water, which are more
    robust than simpler empirical expressions in broader temperature ranges.

    See Also
    --------
    saturation_pressure : Saturation vapor pressure of water.
    humidity_ratio : Humidity ratio from dry-bulb temperature and RH.
    enthalpy : Moist-air enthalpy.
    specific_volume : Specific volume per unit mass of dry air.
    moist_air_density : Physical moist-air density.

    Examples
    --------
    >>> T = np.array([25.0, 30.0])
    >>> RH = np.array([0.50, 0.70])
    >>> W = Psychrometrics.humidity_ratio(T, RH)
    >>> W.shape
    (2,)

    >>> round(Psychrometrics.saturation_pressure(25.0), 2)
    3169.22

    >>> round(Psychrometrics.enthalpy(30.0, 0.018), 2)
    76.2
    """

    # -------------------------------------------------------------------------
    # Thermodynamic constants
    # -------------------------------------------------------------------------
    # Specific heat of dry air at constant pressure [kJ kg^-1 °C^-1]
    cp = 1.006

    # Latent heat of vaporization at 0 °C [kJ kg^-1]
    Hfg = 2501.0

    # Gas constant for dry air [J kg^-1 K^-1]
    Rd = 287.042

    # Specific heat of water vapor [kJ kg^-1 °C^-1]
    cp_v = 1.86

    # Ratio of molecular weights Mw / Md used in psychrometric relationships
    EPSILON = 0.621945

    # Lower bound to avoid exactly zero humidity ratio in some downstream uses
    MIN_HUMIDITY_RATIO = 1e-7

    # Celsius to Kelvin offset
    ZERO_CELSIUS_AS_KELVIN = 273.15

    # Triple point of water in degrees Celsius
    TRIPLE_POINT_WATER_C = 0.01

    @staticmethod
    def _asarray(value):
        """
        Convert input to a NumPy array of type float.

        Parameters
        ----------
        value : Any
            Scalar, list, tuple, or array-like object convertible to a
            floating-point NumPy array.

        Returns
        -------
        ndarray
            Float NumPy array representation of the input.

        Notes
        -----
        This helper is used to normalize scalar and array-like inputs into a
        common internal representation for vectorized numerical operations.

        Examples
        --------
        >>> Psychrometrics._asarray([1, 2, 3]).dtype == float
        True
        """
        return np.asarray(value, dtype=float)

    @staticmethod
    def _return_scalar_if_scalar(original, value):
        """
        Return a Python float when the original input was scalar.

        Parameters
        ----------
        original : Any
            Original input value used to infer whether the caller passed a
            scalar or an array-like object.
        value : float or ndarray
            Computed result to be returned.

        Returns
        -------
        float or ndarray
            Python float if ``original`` was scalar, otherwise the original
            array-like result.

        Notes
        -----
        This helper preserves a convenient API behavior:
        scalar input yields scalar output, while array input yields array output.

        Examples
        --------
        >>> Psychrometrics._return_scalar_if_scalar(3.0, np.array(5.0))
        5.0
        >>> Psychrometrics._return_scalar_if_scalar([3.0], np.array([5.0]))
        array([5.])
        """
        if np.isscalar(original):
            return float(np.asarray(value))
        return value

    @staticmethod
    def _broadcast(*values):
        """
        Broadcast multiple inputs to a common NumPy shape.

        Parameters
        ----------
        *values : Any
            One or more scalar or array-like inputs.

        Returns
        -------
        list of ndarray
            Broadcasted float arrays with a shared shape.

        Notes
        -----
        Broadcasting enables the methods in this class to combine scalar and
        vector inputs naturally, following standard NumPy semantics.

        Examples
        --------
        >>> a, b = Psychrometrics._broadcast([1, 2], 3)
        >>> a.shape == b.shape
        True
        """
        arrays = [np.asarray(v, dtype=float) for v in values]
        return np.broadcast_arrays(*arrays)

    @staticmethod
    def _require_positive_pressure(P):
        """
        Validate that pressure values are strictly positive.

        Parameters
        ----------
        P : float or ndarray
            Pressure value(s) in pascals.

        Raises
        ------
        PsychrometricError
            If any pressure value is less than or equal to zero.

        Examples
        --------
        >>> Psychrometrics._require_positive_pressure(101325.0)
        >>> Psychrometrics._require_positive_pressure(0.0)
        Traceback (most recent call last):
        ...
        PsychrometricError: Pressure must be greater than zero.
        """
        if np.any(np.asarray(P) <= 0.0):
            raise PsychrometricError("Pressure must be greater than zero.")

    @staticmethod
    def _require_rh(RH):
        """
        Validate that relative humidity lies in the interval [0, 1].

        Parameters
        ----------
        RH : float or ndarray
            Relative humidity as a fraction.

        Raises
        ------
        PsychrometricError
            If any relative humidity value is outside [0, 1].

        Examples
        --------
        >>> Psychrometrics._require_rh(0.65)
        >>> Psychrometrics._require_rh(1.2)
        Traceback (most recent call last):
        ...
        PsychrometricError: Relative humidity must be in the interval [0, 1].
        """
        RH_arr = np.asarray(RH, dtype=float)
        if np.any((RH_arr < 0.0) | (RH_arr > 1.0)):
            raise PsychrometricError(
                "Relative humidity must be in the interval [0, 1]."
            )

    @staticmethod
    def _require_non_negative_W(W):
        """
        Validate that humidity ratio values are non-negative.

        Parameters
        ----------
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.

        Raises
        ------
        PsychrometricError
            If any humidity ratio is negative.

        Examples
        --------
        >>> Psychrometrics._require_non_negative_W(0.01)
        >>> Psychrometrics._require_non_negative_W(-0.01)
        Traceback (most recent call last):
        ...
        PsychrometricError: Humidity ratio must be non-negative.
        """
        if np.any(np.asarray(W, dtype=float) < 0.0):
            raise PsychrometricError("Humidity ratio must be non-negative.")

    @staticmethod
    def _require_non_negative_q(q):
        """
        Validate that specific humidity lies in the interval [0, 1).

        Parameters
        ----------
        q : float or ndarray
            Specific humidity in kg_vapor / kg_moist_air.

        Raises
        ------
        PsychrometricError
            If any value is negative or greater than or equal to one.

        Examples
        --------
        >>> Psychrometrics._require_non_negative_q(0.01)
        >>> Psychrometrics._require_non_negative_q(1.0)
        Traceback (most recent call last):
        ...
        PsychrometricError: Specific humidity must be in the interval [0, 1).
        """
        q_arr = np.asarray(q, dtype=float)
        if np.any((q_arr < 0.0) | (q_arr >= 1.0)):
            raise PsychrometricError(
                "Specific humidity must be in the interval [0, 1)."
            )

    @staticmethod
    def saturation_pressure(T):
        """
        Compute saturation vapor pressure of water.

        This method uses a piecewise logarithmic expression consistent with
        ASHRAE-style psychrometric formulations. The ice formulation is used
        below the triple point of water, and the liquid-water formulation is
        used above it.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.

        Returns
        -------
        float or ndarray
            Saturation vapor pressure in pascals.

        Raises
        ------
        PsychrometricError
            If the converted temperature in Kelvin is not physically valid.

        Notes
        -----
        Internally, temperature is converted to Kelvin and then used in the
        logarithmic polynomial forms for ``ln(p_ws)``. This approach is more
        numerically stable and physically defensible over broad temperature
        intervals than simplified Magnus-type formulas.

        See Also
        --------
        vapor_pressure_from_rh : Vapor pressure from temperature and RH.
        saturation_humidity_ratio : Saturation humidity ratio from temperature.

        Examples
        --------
        >>> round(Psychrometrics.saturation_pressure(25.0), 2)
        3169.22
        >>> T = np.array([0.0, 10.0, 20.0])
        >>> Psychrometrics.saturation_pressure(T).shape
        (3,)
        """
        T_arr = Psychrometrics._asarray(T)
        T_k = T_arr + Psychrometrics.ZERO_CELSIUS_AS_KELVIN

        # Kelvin temperature must remain strictly positive for the logarithmic
        # and inverse-temperature terms to be physically meaningful.
        if np.any(T_k <= 0.0):
            raise PsychrometricError("Temperature in Kelvin must be greater than zero.")

        # Decide whether to use the ice or liquid-water saturation curve.
        below = T_arr <= Psychrometrics.TRIPLE_POINT_WATER_C

        # Logarithmic saturation pressure over ice.
        ln_pws_ice = (
            -5.6745359e3 / T_k
            + 6.3925247
            - 9.677843e-3 * T_k
            + 6.2215701e-7 * T_k**2
            + 2.0747825e-9 * T_k**3
            - 9.484024e-13 * T_k**4
            + 4.1635019 * np.log(T_k)
        )

        # Logarithmic saturation pressure over liquid water.
        ln_pws_liquid = (
            -5.8002206e3 / T_k
            + 1.3914993
            - 4.8640239e-2 * T_k
            + 4.1764768e-5 * T_k**2
            - 1.4452093e-8 * T_k**3
            + 6.5459673 * np.log(T_k)
        )

        p_sat = np.exp(np.where(below, ln_pws_ice, ln_pws_liquid))
        return Psychrometrics._return_scalar_if_scalar(T, p_sat)

    @staticmethod
    def vapor_pressure_from_rh(T, RH):
        """
        Compute partial vapor pressure from dry-bulb temperature and RH.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        RH : float or ndarray
            Relative humidity as a fraction in the interval [0, 1].

        Returns
        -------
        float or ndarray
            Water vapor partial pressure in pascals.

        Raises
        ------
        PsychrometricError
            If relative humidity is outside the interval [0, 1].

        Notes
        -----
        The relationship is:

        ``p_v = RH * p_sat(T)``

        where ``p_sat(T)`` is the saturation vapor pressure at dry-bulb
        temperature ``T``.

        Examples
        --------
        >>> round(Psychrometrics.vapor_pressure_from_rh(30.0, 0.60), 2)
        2547.08
        >>> T = np.array([20.0, 25.0])
        >>> RH = np.array([0.50, 0.80])
        >>> Psychrometrics.vapor_pressure_from_rh(T, RH).shape
        (2,)
        """
        Psychrometrics._require_rh(RH)
        T_arr, RH_arr = Psychrometrics._broadcast(T, RH)
        p_v = RH_arr * Psychrometrics.saturation_pressure(T_arr)
        scalar_ref = T if np.isscalar(T) and np.isscalar(RH) else T_arr
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, p_v)

    @staticmethod
    def humidity_ratio(T, RH, P=101325.0):
        """
        Compute humidity ratio from dry-bulb temperature, RH, and pressure.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        RH : float or ndarray
            Relative humidity as a fraction in the interval [0, 1].
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.

        Raises
        ------
        PsychrometricError
            If pressure is not strictly positive.
        PsychrometricError
            If relative humidity is outside [0, 1].
        PsychrometricError
            If the resulting vapor pressure equals or exceeds total pressure.

        Notes
        -----
        The psychrometric relationship used is:

        ``W = epsilon * p_v / (P - p_v)``

        where ``epsilon = Mw / Md`` is the molecular weight ratio of water
        vapor to dry air.

        A minimum humidity ratio threshold is enforced to avoid exactly zero
        values in downstream workflows that may be numerically sensitive.

        See Also
        --------
        humidity_ratio_from_vapor_pressure : Compute humidity ratio directly
            from vapor pressure.
        specific_humidity : Convert humidity ratio to specific humidity.

        Examples
        --------
        >>> round(Psychrometrics.humidity_ratio(30.0, 0.60), 6)
        0.015969
        >>> T = np.array([25.0, 30.0])
        >>> RH = np.array([0.50, 0.70])
        >>> Psychrometrics.humidity_ratio(T, RH).shape
        (2,)
        """
        Psychrometrics._require_positive_pressure(P)
        Psychrometrics._require_rh(RH)

        T_arr, RH_arr, P_arr = Psychrometrics._broadcast(T, RH, P)
        p_sat = Psychrometrics.saturation_pressure(T_arr)
        p_v = RH_arr * p_sat

        # Vapor pressure cannot physically exceed or equal total pressure.
        if np.any(p_v >= P_arr):
            raise PsychrometricError(
                "Partial vapor pressure must remain lower than total pressure."
            )

        W = Psychrometrics.EPSILON * p_v / (P_arr - p_v)
        W = np.maximum(W, Psychrometrics.MIN_HUMIDITY_RATIO)

        scalar_ref = (
            T if np.isscalar(T) and np.isscalar(RH) and np.isscalar(P) else T_arr
        )
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, W)

    @staticmethod
    def humidity_ratio_from_vapor_pressure(p_v, P=101325.0):
        """
        Compute humidity ratio from water vapor partial pressure.

        Parameters
        ----------
        p_v : float or ndarray
            Water vapor partial pressure in pascals.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.

        Raises
        ------
        PsychrometricError
            If total pressure is not strictly positive.
        PsychrometricError
            If vapor pressure is negative.
        PsychrometricError
            If vapor pressure equals or exceeds total pressure.

        Examples
        --------
        >>> round(Psychrometrics.humidity_ratio_from_vapor_pressure(2000.0), 6)
        0.012518
        """
        Psychrometrics._require_positive_pressure(P)
        p_v_arr, P_arr = Psychrometrics._broadcast(p_v, P)

        if np.any(p_v_arr < 0.0):
            raise PsychrometricError("Partial vapor pressure must be non-negative.")
        if np.any(p_v_arr >= P_arr):
            raise PsychrometricError(
                "Partial vapor pressure must remain lower than total pressure."
            )

        W = Psychrometrics.EPSILON * p_v_arr / (P_arr - p_v_arr)
        W = np.maximum(W, Psychrometrics.MIN_HUMIDITY_RATIO)
        return Psychrometrics._return_scalar_if_scalar(p_v, W)

    @staticmethod
    def vapor_pressure_from_W(W, P=101325.0):
        """
        Compute water vapor partial pressure from humidity ratio.

        Parameters
        ----------
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Water vapor partial pressure in pascals.

        Raises
        ------
        PsychrometricError
            If pressure is not strictly positive.
        PsychrometricError
            If humidity ratio is negative.

        Notes
        -----
        The inversion used is:

        ``p_v = P * W / (epsilon + W)``

        Examples
        --------
        >>> round(Psychrometrics.vapor_pressure_from_W(0.01), 2)
        1603.96
        """
        Psychrometrics._require_positive_pressure(P)
        Psychrometrics._require_non_negative_W(W)

        W_arr, P_arr = Psychrometrics._broadcast(W, P)
        W_arr = np.maximum(W_arr, Psychrometrics.MIN_HUMIDITY_RATIO)
        p_v = P_arr * W_arr / (Psychrometrics.EPSILON + W_arr)
        return Psychrometrics._return_scalar_if_scalar(W, p_v)

    @staticmethod
    def saturation_humidity_ratio(T, P=101325.0):
        """
        Compute saturation humidity ratio at dry-bulb temperature.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Saturation humidity ratio in kg_vapor / kg_dry_air.

        Raises
        ------
        PsychrometricError
            If pressure is not strictly positive.
        PsychrometricError
            If saturation pressure equals or exceeds total pressure.

        Examples
        --------
        >>> round(Psychrometrics.saturation_humidity_ratio(25.0), 6)
        0.020081
        """
        Psychrometrics._require_positive_pressure(P)

        T_arr, P_arr = Psychrometrics._broadcast(T, P)
        p_sat = Psychrometrics.saturation_pressure(T_arr)

        if np.any(p_sat >= P_arr):
            raise PsychrometricError(
                "Saturation pressure must remain lower than total pressure."
            )

        W_sat = Psychrometrics.EPSILON * p_sat / (P_arr - p_sat)
        W_sat = np.maximum(W_sat, Psychrometrics.MIN_HUMIDITY_RATIO)
        return Psychrometrics._return_scalar_if_scalar(T, W_sat)

    @staticmethod
    def enthalpy(T, W):
        """
        Compute specific enthalpy of moist air.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.

        Returns
        -------
        float or ndarray
            Moist-air enthalpy in kJ / kg_dry_air.

        Raises
        ------
        PsychrometricError
            If humidity ratio is negative.

        Notes
        -----
        The formulation is:

        ``h = cp * T + W * (Hfg + cp_v * T)``

        This is a standard engineering approximation widely used in
        psychrometric analysis and chart calculations.

        See Also
        --------
        dry_air_enthalpy : Enthalpy of dry air only.
        vapor_enthalpy : Enthalpy contribution of water vapor.

        Examples
        --------
        >>> round(Psychrometrics.enthalpy(30.0, 0.015), 2)
        68.53
        >>> T = np.array([20.0, 25.0, 30.0])
        >>> W = np.array([0.008, 0.010, 0.015])
        >>> Psychrometrics.enthalpy(T, W).shape
        (3,)
        """
        Psychrometrics._require_non_negative_W(W)
        T_arr, W_arr = Psychrometrics._broadcast(T, W)
        W_arr = np.maximum(W_arr, Psychrometrics.MIN_HUMIDITY_RATIO)

        # Total enthalpy is the sum of the dry-air sensible term and the
        # water-vapor latent+sensible term.
        h = Psychrometrics.cp * T_arr + W_arr * (
            Psychrometrics.Hfg + Psychrometrics.cp_v * T_arr
        )

        scalar_ref = T if np.isscalar(T) and np.isscalar(W) else T_arr
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, h)

    @staticmethod
    def dry_air_enthalpy(T):
        """
        Compute specific enthalpy of dry air.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.

        Returns
        -------
        float or ndarray
            Dry-air enthalpy in kJ / kg.

        Notes
        -----
        This method uses the constant specific heat approximation:

        ``h_da = cp * T``

        Examples
        --------
        >>> round(Psychrometrics.dry_air_enthalpy(30.0), 2)
        30.18
        """
        T_arr = Psychrometrics._asarray(T)
        h_da = Psychrometrics.cp * T_arr
        return Psychrometrics._return_scalar_if_scalar(T, h_da)

    @staticmethod
    def wet_bulb_line(T_db, T_wb, P=101325.0):
        """
        Compute a constant wet-bulb line in humidity-ratio space.

        Parameters
        ----------
        T_db : float or ndarray
            Dry-bulb temperature values in degrees Celsius.
        T_wb : float or ndarray
            Wet-bulb temperature in degrees Celsius.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Humidity ratio values along the wet-bulb line.

        Raises
        ------
        PsychrometricError
            If pressure is not strictly positive.

        Notes
        -----
        This method preserves the original fast approximation intended for
        chart construction and quick plotting. It is not a full iterative
        psychrometric wet-bulb solver.

        The approximation used is:

        ``W_line = W_sat(T_wb) - cp * (T_db - T_wb) / Hfg``

        Negative values are clipped to zero.

        Examples
        --------
        >>> T_db = np.array([20.0, 25.0, 30.0])
        >>> W_line = Psychrometrics.wet_bulb_line(T_db, 18.0)
        >>> W_line.shape
        (3,)
        """
        Psychrometrics._require_positive_pressure(P)
        T_db_arr, T_wb_arr, P_arr = Psychrometrics._broadcast(T_db, T_wb, P)

        # The line starts from saturation at the wet-bulb temperature and is
        # adjusted using a simple enthalpy-like approximation.
        W_sat_wb = Psychrometrics.saturation_humidity_ratio(T_wb_arr, P_arr)
        W_line = (
            W_sat_wb
            - Psychrometrics.cp * (T_db_arr - T_wb_arr) / Psychrometrics.Hfg
        )

        # Negative humidity ratios are not physical, so clip at zero.
        W_line = np.maximum(W_line, 0.0)
        return Psychrometrics._return_scalar_if_scalar(T_db, W_line)

    @staticmethod
    def dew_point_temperature(RH, T, P=101325.0, tol=0.01, max_iter=100):
        """
        Compute dew-point temperature from dry-bulb temperature and RH.

        Parameters
        ----------
        RH : float or ndarray
            Relative humidity as a fraction in the interval [0, 1].
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        P : float or ndarray, optional
            Total pressure in pascals. This argument is preserved only for
            interface compatibility. The default is ``101325.0``.
        tol : float, optional
            Convergence tolerance in degrees Celsius. The default is ``0.01``.
        max_iter : int, optional
            Maximum number of bisection iterations. The default is ``100``.

        Returns
        -------
        float or ndarray
            Dew-point temperature in degrees Celsius.

        Raises
        ------
        PsychrometricError
            If relative humidity is outside the interval [0, 1].

        Notes
        -----
        Dew point is determined by first computing the vapor pressure from RH
        and dry-bulb temperature, then solving for the temperature at which the
        saturation pressure equals that vapor pressure.

        A bisection method is used because it is robust and easy to vectorize.

        The pressure argument is not needed when RH and T are already known, but
        it is kept here to preserve drop-in compatibility with an existing API.

        Examples
        --------
        >>> round(Psychrometrics.dew_point_temperature(0.60, 30.0), 2)
        21.38
        >>> T = np.array([25.0, 30.0])
        >>> RH = np.array([0.50, 0.80])
        >>> Psychrometrics.dew_point_temperature(RH, T).shape
        (2,)
        """
        # Pressure is intentionally unused; it is retained only for signature
        # compatibility with existing calling code.
        del P

        Psychrometrics._require_rh(RH)
        T_arr, RH_arr = Psychrometrics._broadcast(T, RH)
        p_v = RH_arr * Psychrometrics.saturation_pressure(T_arr)

        # For zero or near-zero vapor pressure, dew point is undefined in the
        # usual atmospheric sense; return NaN to signal absence of a finite
        # solution under this implementation.
        if np.any(p_v <= 0.0):
            result = np.full(np.shape(p_v), np.nan, dtype=float)
            scalar_ref = T if np.isscalar(T) and np.isscalar(RH) else T_arr
            return Psychrometrics._return_scalar_if_scalar(scalar_ref, result)

        # Initial bounds cover a wide practical temperature range.
        low = np.full_like(p_v, -100.0, dtype=float)
        high = np.full_like(p_v, 200.0, dtype=float)

        # Solve p_sat(T_dp) = p_v using bisection.
        for _ in range(max_iter):
            mid = 0.5 * (low + high)
            p_mid = Psychrometrics.saturation_pressure(mid)

            too_high = p_mid > p_v
            high = np.where(too_high, mid, high)
            low = np.where(too_high, low, mid)

            if np.all((high - low) <= tol):
                break

        t_dp = 0.5 * (low + high)
        scalar_ref = T if np.isscalar(T) and np.isscalar(RH) else T_arr
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, t_dp)

    @staticmethod
    def relative_humidity_from_W(T, W, P=101325.0):
        """
        Compute relative humidity from humidity ratio.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Relative humidity as a fraction in the interval [0, 1].

        Raises
        ------
        PsychrometricError
            If pressure is not strictly positive.
        PsychrometricError
            If humidity ratio is negative.

        Notes
        -----
        This function reconstructs vapor pressure from humidity ratio and then
        divides it by saturation vapor pressure at the given dry-bulb
        temperature. The final result is clipped to the interval [0, 1].

        Examples
        --------
        >>> W = Psychrometrics.humidity_ratio(30.0, 0.60)
        >>> round(Psychrometrics.relative_humidity_from_W(30.0, W), 6)
        0.6
        """
        Psychrometrics._require_positive_pressure(P)
        Psychrometrics._require_non_negative_W(W)

        T_arr, W_arr, P_arr = Psychrometrics._broadcast(T, W, P)
        p_v = Psychrometrics.vapor_pressure_from_W(W_arr, P_arr)
        p_sat = Psychrometrics.saturation_pressure(T_arr)
        RH = np.clip(p_v / p_sat, 0.0, 1.0)

        scalar_ref = (
            T if np.isscalar(T) and np.isscalar(W) and np.isscalar(P) else T_arr
        )
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, RH)

    @staticmethod
    def specific_humidity(W):
        """
        Convert humidity ratio to specific humidity.

        Parameters
        ----------
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.

        Returns
        -------
        float or ndarray
            Specific humidity in kg_vapor / kg_moist_air.

        Raises
        ------
        PsychrometricError
            If humidity ratio is negative.

        Notes
        -----
        The conversion is:

        ``q = W / (1 + W)``

        Specific humidity is based on the total moist-air mass, while humidity
        ratio is based only on the dry-air mass.

        See Also
        --------
        humidity_ratio_from_specific_humidity : Inverse transformation.

        Examples
        --------
        >>> round(Psychrometrics.specific_humidity(0.01), 6)
        0.009901
        """
        Psychrometrics._require_non_negative_W(W)
        W_arr = Psychrometrics._asarray(W)
        q = W_arr / (1.0 + W_arr)
        return Psychrometrics._return_scalar_if_scalar(W, q)

    @staticmethod
    def humidity_ratio_from_specific_humidity(q):
        """
        Convert specific humidity to humidity ratio.

        Parameters
        ----------
        q : float or ndarray
            Specific humidity in kg_vapor / kg_moist_air.

        Returns
        -------
        float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.

        Raises
        ------
        PsychrometricError
            If specific humidity is outside the interval [0, 1).

        Notes
        -----
        The inverse conversion is:

        ``W = q / (1 - q)``

        A lower bound is applied to avoid exactly zero humidity ratio in some
        numerical workflows.

        Examples
        --------
        >>> round(Psychrometrics.humidity_ratio_from_specific_humidity(0.01), 6)
        0.010101
        """
        Psychrometrics._require_non_negative_q(q)
        q_arr = Psychrometrics._asarray(q)
        W = q_arr / (1.0 - q_arr)
        W = np.maximum(W, Psychrometrics.MIN_HUMIDITY_RATIO)
        return Psychrometrics._return_scalar_if_scalar(q, W)

    @staticmethod
    def specific_volume(T, W, P=101325.0):
        """
        Compute specific volume of moist air per unit mass of dry air.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Specific volume in m^3 / kg_dry_air.

        Raises
        ------
        PsychrometricError
            If pressure is not strictly positive.
        PsychrometricError
            If humidity ratio is negative.

        Notes
        -----
        The formulation is based on the ideal-gas approximation for moist air:

        ``v = Rd * T_K * (1 + 1.607858 * W) / P``

        This expression returns volume per unit mass of dry air, which is the
        standard psychrometric convention used in chart calculations.

        Examples
        --------
        >>> round(Psychrometrics.specific_volume(30.0, 0.015), 4)
        0.8772
        """
        Psychrometrics._require_positive_pressure(P)
        Psychrometrics._require_non_negative_W(W)

        T_arr, W_arr, P_arr = Psychrometrics._broadcast(T, W, P)
        W_arr = np.maximum(W_arr, Psychrometrics.MIN_HUMIDITY_RATIO)
        T_K = T_arr + Psychrometrics.ZERO_CELSIUS_AS_KELVIN

        # The correction factor (1 + 1.607858 * W) accounts for the presence of
        # water vapor relative to dry air under the ideal-gas framework.
        v = (Psychrometrics.Rd * T_K * (1.0 + 1.607858 * W_arr)) / P_arr

        scalar_ref = (
            T if np.isscalar(T) and np.isscalar(W) and np.isscalar(P) else T_arr
        )
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, v)

    @staticmethod
    def density(T, W, P=101325.0):
        """
        Compute apparent density-like quantity based on dry-air specific volume.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Density-like quantity in kg_dry_air / m^3.

        Notes
        -----
        This method preserves the original API behavior:

        ``density = 1 / specific_volume``

        Because ``specific_volume`` is expressed per unit mass of dry air, this
        result is not the full physical moist-air density. For the physically
        consistent density of moist air in kg_moist_air / m^3, use
        :meth:`moist_air_density`.

        See Also
        --------
        specific_volume : Specific volume per unit mass of dry air.
        moist_air_density : Physical moist-air density.

        Examples
        --------
        >>> round(Psychrometrics.density(30.0, 0.015), 4)
        1.14
        """
        v = Psychrometrics.specific_volume(T, W, P)
        rho = 1.0 / v
        scalar_ref = T if np.isscalar(T) and np.isscalar(W) and np.isscalar(P) else v
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, rho)

    @staticmethod
    def moist_air_density(T, W, P=101325.0):
        """
        Compute physical moist-air density.

        Parameters
        ----------
        T : float or ndarray
            Dry-bulb temperature in degrees Celsius.
        W : float or ndarray
            Humidity ratio in kg_vapor / kg_dry_air.
        P : float or ndarray, optional
            Total air pressure in pascals. The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Moist-air density in kg_moist_air / m^3.

        Notes
        -----
        Since :meth:`specific_volume` returns volume per unit mass of dry air,
        multiplying by ``(1 + W)`` converts the dry-air-based formulation into
        a total moist-air density:

        ``rho_moist = (1 + W) / v``

        Examples
        --------
        >>> round(Psychrometrics.moist_air_density(30.0, 0.015), 4)
        1.1571
        """
        T_arr, W_arr, P_arr = Psychrometrics._broadcast(T, W, P)
        v = Psychrometrics.specific_volume(T_arr, W_arr, P_arr)
        rho_moist = (1.0 + W_arr) / v

        scalar_ref = (
            T if np.isscalar(T) and np.isscalar(W) and np.isscalar(P) else T_arr
        )
        return Psychrometrics._return_scalar_if_scalar(scalar_ref, rho_moist)

    @staticmethod
    def vapor_enthalpy(T):
        """
        Compute specific enthalpy of water vapor.

        Parameters
        ----------
        T : float or ndarray
            Temperature in degrees Celsius.

        Returns
        -------
        float or ndarray
            Water vapor enthalpy in kJ / kg.

        Notes
        -----
        The approximation used is:

        ``h_v = Hfg + cp_v * T``

        This is useful when separating moist-air enthalpy into dry-air and
        vapor contributions.

        Examples
        --------
        >>> round(Psychrometrics.vapor_enthalpy(30.0), 2)
        2556.8
        """
        T_arr = Psychrometrics._asarray(T)
        h_v = Psychrometrics.Hfg + Psychrometrics.cp_v * T_arr
        return Psychrometrics._return_scalar_if_scalar(T, h_v)

    @staticmethod
    def dew_point_line(T_db, RH, P=101325.0):
        """
        Compute dew-point temperature line for constant relative humidity.

        Parameters
        ----------
        T_db : float or ndarray
            Dry-bulb temperature values in degrees Celsius.
        RH : float or ndarray
            Relative humidity as a fraction in the interval [0, 1].
        P : float or ndarray, optional
            Total air pressure in pascals. Kept for interface compatibility.
            The default is ``101325.0``.

        Returns
        -------
        float or ndarray
            Dew-point temperatures in degrees Celsius.

        Notes
        -----
        This is a convenience wrapper around :meth:`dew_point_temperature`.

        Examples
        --------
        >>> T = np.array([20.0, 25.0, 30.0])
        >>> Psychrometrics.dew_point_line(T, 0.60).shape
        (3,)
        """
        return Psychrometrics.dew_point_temperature(RH, T_db, P)

    @staticmethod
    def standard_atmosphere_pressure(altitude_m):
        """
        Estimate standard-atmosphere pressure from altitude.

        Parameters
        ----------
        altitude_m : float or ndarray
            Altitude above mean sea level in meters.

        Returns
        -------
        float or ndarray
            Estimated pressure in pascals.

        Notes
        -----
        This method uses a common standard-atmosphere approximation valid for
        lower tropospheric applications:

        ``P = 101325 * (1 - 2.25577e-5 * z)^5.2559``

        It is useful for converting station elevation into an approximate local
        pressure when explicit pressure observations are unavailable.

        Examples
        --------
        >>> round(Psychrometrics.standard_atmosphere_pressure(0.0), 2)
        101325.0
        >>> round(Psychrometrics.standard_atmosphere_pressure(1000.0), 2)
        89874.57
        """
        z = Psychrometrics._asarray(altitude_m)
        P = 101325.0 * (1.0 - 2.25577e-5 * z) ** 5.2559
        return Psychrometrics._return_scalar_if_scalar(altitude_m, P)
