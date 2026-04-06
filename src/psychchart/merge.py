"""
Deep merge utilities for psychchart configuration documents.

This module merges:
- a base profile YAML
- a user YAML override

Merge rules
-----------
1. Dictionaries are merged recursively.
2. Scalars are replaced by the override value.
3. Lists without explicit identity are replaced entirely.
4. Selected top-level lists are merged by logical identity.

Why keyed list merge exists
---------------------------
Some top-level configuration lists represent named entities rather than
anonymous ordered collections. For these, replacing the entire list would be
too coarse and would force users to repeat too much YAML.

Examples include:
- ``indexes`` merged by ``index`` or legacy ``name``
- ``zones`` merged by ``name``
- ``index_zones`` merged by ``(index, name)``
- ``observations`` merged by ``file``
- ``temporal_overlays`` merged by ``(type, data)``
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


def merge_list_by_key(
    base: list[Any],
    override: list[Any],
    key_fn: Callable[[dict[str, Any]], Any],
) -> list[Any]:
    """
    Merge two lists using logical identity keys.

    Parameters
    ----------
    base : list
        Base list, usually from the profile.
    override : list
        Override list, usually from the user configuration.
    key_fn : callable
        Function that extracts the logical identity of an item.

    Returns
    -------
    list
        Merged list.

    Notes
    -----
    Items that are not mappings or that do not provide a valid identity key
    are appended without keyed merge behavior.
    """
    result: list[Any] = []
    keyed_positions: dict[Any, int] = {}

    for item in deepcopy(base):
        if isinstance(item, dict):
            identity = key_fn(item)
            if identity is not None:
                keyed_positions[identity] = len(result)
        result.append(item)

    for item in deepcopy(override):
        if not isinstance(item, dict):
            result.append(item)
            continue

        identity = key_fn(item)
        if identity is None:
            result.append(item)
            continue

        if identity in keyed_positions:
            pos = keyed_positions[identity]
            result[pos] = deep_merge(result[pos], item)
        else:
            keyed_positions[identity] = len(result)
            result.append(item)

    return result


def deep_merge(base: Any, override: Any) -> Any:
    """
    Recursively merge two configuration values.

    Parameters
    ----------
    base : Any
        Base value, usually from the profile.
    override : Any
        Override value, usually from the user YAML.

    Returns
    -------
    Any
        Merged value.
    """
    if isinstance(base, dict) and isinstance(override, dict):
        merged = deepcopy(base)

        for key, value in override.items():
            if key not in merged:
                merged[key] = deepcopy(value)
                continue

            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = deep_merge(merged[key], value)
                continue

            if isinstance(merged[key], list) and isinstance(value, list):
                if key == "indexes":
                    merged[key] = merge_list_by_key(
                        merged[key],
                        value,
                        lambda x: x.get("index") or x.get("name"),
                    )
                elif key == "zones":
                    merged[key] = merge_list_by_key(
                        merged[key],
                        value,
                        lambda x: x.get("name"),
                    )
                elif key == "index_zones":
                    merged[key] = merge_list_by_key(
                        merged[key],
                        value,
                        lambda x: (x.get("index"), x.get("name"))
                        if x.get("index") is not None and x.get("name") is not None
                        else None,
                    )
                elif key == "observations":
                    merged[key] = merge_list_by_key(
                        merged[key],
                        value,
                        lambda x: x.get("file"),
                    )
                elif key == "temporal_overlays":
                    merged[key] = merge_list_by_key(
                        merged[key],
                        value,
                        lambda x: (x.get("type"), x.get("data"))
                        if x.get("type") is not None and x.get("data") is not None
                        else None,
                    )
                else:
                    # Anonymous lists are replaced entirely. This is more
                    # predictable than guessing element-wise merge semantics.
                    merged[key] = deepcopy(value)
                continue

            merged[key] = deepcopy(value)

        return merged

    return deepcopy(override)
