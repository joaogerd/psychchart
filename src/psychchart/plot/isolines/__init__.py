"""
Public interface for psychrometric isoline rendering.

This module exposes the **stable public API** for drawing psychrometric
isolines on a chart.

Only high-level orchestration functions intended for external use
are re-exported here. Internal helpers, handlers, and registries
remain encapsulated within the subpackage.

Design goals
------------
- Provide a minimal and explicit public API.
- Hide internal implementation details (handlers, registries, helpers).
- Allow internal refactoring without breaking user code.

External code should import isoline rendering functionality
**exclusively** from this module.
"""

from .base import draw_isolines


# -----------------------------------------------------------------------------
# Public symbols
# -----------------------------------------------------------------------------
# Only the following names are guaranteed to be stable.
__all__ = ["draw_isolines"]

