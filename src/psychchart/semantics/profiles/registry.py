from __future__ import annotations

from .base import ClassificationProfile
from .cta import CTA_PROFILE


SEMANTIC_PROFILE_REGISTRY: dict[str, ClassificationProfile] = {
    CTA_PROFILE.name: CTA_PROFILE,
}


def get_classification_profile(name: str) -> ClassificationProfile:
    """
    Resolve one classification profile by name.

    Parameters
    ----------
    name : str
        Registered profile name.

    Returns
    -------
    ClassificationProfile
        Registered profile.

    Raises
    ------
    KeyError
        If the profile name is unknown.
    """
    key = str(name).upper()
    registry = {k.upper(): v for k, v in SEMANTIC_PROFILE_REGISTRY.items()}

    if key not in registry:
        available = ", ".join(sorted(SEMANTIC_PROFILE_REGISTRY))
        raise KeyError(
            f"Unknown classification profile {name!r}. Available: {available}"
        )

    return registry[key]
