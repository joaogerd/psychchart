"""
Thermal and bioclimatic indexes.

This subpackage aggregates thermal comfort and heat-stress indexes
under a unified public API. It exposes both the abstract base class
(:class:`ComfortIndex`) and concrete index implementations (e.g., ITU).

Design goals
------------
- Provide a clear and stable import surface for users.
- Allow interchangeable use of different indexes via a common interface.
- Support scientific reproducibility by enforcing explicit documentation
  of inputs and assumptions at the index level.

Conceptual scope
----------------
Thermal and bioclimatic indexes are empirical or semi-empirical
diagnostic tools that combine meteorological variables (temperature,
humidity, wind, radiation) to interpret comfort or heat stress.

They are conceptually distinct from psychrometric relationships, but
often rely on psychrometric variables as inputs.

Currently implemented indexes
-----------------------------
- ITU (Temperature-Humidity Index)

Future extensions may include:
- BGHI (Black Globe Humidity Index)
- HLI (Heat Load Index)
- UTCI (Universal Thermal Climate Index)
"""

# ---------------------------------------------------------------------
# Public base class
# ---------------------------------------------------------------------
from .base import ComfortIndex

# ---------------------------------------------------------------------
# Concrete index implementations
# ---------------------------------------------------------------------
from .iti import ITU

# ---------------------------------------------------------------------
# Public symbols exported by this module
#
# Using __all__ explicitly defines the public API and prevents
# accidental exposure of internal helpers when using:
#     from psychchart.indexes import *
# ---------------------------------------------------------------------
__all__ = [
    "ComfortIndex",
    "ITU",
]

