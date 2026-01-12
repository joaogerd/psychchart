# psychchart/plot/index_profiles/__init__.py

"""
Public interface for index semantic profiles.

This subpackage provides **semantic definitions** for bioclimatic
and thermal indexes used in psychrometric charts.

It exposes:
- the :class:`IndexProfile` dataclass, which defines how an index
  should be interpreted and visualized;
- the :func:`get_index_profile` helper, which retrieves the
  canonical profile for a given index name.

The goal of this package is to centralize *scientific meaning*
(thresholds, colors, labels) and keep plotting code generic
and free of hard-coded semantics.

Typical usage
-------------
Retrieve a semantic profile by index name:

>>> from psychchart.plot.index_profiles import get_index_profile
>>> profile = get_index_profile("ITU")
>>> profile.levels
[0, 72, 78, 84, 90, 200]

Use the profile to configure an index field:

>>> from psychchart.plot.index_profiles import get_index_profile
>>> profile = get_index_profile("ITU")
>>> field = IndexField(
...     index=profile.name,
...     levels=profile.levels,
... )

Design notes
------------
- Only the **public API** is re-exported here.
- Concrete profile implementations (e.g., ITU, HLI) are intentionally
  *not* imported at this level to avoid namespace pollution.
- All profiles are immutable and centrally registered.
"""

# ---------------------------------------------------------------------
# Public re-exports
# ---------------------------------------------------------------------
from .base import IndexProfile
from .registry import get_index_profile

__all__ = [
    "IndexProfile",
    "get_index_profile",
]

