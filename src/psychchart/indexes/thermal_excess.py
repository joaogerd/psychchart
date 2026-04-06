from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .base import BaseIndex
from .itu import ITU


class ThermalExcess(BaseIndex):
    """
    Instantaneous thermal excess above a THI/ITU threshold.

    This index quantifies the **positive environmental exceedance**
    above a reference ITU/THI threshold. It is defined as:

    .. math::

        \\mathrm{THERMAL\\_EXCESS} = \\max(0, \\mathrm{ITU} - \\mathrm{threshold})

    The metric is useful when the goal is to represent, at each point
    in the psychrometric space, how much the thermal environment exceeds
    a predefined comfort or alert threshold. Unlike cumulative heat-load
    metrics, this quantity is **purely instantaneous** and does not retain
    any memory of previous exposure.

    In practical terms:

    - values equal to ``0`` indicate conditions at or below the threshold;
    - positive values indicate how far the current ITU is above the threshold;
    - larger values represent stronger instantaneous thermal stress potential.

    This class is especially suitable for:

    - background scalar fields in psychrometric charts;
    - risk-layer visualization;
    - threshold-based highlighting of stressful thermal regions.

    Attributes
    ----------
    name : str
        Canonical semantic name of the index.
    required_fields : set[str]
        Required input fields for computing the index.

    Notes
    -----
    - This is an **instantaneous** index.
    - It does **not** represent cumulative or lagged thermal load.
    - The underlying ITU value is delegated to :class:`ITU`.
    - The default threshold is ``72.0``, a commonly used reference in
      thermal comfort studies for dairy cattle, although the exact value
      may vary depending on species, breed, production system, and literature.
    - This design keeps the computation modular by reusing the ITU index
      instead of duplicating its formula here.

    See Also
    --------
    ITU
        Base thermal-humidity index used internally to compute the excess.
    BaseIndex
        Abstract base interface for scalar and vectorized thermal indexes.

    Examples
    --------
    Scalar computation using a single state:

    >>> context = {"T": 30.0, "RH": 70.0, "threshold": 72.0}
    >>> value = ThermalExcess.compute(context)
    >>> isinstance(value, float)
    True
    >>> value >= 0.0
    True

    Vectorized computation over multiple points:

    >>> context = {
    ...     "T": np.array([24.0, 28.0, 32.0]),
    ...     "RH": np.array([50.0, 65.0, 80.0]),
    ...     "threshold": 72.0,
    ... }
    >>> excess = ThermalExcess.compute_vectorized(context)
    >>> excess.shape
    (3,)
    >>> np.all(excess >= 0.0)
    np.True_

    Example with no excess below threshold:

    >>> context = {"T": 20.0, "RH": 40.0, "threshold": 72.0}
    >>> ThermalExcess.compute(context)
    0.0
    """

    # Canonical registry name used by the index system.
    # This string should remain stable because external configuration
    # files and the index registry may depend on it.
    name = "TE"

    # Minimal fields required by this index.
    # Although the computation is defined here, the actual thermal-humidity
    # formula is delegated to the ITU index, which itself depends on dry-bulb
    # temperature and relative humidity.
    required_fields = {"T", "RH"}

    @staticmethod
    def compute(context: Dict[str, Any]) -> float:
        """
        Compute the scalar instantaneous thermal excess.

        This method evaluates the ITU value for a single environmental state
        and then clips the result below zero according to the threshold rule:

        .. math::

            \\mathrm{THERMAL\\_EXCESS} = \\max(0, \\mathrm{ITU} - \\mathrm{threshold})

        Parameters
        ----------
        context : dict[str, Any]
            Mapping containing the environmental inputs required by
            :class:`ITU` and, optionally, the threshold configuration.

            Expected keys include:

            ``"T"``
                Dry-bulb air temperature.
            ``"RH"``
                Relative humidity.
            ``"threshold"``, optional
                Reference ITU threshold above which excess is computed.
                If omitted, the default value ``72.0`` is used.

        Returns
        -------
        float
            Non-negative instantaneous thermal excess.

        Raises
        ------
        KeyError
            If required fields expected by :class:`ITU` are missing from
            the input context.
        TypeError
            If the provided values cannot be interpreted by the underlying
            ITU computation.
        ValueError
            If the threshold value cannot be converted to ``float``.

        Notes
        -----
        - This method is intended for scalar or pointwise evaluation.
        - The result is always clipped to be non-negative.
        - The threshold is explicitly converted to ``float`` to ensure
          numerical consistency and predictable behavior.

        See Also
        --------
        compute_vectorized
            Vectorized version for NumPy arrays.
        ITU.compute
            Scalar computation of the underlying ITU index.

        Examples
        --------
        >>> context = {"T": 30.0, "RH": 70.0, "threshold": 72.0}
        >>> value = ThermalExcess.compute(context)
        >>> value >= 0.0
        True

        >>> context = {"T": 18.0, "RH": 45.0}
        >>> ThermalExcess.compute(context)
        0.0
        """
        # Use a configurable threshold so the same class can support
        # different scientific conventions or species-specific settings
        # without changing the implementation.
        threshold = float(context.get("threshold", 72.0))

        # Delegate ITU evaluation to the canonical index implementation.
        # This avoids formula duplication and guarantees consistency
        # across all components that depend on ITU.
        itu = ITU.compute(context)

        # The "excess" concept is one-sided: values below the threshold
        # are not negative stress, they simply mean "no excess".
        return max(0.0, itu - threshold)

    @staticmethod
    def compute_vectorized(context: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute the vectorized instantaneous thermal excess.

        This method evaluates the ITU field for array-like environmental
        inputs and applies the thermal excess definition elementwise:

        .. math::

            \\mathrm{THERMAL\\_EXCESS}_i =
            \\max(0, \\mathrm{ITU}_i - \\mathrm{threshold})

        The operation is fully vectorized using NumPy and is therefore
        appropriate for gridded fields, chart meshes, and batch evaluation.

        Parameters
        ----------
        context : dict[str, numpy.ndarray]
            Mapping containing array-like environmental inputs required by
            :class:`ITU` and, optionally, a scalar threshold.

            Expected keys include:

            ``"T"``
                Array of dry-bulb air temperatures.
            ``"RH"``
                Array of relative humidity values.
            ``"threshold"``, optional
                Scalar threshold applied to the full array.
                If omitted, the default value ``72.0`` is used.

        Returns
        -------
        numpy.ndarray
            Array with the same broadcast-compatible shape as the ITU result,
            containing the non-negative instantaneous thermal excess.

        Raises
        ------
        KeyError
            If required fields expected by :class:`ITU` are missing.
        TypeError
            If the provided arrays are not compatible with the underlying
            vectorized ITU computation.
        ValueError
            If broadcasting fails or the threshold cannot be converted
            to ``float``.

        Notes
        -----
        - This method is intended for efficient field computation.
        - ``numpy.maximum`` is used instead of Python's ``max`` because
          the operation must be applied elementwise over arrays.
        - The threshold is treated as a scalar reference across the domain.
          If spatially varying thresholds are needed in the future, this
          interface could be extended accordingly.

        See Also
        --------
        compute
            Scalar version for single-state evaluation.
        ITU.compute_vectorized
            Vectorized computation of the underlying ITU field.
        numpy.maximum
            Elementwise maximum operation used for zero clipping.

        Examples
        --------
        >>> context = {
        ...     "T": np.array([24.0, 28.0, 32.0]),
        ...     "RH": np.array([50.0, 65.0, 80.0]),
        ...     "threshold": 72.0,
        ... }
        >>> excess = ThermalExcess.compute_vectorized(context)
        >>> excess.shape
        (3,)
        >>> np.all(excess >= 0.0)
        np.True_

        >>> context = {
        ...     "T": np.array([18.0, 19.0]),
        ...     "RH": np.array([40.0, 45.0]),
        ... }
        >>> ThermalExcess.compute_vectorized(context)
        array([0., 0.])
        """
        # The threshold is kept scalar for conceptual simplicity:
        # one comfort/stress reference applied across the evaluated field.
        threshold = float(context.get("threshold", 72.0))

        # Reuse the canonical vectorized ITU implementation so that all
        # downstream products remain physically and numerically consistent.
        itu = ITU.compute_vectorized(context)

        # Apply non-negative clipping elementwise. This is the array-based
        # counterpart of "max(0.0, itu - threshold)" used in the scalar case.
        return np.maximum(0.0, itu - threshold)
