from __future__ import annotations

from typing import Any, Dict, List, Mapping, Type
import numpy as np

from psychchart.indexes.base import BaseIndex


class IndexEngine:
    """
    Index evaluation engine.

    This engine evaluates BaseIndex subclasses over:
    - 2D grids (T_grid, RH_grid) with optional extra context
    - lists of record contexts

    Vectorization strategy
    ----------------------
    If the index class provides a `compute_vectorized(context)` method,
    it will be used for fast array evaluation.

    Otherwise, the engine falls back to the safe scalar path:
        cls.evaluate(context)  # validation + compute per point

    Domain Rule
    -----------
    Grid evaluation is only permitted for indices that depend on
    thermodynamic variables {"T", "RH"}.

    This enforces architectural consistency:

    ✔ ITU  -> allowed on grid
    ✔ HLI  -> allowed on grid
    ✘ ICF  -> blocked on grid (behavior-only index)
    ✔ ICF  -> allowed on records
    Notes
    -----
    - `extra_context` can contain scalars or arrays.
    - If arrays are provided in `extra_context`, they must match the grid shape.
    - Scalars are automatically broadcast to the grid shape.
    - If an index implements `compute_vectorized`, it will be used.
      Otherwise, evaluation falls back to scalar evaluation.
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _as_2d_float(arr: Any, name: str) -> np.ndarray:
        """Convert input to 2D float ndarray."""
        a = np.asarray(arr, dtype=float)
        if a.ndim != 2:
            raise ValueError(f"{name} must be a 2D array, got shape {a.shape}.")
        return a

    @staticmethod
    def _broadcast_or_validate(value: Any, shape: tuple[int, int], key: str) -> np.ndarray:
        """
        Convert value into a 2D array matching `shape`.

        - scalars -> broadcast
        - 2D arrays -> must match shape
        """
        a = np.asarray(value, dtype=float)

        # Scalar -> broadcast
        if a.ndim == 0:
            return np.full(shape, float(a), dtype=float)

        # Already 2D -> validate shape
        if a.ndim == 2:
            if a.shape != shape:
                raise ValueError(
                    f"extra_context['{key}'] shape {a.shape} does not match grid shape {shape}."
                )
            return a.astype(float, copy=False)

        raise ValueError(
            f"extra_context['{key}'] must be scalar or 2D array, got ndim={a.ndim}."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @staticmethod
    def evaluate_on_grid(
        index_cls: Type[BaseIndex],
        T_grid: Any,
        RH_grid: Any,
        extra_context: Dict[str, Any] | None = None,
    ) -> np.ndarray:
        """
        Evaluate an index over a 2D thermodynamic grid.

        Parameters
        ----------
        index_cls
            A BaseIndex subclass (e.g., ITU, ICF, HLI).
        T_grid
            2D temperature array (°C).
        RH_grid
            2D relative humidity array (%).
        extra_context
            Optional dict of extra inputs (scalars or 2D arrays).

        Returns
        -------
        np.ndarray
            2D array of computed index values.
        """
        T = IndexEngine._as_2d_float(T_grid, "T_grid")
        RH = IndexEngine._as_2d_float(RH_grid, "RH_grid")

        if T.shape != RH.shape:
            raise ValueError(f"T_grid shape {T.shape} must match RH_grid shape {RH.shape}.")

        shape = T.shape

        # Build a vector context (all keys -> 2D arrays)
        ctx_vec: Dict[str, np.ndarray] = {
            "T": T,
            "RH": RH,
        }

        if extra_context:
            for k, v in extra_context.items():
                ctx_vec[k] = IndexEngine._broadcast_or_validate(v, shape, k)

        # --------------------------------------------------------------
        # Fast path: vectorized index
        # --------------------------------------------------------------
        compute_vec = getattr(index_cls, "compute_vectorized", None)
        if callable(compute_vec):
            # Validation here only checks presence of keys (not values).
            # For vectorized evaluation, that's enough to catch config errors early.
            index_cls.validate_context(ctx_vec)  # type: ignore[arg-type]
            out = compute_vec(ctx_vec)  # expects ndarray output
            out = np.asarray(out, dtype=float)
            if out.shape != shape:
                raise ValueError(
                    f"{index_cls.__name__}.compute_vectorized returned shape {out.shape}, expected {shape}."
                )
            return out

        # --------------------------------------------------------------
        # Safe path: scalar evaluation per cell (slower)
        # --------------------------------------------------------------
        result = np.empty(shape, dtype=float)
        for i in range(shape[0]):
            for j in range(shape[1]):
                ctx = {k: float(v[i, j]) for k, v in ctx_vec.items()}
                result[i, j] = index_cls.evaluate(ctx)
        return result

    @staticmethod
    def evaluate_on_records(
        index_cls: Type[BaseIndex],
        records: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Evaluate an index over a list of record contexts.

        Notes
        -----
        Record evaluation is typically small/medium sized and kept simple.
        If later you want, we can add a `compute_vectorized_records` protocol.
        """
        if not records:
            return np.array([], dtype=float)

        values = np.empty(len(records), dtype=float)
        for i, r in enumerate(records):
            values[i] = index_cls.evaluate(r)
        return values

