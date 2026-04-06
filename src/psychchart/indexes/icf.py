from __future__ import annotations
from typing import Dict, Any
import numpy as np
from .base import BaseIndex


class ICF(BaseIndex):
    """
    Functional Comfort Index (ICF).

    Overview
    --------
    The Functional Comfort Index (ICF) is a dimensionless behavioral
    index that quantifies the balance between comfort-related and
    stress-related activities.

    Mathematical Definition
    ------------------------
    The index is defined as:

        ICF = rumination /
              (rumination + panting)

    where:

        rumination : scalar intensity of rumination behavior
        panting    : scalar intensity of panting behavior

    Interpretation
    --------------
    - ICF → 1.0 : animal predominantly engaged in comfort behaviors
    - ICF → 0.0 : animal predominantly engaged in heat-stress behavior
    - ICF = NaN : undefined (no behavioral activity recorded)

    Properties
    ----------
    - Dimensionless
    - Bounded in [0, 1]
    - Scale-invariant (homogeneous of degree 0)

    Context Requirements
    --------------------
    Required keys:

        { "rumination", "panting"}

    All values must be numeric and non-negative.

    Notes
    -----
    - If denominator == 0, NaN is returned.
    - No clipping is applied.
    - No normalization is performed here.
    - Behavioral preprocessing belongs to data layer.
    """

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    name = "ICF"
    required_fields = {"rumination", "panting"}

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    @staticmethod
    def compute(context: Dict[str, Any]) -> float:
        """
        Compute ICF from behavioral components.

        Parameters
        ----------
        context : dict
            Must contain:
                - "rumination"
                - "panting"

        Returns
        -------
        float
            ICF value in [0, 1] or NaN if undefined.
        """

        # --------------------------------------------------------------
        # Extract and cast inputs
        # --------------------------------------------------------------
        rumination = float(context["rumination"])
        panting = float(context["panting"])

        # Optional scientific safeguard (recommended)
        if rumination < 0 or panting < 0:
            raise ValueError("Behavioral components must be non-negative.")

        # --------------------------------------------------------------
        # Core formula
        # --------------------------------------------------------------
        numerator =  rumination
        denominator =  rumination + panting

        # Scientifically correct handling of null activity
        if denominator == 0:
            return np.nan

        icf = numerator / denominator

        # Numerical safety (floating rounding)
        return float(icf)
    
    @staticmethod
    def compute_vectorized(context: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Vectorized ICF over arrays.

        Parameters
        ----------
        context : dict[str, ndarray]
            Must contain 2D arrays:
            - "rumination"
            - "panting"tests/test_plot_smoke.py

        Returns
        -------
        ndarray
            2D ICF field (NaN where denominator == 0).
        """
        rumination = np.asarray(context["rumination"], dtype=float)
        panting = np.asarray(context["panting"], dtype=float)

        if np.any(rumination < 0) or np.any(panting < 0):
            raise ValueError("Behavioral components must be non-negative.")

        num = rumination
        den = num + panting

        # NaN where undefined
        return np.where(den == 0.0, np.nan, num / den)
