"""
Central registry for isoline semantic profiles.

This module defines a **single source of truth** for all available
:class:`IsolineProfile` objects used by the psychrometric chart
rendering pipeline.

It acts as a lightweight lookup layer that maps **canonical isoline
family names** (strings) to their corresponding semantic profiles.

Design intent
-------------
- Provide a centralized and explicit registry of isoline profiles.
- Avoid scattered imports of individual profiles across the codebase.
- Enable dynamic profile resolution by name (e.g. from configuration).

This module is intentionally minimal and declarative.
"""

from typing import Optional

from .base import IsolineProfile
from .relative_humidity import RH_PROFILE
from .enthalpy import ENTHALPY_PROFILE
from .moisture import MOISTURE_PROFILE
from .specific_volume import SPECIFIC_VOLUME_PROFILE
from .wet_bulb import WET_BULB_PROFILE


# =============================================================================
# Internal isoline profile registry
# =============================================================================
# Keys must match:
# - IsoSet identifiers
# - renderer isoline-family names
#
# Values are immutable IsolineProfile instances.
#
# This dictionary should ONLY contain semantic definitions, never logic.
_ISOLINE_PROFILES = {
    "relative_humidity": RH_PROFILE,
    "enthalpy"         : ENTHALPY_PROFILE,
    "moisture"         : MOISTURE_PROFILE,
    "specific_volume"  : SPECIFIC_VOLUME_PROFILE,
    "wet_bulb.py"      : WET_BULB_PROFILE,
}


def get_isoline_profile(name: str) -> Optional[IsolineProfile]:
    """
    Retrieve a semantic isoline profile by name.

    This function provides a safe and centralized way to resolve
    an isoline semantic profile given its canonical name.

    Parameters
    ----------
    name : str
        Canonical name of the isoline family.

        This must match one of the keys registered in the internal
        isoline profile registry (e.g. ``"relative_humidity"``).

    Returns
    -------
    IsolineProfile or None
        The corresponding semantic isoline profile if found,
        otherwise ``None``.

    Notes
    -----
    - This function does **not** raise an exception if the profile
      is missing. Missing profiles are expected to be handled
      gracefully by higher-level code.
    - Validation of isoline names should occur at the configuration
      or orchestration layer, not here.

    Examples
    --------
    Retrieve the relative humidity profile:

    >>> profile = get_isoline_profile("relative_humidity")
    >>> profile.name
    'relative_humidity'

    Handle missing profiles safely:

    >>> profile = get_isoline_profile("nonexistent_isoline")
    >>> profile is None
    True
    """
    return _ISOLINE_PROFILES.get(name)

