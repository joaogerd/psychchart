"""
Index evaluation engine.

This module centralizes the **resolution and evaluation**
of thermal and bioclimatic comfort indexes.

It provides a **single public entry point** to compute index values
given:
- an index name,
- dry-bulb temperature,
- relative humidity,
- optional index-specific parameters.

The goal of this module is to:
- decouple index *selection* from index *implementation*,
- provide a stable API for plotting, diagnostics, and analysis,
- enforce the canonical ComfortIndex interface.
"""

from __future__ import annotations

from typing import Any, Dict, Union
import numpy as np

from .iti import ITU
from .hli import HLI
from .base import ComfortIndex


# ---------------------------------------------------------------------
# Public type alias
# ---------------------------------------------------------------------
ArrayLike = Union[float, np.ndarray]


# ---------------------------------------------------------------------
# Registry of available indexes
# ---------------------------------------------------------------------
# Maps index identifiers (strings) to concrete ComfortIndex classes.
#
# IMPORTANT:
# - Keys must match the `name` attribute of each index class.
# - Values must be subclasses of ComfortIndex.
#
# This registry is intentionally explicit to:
# - preserve scientific transparency,
# - avoid dynamic imports or reflection,
# - make supported indexes discoverable.
_INDEX_REGISTRY: Dict[str, type[ComfortIndex]] = {
    "ITU": ITU,
    "HLI": HLI,
}


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def evaluate_index(
    name: str,
    T: ArrayLike,
    RH: ArrayLike,
    *,
    params: Dict[str, Any] | None = None,
) -> ArrayLike:
    """
    Evaluate a thermal or bioclimatic comfort index by name.

    This function acts as a **dispatch layer** between high-level
    application logic (charts, diagnostics, reports) and concrete
    index implementations.

    It resolves the requested index from the internal registry
    and delegates the computation to the corresponding
    :class:`ComfortIndex` subclass.

    Parameters
    ----------
    name : str
        Identifier of the comfort index to evaluate.

        Examples:
        - ``"ITU"``
        - ``"HLI"``

    T : float or numpy.ndarray
        Dry-bulb air temperature [°C].

        Can be either:
        - a scalar value, or
        - a NumPy array.

    RH : float or numpy.ndarray
        Relative humidity as a fraction in the range [0, 1].

        Must have a shape compatible with ``T``.

    params : dict, optional
        Dictionary of index-specific auxiliary parameters.

        Examples:
        - ``{"WS": 2.0}``  (wind speed)
        - ``{"SR": 600}``  (solar radiation)

        If omitted, an empty dictionary is used.

    Returns
    -------
    float or numpy.ndarray
        Computed index value(s).

        The returned object has the same shape as the input
        ``T`` and ``RH``.

    Raises
    ------
    KeyError
        If the requested index name is not registered.

    Notes
    -----
    - This function does NOT:
        * validate input ranges,
        * perform unit conversion,
        * apply physical masking.
    - All such responsibilities are delegated to the caller
      or to the index implementation itself.
    - The function assumes that all registered indexes follow
      the :class:`ComfortIndex` contract.

    Design considerations
    ---------------------
    - Using an explicit registry avoids hidden dependencies.
    - Centralizing dispatch logic keeps plotting and analysis
      code free of index-specific branching.
    - This function is intentionally simple and transparent,
      favoring readability over cleverness.

    Examples
    --------
    Scalar evaluation:

    >>> evaluate_index("ITU", T=30.0, RH=0.65)
    78.4

    Vectorized evaluation:

    >>> T = np.array([25.0, 30.0, 35.0])
    >>> RH = np.array([0.5, 0.6, 0.7])
    >>> evaluate_index("ITU", T, RH)
    array([72.1, 78.4, 84.9])

    Evaluation with auxiliary parameters:

    >>> evaluate_index(
    ...     "HLI",
    ...     T, RH,
    ...     params={"WS": 2.0, "SR": 600.0}
    ... )
    """

    # --------------------------------------------------------------
    # Resolve index from registry
    # --------------------------------------------------------------
    try:
        index_cls = _INDEX_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown comfort index '{name}'. "
            f"Available indexes: {list(_INDEX_REGISTRY)}"
        ) from exc

    # --------------------------------------------------------------
    # Normalize optional parameters
    # --------------------------------------------------------------
    if params is None:
        params = {}

    # --------------------------------------------------------------
    # Delegate computation to index implementation
    # --------------------------------------------------------------
    return index_cls.evaluate(T, RH, **params)

