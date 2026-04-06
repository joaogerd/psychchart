"""
Index registry and public API for psychchart indexes.

This module exposes:

- Built-in index classes
- Centralized INDEX_REGISTRY
- Utility functions for dynamic lookup

Design Philosophy
-----------------
All indices are unified under BaseIndex and registered here.

This eliminates:

- if/else chains
- hard-coded imports
- special cases for specific indices

The registry is the single source of truth.
"""

from __future__ import annotations

from typing import Type, Dict

from .base import BaseIndex
from .itu import ITU
from .icf import ICF
from .hli import HLI


# ---------------------------------------------------------------------
# Central registry
# ---------------------------------------------------------------------

INDEX_REGISTRY: Dict[str, Type[BaseIndex]] = {
    ITU.name: ITU,
    ICF.name: ICF,
    HLI.name: HLI,
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def get_index(name: str) -> Type[BaseIndex]:
    """
    Retrieve an index class by name.

    Parameters
    ----------
    name : str
        Index name (case-insensitive).

    Returns
    -------
    Type[BaseIndex]
        Corresponding index class.

    Raises
    ------
    KeyError
        If index is not registered.

    Examples
    --------
    >>> idx_cls = get_index("ITU")
    >>> idx_cls.name
    'ITU'
    """
    key = name.upper()

    if key not in INDEX_REGISTRY:
        raise KeyError(
            f"Unknown index '{name}'. "
            f"Available: {list(INDEX_REGISTRY.keys())}"
        )

    return INDEX_REGISTRY[key]


def list_indexes() -> list[str]:
    """
    List available index names.

    Returns
    -------
    list of str
        Registered index identifiers.

    Examples
    --------
    >>> list_indexes()
    ['ITU', 'ICF', 'HLI']
    """
    return sorted(INDEX_REGISTRY.keys())


__all__ = [
    "BaseIndex",
    "ITU",
    "ICF",
    "HLI",
    "INDEX_REGISTRY",
    "get_index",
    "list_indexes",
]

