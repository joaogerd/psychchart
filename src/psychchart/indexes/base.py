from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Set
import numpy as np


class BaseIndex(ABC):
    """
    Abstract base class for all psychrometric indexes.

    This class defines the unified evaluation interface for both:

        • Domain-based indexes  (continuous grid evaluation)
        • Data-based indexes    (record-level evaluation)

    Subclasses must define:

        - ``name`` (str)
        - ``required_fields`` (set[str])
        - ``compute(context)``

    They MAY override:

        - ``compute_vectorized(context)`` for performance.

    Attributes
    ----------
    name : str
        Unique identifier for the index.

    required_fields : set of str
        Context keys required for computation.
        Example: {"T", "RH"}.

    Notes
    -----
    • Context is a dictionary mapping variable names to values.

    • Values may be:
        - scalars (float)
        - numpy arrays (vectorized evaluation)

    • If numpy arrays are detected, the class will attempt to use
      ``compute_vectorized``. If not implemented, a fallback loop
      may be applied.

    • This abstraction allows unified use in:

        - build_index_field()
        - observation pipelines
        - CLI evaluation
        - future hybrid systems

    Examples
    --------
    Minimal index implementation:

    >>> class SimpleTHI(BaseIndex):
    ...     name = "THI"
    ...     required_fields = {"T", "RH"}
    ...
    ...     @staticmethod
    ...     def compute(context):
    ...         T = context["T"]
    ...         RH = context["RH"]
    ...         return T - (0.55 - 0.0055 * RH) * (T - 14.5)

    Scalar evaluation:

    >>> SimpleTHI.evaluate({"T": 30.0, "RH": 0.7})

    Vectorized evaluation:

    >>> T = np.array([25.0, 30.0])
    >>> RH = np.array([0.6, 0.7])
    >>> SimpleTHI.evaluate({"T": T, "RH": RH})

    See Also
    --------
    build_index_field :
        Builds continuous domain scalar fields.

    FunctionalObservations :
        Observation-based evaluation pipeline.
    """

    name: str = "UnnamedIndex"
    required_fields: Set[str] = set()

    # ------------------------------------------------------------------
    # Context validation
    # ------------------------------------------------------------------
    @classmethod
    def validate_context(cls, context: Dict[str, Any]) -> None:
        """
        Ensure all required fields are present in context.

        Parameters
        ----------
        context : dict
            Input context dictionary.

        Raises
        ------
        ValueError
            If required fields are missing.
        """
        missing = cls.required_fields - context.keys()
        if missing:
            raise ValueError(
                f"Index '{cls.name}' missing required fields: {missing}"
            )

    # ------------------------------------------------------------------
    # Unified evaluation entry point
    # ------------------------------------------------------------------
    @classmethod
    def evaluate(cls, context: Dict[str, Any]):
        """
        Evaluate the index given a context.

        Automatically detects scalar vs. vectorized input.

        Parameters
        ----------
        context : dict
            Dictionary mapping required fields to values.

        Returns
        -------
        float or np.ndarray
            Computed index value(s).
        """
        cls.validate_context(context)

        # Detect array-based evaluation
        sample_value = next(iter(context.values()))

        if isinstance(sample_value, np.ndarray):
            try:
                return cls.compute_vectorized(context)
            except NotImplementedError:
                # Fallback to scalar loop
                return cls._fallback_vectorized(context)

        return cls.compute(context)

    # ------------------------------------------------------------------
    # Scalar computation (mandatory)
    # ------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def compute(context: Dict[str, Any]) -> float:
        """
        Scalar computation of the index.

        Must be implemented by subclasses.

        Parameters
        ----------
        context : dict

        Returns
        -------
        float
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Vectorized computation (optional)
    # ------------------------------------------------------------------
    @staticmethod
    def compute_vectorized(context: Dict[str, Any]):
        """
        Vectorized computation of the index.

        Subclasses SHOULD override this method for performance.

        Raises
        ------
        NotImplementedError
        """
        raise NotImplementedError(
            "Vectorized computation not implemented."
        )

    # ------------------------------------------------------------------
    # Automatic fallback vectorization
    # ------------------------------------------------------------------
    @classmethod
    def _fallback_vectorized(cls, context: Dict[str, Any]):
        """
        Fallback vectorization using scalar compute.

        This method iterates over flattened arrays and applies
        scalar compute element-wise.

        This is slower but guarantees compatibility.
        """
        arrays = {k: np.asarray(v) for k, v in context.items()}
        shape = next(iter(arrays.values())).shape

        flat_results = []

        for i in range(arrays[next(iter(arrays))].size):
            scalar_context = {
                k: v.flatten()[i]
                for k, v in arrays.items()
            }
            flat_results.append(cls.compute(scalar_context))

        return np.array(flat_results).reshape(shape)

