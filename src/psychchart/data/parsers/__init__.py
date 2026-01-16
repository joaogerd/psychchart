"""
Public interface for observation parsers.

This module defines the **public API** of the
``psychchart.data.parsers`` package.

Only parser classes explicitly exported via ``__all__``
are considered stable and supported for external use.

Design rationale
----------------
- Internal parser implementations may evolve or be refactored
  without breaking user code.
- The public surface remains minimal, explicit, and predictable.
- Users are guided toward the recommended parsers.

Currently supported parsers
---------------------------
- CSVObservationParser
"""

from .csv import CSVObservationParser

# ---------------------------------------------------------------------
# Public symbols exported by this package
# ---------------------------------------------------------------------
__all__ = [
    "CSVObservationParser",
]

