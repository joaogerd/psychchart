"""
Runtime field registry for canonical data layers.

This module resolves declarative data-layer field definitions into concrete
runtime arrays.

The registry is intentionally narrow and deterministic. It maps configuration
field types to computation logic while keeping rendering concerns out of the
data-processing layer.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from psychchart.config.data_layers import (
    DataIndexFieldConfig,
    DirectColumnFieldConfig,
)


def _coerce_mapping_like(value: Any) -> Any:
    """
    Coerce JSON-like or Python-literal-like strings into structured values.

    Parameters
    ----------
    value : Any
        Raw payload from a dataset cell.

    Returns
    -------
    Any
        Parsed or original value.
    """
    if isinstance(value, Mapping):
        return value

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return value

        try:
            return json.loads(raw)
        except Exception:
            pass

        try:
            return ast.literal_eval(raw)
        except Exception:
            pass

    return value


def _resolve_index_backend(index_name: str) -> Any:
    """
    Resolve one index backend from the actual psychchart index package.

    Resolution order
    ----------------
    1. ``psychchart.indexes`` public API
    2. ``psychchart.indexes.engine`` registry (private fallback)

    Parameters
    ----------
    index_name : str
        Canonical index identifier.

    Returns
    -------
    Any
        Resolved backend class/object.

    Raises
    ------
    ValueError
        If the index cannot be resolved.
    """
    # --------------------------------------------------------------
    # Public API first: expected stable import path
    # --------------------------------------------------------------
    try:
        import psychchart.indexes as public_indexes  # type: ignore

        if hasattr(public_indexes, index_name):
            return getattr(public_indexes, index_name)
    except Exception:
        pass

    # --------------------------------------------------------------
    # Engine registry fallback
    # --------------------------------------------------------------
    try:
        from psychchart.indexes import engine as index_engine  # type: ignore

        registry = getattr(index_engine, "_INDEX_REGISTRY", None)
        if isinstance(registry, dict) and index_name in registry:
            return registry[index_name]
    except Exception:
        pass

    raise ValueError(
        f"Unknown data index '{index_name}'. "
        "It is not available through psychchart.indexes nor indexes.engine."
    )


def _compute_from_direct_column(
    cfg: DirectColumnFieldConfig,
    df: pd.DataFrame,
) -> np.ndarray:
    """
    Materialize one direct-column field.

    Parameters
    ----------
    cfg : DirectColumnFieldConfig
        Field configuration.
    df : pandas.DataFrame
        Runtime dataframe.

    Returns
    -------
    ndarray
        Column values.

    Raises
    ------
    KeyError
        If the configured source column does not exist.
    """
    if cfg.col not in df.columns:
        raise KeyError(
            f"Direct-column field '{cfg.name}' references missing column '{cfg.col}'."
        )

    return df[cfg.col].to_numpy()


def _compute_from_data_index(
    cfg: DataIndexFieldConfig,
    df: pd.DataFrame,
) -> np.ndarray:
    """
    Materialize one computed data-index field.

    Parameters
    ----------
    cfg : DataIndexFieldConfig
        Field configuration.
    df : pandas.DataFrame
        Runtime dataframe.

    Returns
    -------
    ndarray
        Computed field values.

    Raises
    ------
    ValueError
        If the configured data index is unknown or does not expose
        a compatible entry point.
    KeyError
        If the configured ``source_col`` does not exist.
    """
    index_backend = _resolve_index_backend(cfg.index)

    # --------------------------------------------------------------
    # Record-based mode:
    # use one source column (e.g. behavior payload for ICF)
    # --------------------------------------------------------------
    if cfg.source_col is not None:
        if cfg.source_col not in df.columns:
            raise KeyError(
                f"Data-index field '{cfg.name}' references missing source column "
                f"'{cfg.source_col}'."
            )

        compute = getattr(index_backend, "compute", None)
        if compute is None or not callable(compute):
            raise ValueError(
                f"Data index backend '{cfg.index}' does not expose a callable 'compute'."
            )

        values: list[float] = []
        for raw in df[cfg.source_col]:
            payload = _coerce_mapping_like(raw)
            values.append(compute(payload, **cfg.parameters))

        return np.asarray(values, dtype=float)

    # --------------------------------------------------------------
    # Vectorized thermodynamic mode:
    # evaluate on (_T, _RH)
    # --------------------------------------------------------------
    evaluate = getattr(index_backend, "evaluate", None)
    if evaluate is not None and callable(evaluate):
        values = evaluate(
            df["_T"].to_numpy(),
            df["_RH"].to_numpy(),
            **cfg.parameters,
        )
        return np.asarray(values, dtype=float)

    # --------------------------------------------------------------
    # Final fallback: row-wise compute(dict)
    # --------------------------------------------------------------
    compute = getattr(index_backend, "compute", None)
    if compute is not None and callable(compute):
        values = []
        for _, row in df.iterrows():
            values.append(compute(row.to_dict(), **cfg.parameters))
        return np.asarray(values, dtype=float)

    raise ValueError(
        f"Data index backend '{cfg.index}' exposes neither 'evaluate' nor 'compute'."
    )


def compute_field(cfg: Any, df: pd.DataFrame) -> np.ndarray:
    """
    Resolve one canonical field configuration into a numeric runtime array.

    Parameters
    ----------
    cfg : Any
        Validated field configuration.
    df : pandas.DataFrame
        Runtime dataframe.

    Returns
    -------
    ndarray
        Materialized numeric field.

    Raises
    ------
    ValueError
        If the field type is unsupported.
    """
    if isinstance(cfg, DirectColumnFieldConfig):
        return _compute_from_direct_column(cfg, df)

    if isinstance(cfg, DataIndexFieldConfig):
        return _compute_from_data_index(cfg, df)

    raise ValueError(f"Unsupported field configuration type: {type(cfg)!r}")
