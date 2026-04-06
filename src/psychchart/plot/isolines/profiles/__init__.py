"""
Public interface for isoline semantic profiles.

This module defines the **public API surface** of the
``psychchart.isolines.profiles`` subpackage.

It re-exports only the objects that are intended to be consumed by
external code (renderers, configuration layers, extensions), while
hiding internal implementation details such as registries or
profile-specific modules.

Design goals
------------
- Provide a clean and minimal public API.
- Decouple external users from internal module structure.
- Allow internal refactoring without breaking user code.

Examples
--------
Import the public lookup function (recommended):

>>> from psychchart.isolines.profiles import get_isoline_profile
>>> prof = get_isoline_profile("relative_humidity")
>>> prof is not None
True
>>> prof.name
'relative_humidity'

Use the returned profile to access defaults:

>>> prof.values[:3]
[0.1, 0.2, 0.3]
>>> prof.linestyle
'--'
>>> prof.labels
True

Handle unknown profile names safely:

>>> missing = get_isoline_profile("nope")
>>> missing is None
True

Type annotations using the public interface:

>>> from psychchart.isolines.profiles import IsolineProfile
>>> def accepts_profile(p: IsolineProfile) -> str:
...     return p.name
>>> accepts_profile(prof)
'relative_humidity'
"""

from .base import IsolineProfile
from .registry import get_isoline_profile


# -----------------------------------------------------------------------------
# Public symbols
# -----------------------------------------------------------------------------
# Only the following names are guaranteed to be stable and supported.
# Anything not listed here should be considered internal.
__all__ = [
    "IsolineProfile",
    "get_isoline_profile",
]


# -----------------------------------------------------------------------------
# Optional: minimal smoke-test when executed directly
# -----------------------------------------------------------------------------
# This is handy during development ("python -m psychchart.isolines.profiles")
# and does not affect library behavior when imported.
if __name__ == "__main__":
    # Basic registry lookup
    prof = get_isoline_profile("relative_humidity")
    assert prof is not None, "Expected 'relative_humidity' profile to exist"

    # Print a short summary to help manual inspection
    print("[INFO] Loaded profile:", prof.name)
    print("[INFO] Levels:", list(prof.values or []))
    print("[INFO] Style:", prof.color, prof.linestyle, prof.linewidth)
    print("[INFO] Labels:", prof.labels, prof.label_fmt, prof.label_fontsize)
    print("[INFO] Rendering:", prof.zorder, prof.clip_to_saturation)

