# psychchart/plot/index_profiles/registry.py

"""
Central registry for index semantic profiles.

This module provides a **single point of access** to all
canonical :class:`IndexProfile` definitions available in the system.

The registry decouples:
- *index semantics* (thresholds, colors, labels),
from:
- *plotting logic* and *configuration parsing*.

By centralizing profiles here, the rest of the codebase can:
- request a profile by name,
- remain agnostic to where and how profiles are defined,
- avoid hard-coded imports scattered across modules.

This module is intentionally minimal and dependency-light.
"""

from typing import Optional

from .base import IndexProfile
from .itu import ITU_PROFILE


# =============================================================================
# Internal registry
# =============================================================================
# Maps index identifiers to their canonical semantic profiles.
#
# Keys MUST match:
# - IndexConfig.name
# - IndexField.index
# - IndexZone.index
#
# Values are immutable IndexProfile instances.
_INDEX_PROFILES = {
    "ITU": ITU_PROFILE,
}


# =============================================================================
# Public API
# =============================================================================
def get_index_profile(name: str) -> Optional[IndexProfile]:
    """
    Return the canonical semantic profile for a given index.

    This function acts as a **read-only lookup service** for
    :class:`IndexProfile` objects.

    It allows plotting and configuration code to retrieve
    the semantic definition of an index (thresholds, colors,
    labels, default mode) using only its string identifier,
    without importing specific profile modules directly.

    Parameters
    ----------
    name : str
        Index identifier (e.g., ``"ITU"``, ``"HLI"``).

    Returns
    -------
    IndexProfile or None
        The corresponding semantic profile if the index
        is registered, otherwise ``None``.

    Notes
    -----
    - This function performs **no validation** beyond dictionary lookup.
    - Returning ``None`` instead of raising an exception allows
      higher-level code to:
        * fall back to defaults,
        * emit warnings,
        * or raise domain-specific errors.
    - All profiles returned by this function are immutable
      (``IndexProfile`` is frozen).

    Examples
    --------
    Basic lookup:

    >>> profile = get_index_profile("ITU")
    >>> profile.name
    'ITU'

    Using profile information to configure an index field:

    >>> profile = get_index_profile("ITU")
    >>> field = IndexField(
    ...     index=profile.name,
    ...     levels=profile.levels,
    ... )

    Handling missing profiles gracefully:

    >>> profile = get_index_profile("UNKNOWN")
    >>> if profile is None:
    ...     print("No semantic profile defined for this index.")
    """

    # ------------------------------------------------------------------
    # Dictionary lookup (read-only)
    # ------------------------------------------------------------------
    return _INDEX_PROFILES.get(name)

