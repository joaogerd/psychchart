"""
Configuration loader for psychchart.

This module implements the complete loading pipeline:

1. read packaged base profile
2. read user YAML
3. resolve which profile should be used
4. deep-merge profile + user data
5. validate and normalize using the single Pydantic model layer
6. return the payload expected by the plotting runtime

The loader deliberately does not contain field-by-field procedural parsing.
That responsibility now belongs to the typed models declared in
``psychchart.config``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import ValidationError

from .config import AppConfig
from .merge import deep_merge

BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"
DEFAULT_PROFILE = "default_si.yaml"


def load_yaml(path: str | Path) -> dict[str, Any]:
    """
    Read a YAML file into a Python mapping.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the YAML file.

    Returns
    -------
    dict
        Parsed YAML mapping. Empty YAML documents become empty dicts.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the top-level YAML node is not a mapping.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Top-level YAML structure must be a mapping/dict: {path}")

    return data


def resolve_profile_path(profile_name: str | None) -> Path:
    """
    Resolve a profile name to a packaged YAML file path.

    Parameters
    ----------
    profile_name : str or None
        Profile name declared by the user. If ``None``, the default packaged
        profile is used.

    Returns
    -------
    pathlib.Path
        Absolute path to the selected profile file.
    """
    if not profile_name:
        return PROFILES_DIR / DEFAULT_PROFILE

    profile_name = profile_name.strip()
    if not profile_name.endswith((".yaml", ".yml")):
        profile_name = f"{profile_name}.yaml"

    return PROFILES_DIR / profile_name


def load_chart_config(path: str | Path) -> Dict[str, Any]:
    """
    Load a psychchart configuration file.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the user YAML configuration.

    Returns
    -------
    dict
        Payload compatible with ``PsychChart(**data)``.

    Raises
    ------
    FileNotFoundError
        If the user file or selected profile does not exist.
    ValueError
        If YAML parsing or typed validation fails.

    Examples
    --------
    >>> data = load_chart_config("examples/IOR_full.yaml")
    >>> sorted(data.keys())
    ['cfg', 'index_zones', 'indexes', 'isolines', 'observations', 'points', 'temporal_overlays', 'zones']
    """
    user_path = Path(path)
    user_data = load_yaml(user_path)

    # The user may explicitly select a packaged profile through a top-level
    # "profile" key. This key is configuration meta-data and is not part of
    # the validated chart model itself, so it is removed before merge.
    profile_name = user_data.pop("profile", None)
    profile_path = resolve_profile_path(profile_name)

    profile_data = load_yaml(profile_path)
    merged = deep_merge(profile_data, user_data)

    try:
        config = AppConfig.model_validate(merged)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid configuration in '{user_path.name}' "
            f"using profile '{profile_path.name}':\n{exc}"
        ) from exc

    return config.to_runtime_payload()


def load(path: str | Path) -> Dict[str, Any]:
    """
    Backward-compatible alias for :func:`load_chart_config`.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the user YAML configuration.

    Returns
    -------
    dict
        Payload compatible with ``PsychChart(**data)``.
    """
    return load_chart_config(path)
