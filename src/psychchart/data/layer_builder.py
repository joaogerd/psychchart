"""
Builder for canonical data-layer runtime objects.

This module converts validated ``DataLayerConfig`` objects into fully processed
``ProcessedDataLayer`` instances ready for rendering.

Responsibilities
----------------
- file loading (CSV / Parquet)
- projection-column validation
- relative-humidity normalization
- humidity-ratio computation
- construction of ``Observations`` / ``FunctionalObservations``
- derived-field materialization
- optional temporal ordering

Non-responsibilities
--------------------
- plotting
- semantic labeling
- legend construction
- Matplotlib artist creation
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from psychchart.config.data_layers import DataLayerConfig
from psychchart.data.config import ObservationsConfig as InMemoryObservationsConfig
from psychchart.data.functional import FunctionalObservations
from psychchart.data.observations import Observations
from psychchart.psychrometrics import Psychrometrics

from .field_registry import compute_field
from .layer_runtime import ProcessedDataLayer


def _infer_format(path: str) -> str:
    """
    Infer file format from path suffix.

    Parameters
    ----------
    path : str
        Source dataset path.

    Returns
    -------
    str
        Inferred format identifier.
    """
    suffix = Path(path).suffix.lower().lstrip(".")
    if suffix in {"csv", "parquet"}:
        return suffix
    return suffix


def _load_frame(path: str, fmt: str) -> pd.DataFrame:
    """
    Load a tabular dataset into a dataframe.

    Parameters
    ----------
    path : str
        Source dataset path.
    fmt : str
        Declared or inferred format.

    Returns
    -------
    pandas.DataFrame
        Loaded dataframe.

    Raises
    ------
    ValueError
        If the format is unsupported.
    """
    resolved = fmt or _infer_format(path)

    if resolved == "csv":
        return pd.read_csv(path)

    if resolved == "parquet":
        return pd.read_parquet(path)

    raise ValueError(f"Unsupported data-layer format: {resolved}")


def _normalize_rh_series(values: Iterable[float], unit: str) -> np.ndarray:
    """
    Normalize a relative-humidity series into fractional form.

    Parameters
    ----------
    values : iterable of float
        Raw RH values.
    unit : {"fraction", "percent", "auto"}
        RH convention.

    Returns
    -------
    ndarray
        Normalized RH values in the interval approximately ``[0, 1]``.
    """
    arr = np.asarray(list(values), dtype=float)

    if unit == "fraction":
        normalized = arr
    elif unit == "percent":
        normalized = arr / 100.0
    elif unit == "auto":
        normalized = np.where(arr > 1.0, arr / 100.0, arr)
    else:
        raise ValueError(f"Unsupported rh_unit: {unit}")

    return normalized


def _build_observations_config(
    cfg: DataLayerConfig,
    df: pd.DataFrame,
) -> InMemoryObservationsConfig:
    """
    Build the existing in-memory observations config used by the data layer.

    Parameters
    ----------
    cfg : DataLayerConfig
        Canonical data-layer configuration.
    df : pandas.DataFrame
        Runtime dataframe already containing ``_T`` and ``_RH``.

    Returns
    -------
    ObservationsConfig
        In-memory observation configuration reused by the existing data layer.
    """
    time_values: Optional[np.ndarray] = None
    if cfg.temporal is not None and cfg.temporal.time_col in df.columns:
        time_values = df[cfg.temporal.time_col].to_numpy()

    return InMemoryObservationsConfig(
        T=df["_T"].to_numpy(),
        RH=df["_RH"].to_numpy(),
        time=time_values,
        label=None,
        metadata={"source": cfg.data},
    )


def _require_columns(df: pd.DataFrame, names: Iterable[str], context: str) -> None:
    """Validate that all named columns are present in a dataframe."""
    missing = [name for name in names if name not in df.columns]
    if not missing:
        return

    available = ", ".join(map(str, df.columns))
    raise KeyError(
        f"{context} references missing column(s): {missing}. "
        f"Available columns: {available}"
    )


def _validate_render_references(cfg: DataLayerConfig, df: pd.DataFrame) -> None:
    """Validate renderer column references after fields have been materialized.

    Renderers should fail before plotting when they reference a missing field or
    source column. This keeps errors close to the data-layer build step and
    avoids partially rendered figures with late Matplotlib failures.
    """
    for render_cfg in cfg.render:
        render_type = render_cfg.type
        context = f"Data layer '{cfg.data}' render '{render_type}'"

        if render_type == "scatter" and render_cfg.value is not None:
            _require_columns(df, [render_cfg.value], context)

        elif render_type == "scalar_field":
            _require_columns(df, [render_cfg.value], context)

        elif render_type == "classified_points":
            _require_columns(df, [render_cfg.value_col], context)

        elif render_type == "path":
            names: list[str] = []
            if render_cfg.order_by is not None:
                names.append(render_cfg.order_by)
            if render_cfg.color_by is not None:
                names.append(render_cfg.color_by)
            _require_columns(df, names, context)

        elif render_type == "annotate":
            names = [name for name in (render_cfg.time_field, render_cfg.value_field) if name]
            _require_columns(df, names, context)


def build_data_layer(cfg: DataLayerConfig, pressure: float) -> ProcessedDataLayer:
    """
    Build one processed runtime layer from a canonical data-layer config.

    Parameters
    ----------
    cfg : DataLayerConfig
        Validated data-layer configuration.
    pressure : float
        Reference pressure used to compute humidity ratio.

    Returns
    -------
    ProcessedDataLayer
        Fully processed runtime layer.

    Raises
    ------
    KeyError
        If required dataset columns are missing.
    ValueError
        If one or more thermodynamic values are outside the accepted range.
    """
    df = _load_frame(cfg.data, cfg.format)

    t_col = cfg.projection.t_col
    rh_col = cfg.projection.rh_col

    if t_col not in df.columns:
        raise KeyError(
            f"Data-layer source '{cfg.data}' is missing temperature column '{t_col}'."
        )

    if rh_col not in df.columns:
        raise KeyError(
            f"Data-layer source '{cfg.data}' is missing RH column '{rh_col}'."
        )

    T = df[t_col].astype(float).to_numpy()
    RH = _normalize_rh_series(df[rh_col], cfg.projection.rh_unit)

    if np.any((RH < 0.0) | (RH > 1.05)):
        raise ValueError(
            f"Relative humidity outside valid range after normalization in '{cfg.data}'."
        )

    W = Psychrometrics.humidity_ratio(T, RH, P=pressure)

    runtime_df = df.copy()
    runtime_df["_T"] = T
    runtime_df["_RH"] = RH
    runtime_df["_W"] = W

    if cfg.temporal is not None and cfg.temporal.sort:
        time_col = cfg.temporal.time_col
        if time_col not in runtime_df.columns:
            raise KeyError(
                f"Temporal ordering column '{time_col}' not found in '{cfg.data}'."
            )
        runtime_df = runtime_df.sort_values(time_col).reset_index(drop=True)

    obs_cfg = _build_observations_config(cfg, runtime_df)
    observations = Observations(obs_cfg)

    field_names: list[str] = []
    for field_cfg in cfg.fields:
        runtime_df[field_cfg.name] = compute_field(field_cfg, runtime_df)
        field_names.append(field_cfg.name)

    functional_observations: Optional[FunctionalObservations] = None
    if field_names:
        functional_observations = FunctionalObservations(
            obs_cfg,
            **{name: runtime_df[name].to_numpy() for name in field_names},
        )

    _validate_render_references(cfg, runtime_df)

    return ProcessedDataLayer(
        config=cfg,
        frame=runtime_df,
        observations=observations,
        functional_observations=functional_observations,
        T=runtime_df["_T"].to_numpy(),
        RH=runtime_df["_RH"].to_numpy(),
        W=runtime_df["_W"].to_numpy(),
        fields={name: runtime_df[name].to_numpy() for name in field_names},
    )
