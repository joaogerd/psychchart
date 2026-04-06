from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .base import BaseIndex


class HLI(BaseIndex):
    """
    Heat Load Index (HLI).

    Implements the piecewise HLI formulation using black globe temperature (BG),
    relative humidity (RH) and wind speed (WS).

    Formula
    -------
    Let:
      BG : black globe temperature (°C)
      RH : relative humidity (%)
      WS : wind speed (m/s)

    If BG >= 25:
        HLI = 8.62 + (0.38 * RH) + (1.55 * BG) + exp(2.4 - WS) - (0.5 * WS)

    If BG < 25:
        HLI = 10.66 + (0.28 * RH) + (1.30 * BG) - WS

    Inputs
    ------
    Supported input modes:

    1) Measured globe temperature:
       context must include: {"BG", "RH", "wind"}

    2) Estimated globe temperature from dry-bulb temperature and solar radiation:
       context must include: {"T", "SR", "RH", "wind"}

    3) Fallback estimated globe temperature from dry-bulb temperature only:
       context must include: {"T", "RH", "wind"}

       BG = 1.33*T - 2.65*sqrt(T)

       If T < 0 °C, BG is undefined in this fallback and NaN is returned.

    Conventions
    -----------
    - RH must be provided as a fraction in the range [0, 1].
      It is internally converted to percentage.
    - wind must be provided in m/s.
    - SR is expected to represent solar radiation.
    - BG and T are expected in °C.

    Notes
    -----
    - When BG is measured, it is always preferred over estimated BG.
    - The BG estimator using SR is a simplified approximation and should be
      validated for operational use.
    """

    name = "HLI"
    required_fields = {"RH", "wind"}

    @staticmethod
    def _rh_fraction_to_percent(rh: np.ndarray | float) -> np.ndarray:
        """
        Convert RH from fraction [0, 1] to percentage [0, 100].
        """
        rh = np.asarray(rh, dtype=float)
        return rh * 100.0

    @staticmethod
    def _bg_from_t(T: np.ndarray) -> np.ndarray:
        """
        Estimate black globe temperature from dry-bulb temperature only.

        BG = 1.33*T - 2.65*sqrt(T)

        Returns NaN where T < 0.
        """
        T = np.asarray(T, dtype=float)
        BG = np.full_like(T, np.nan, dtype=float)

        valid = T >= 0.0
        BG[valid] = 1.33 * T[valid] - 2.65 * np.sqrt(T[valid])

        return BG

    @staticmethod
    def _estimate_bg(
        T: np.ndarray,
        wind: np.ndarray,
        solar: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Estimate black globe temperature (BG).

        If solar radiation is available, use a simplified approximation based on
        temperature, radiation and wind. Otherwise, fall back to the empirical
        temperature-only estimator.
        """
        T = np.asarray(T, dtype=float)
        wind = np.asarray(wind, dtype=float)

        if solar is not None:
            solar = np.asarray(solar, dtype=float)
            return T + 0.0121 * solar - 0.021 * wind + 0.544

        return HLI._bg_from_t(T)

    @staticmethod
    def _resolve_bg_scalar(context: Dict[str, Any], ws: float) -> float:
        """
        Resolve scalar BG from context, preferring measured BG.
        """
        if "BG" in context:
            return float(context["BG"])

        if "T" not in context:
            raise ValueError("HLI requires either 'BG' or 'T' in context.")

        T = float(context["T"])

        if "SR" in context:
            SR = float(context["SR"])
            return float(HLI._estimate_bg(np.array([T]), np.array([ws]), np.array([SR]))[0])

        return float(HLI._bg_from_t(np.array([T]))[0])

    @staticmethod
    def _resolve_bg_vectorized(context: Dict[str, np.ndarray], ws: np.ndarray) -> np.ndarray:
        """
        Resolve vectorized BG from context, preferring measured BG.
        """
        if "BG" in context:
            return np.asarray(context["BG"], dtype=float)

        if "T" not in context:
            raise ValueError("HLI requires either 'BG' or 'T' in context (vectorized).")

        T = np.asarray(context["T"], dtype=float)

        if "SR" in context:
            SR = np.asarray(context["SR"], dtype=float)
            return HLI._estimate_bg(T, ws, SR)

        return HLI._bg_from_t(T)

    @staticmethod
    def compute(context: Dict[str, Any]) -> float:
        """
        Compute scalar HLI from a context dictionary.
        """
        rh = HLI._rh_fraction_to_percent(float(context["RH"]))
        ws = float(context["wind"])
        bg = HLI._resolve_bg_scalar(context, ws)

        if np.isnan(bg):
            return float("nan")

        if bg >= 25.0:
            hli = 8.62 + (0.38 * rh) + (1.55 * bg) + np.exp(2.4 - ws) - (0.5 * ws)
        else:
            hli = 10.66 + (0.28 * rh) + (1.30 * bg) - ws

        return float(hli)

    @staticmethod
    def compute_vectorized(context: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute vectorized HLI from array-like context fields.
        """
        rh = HLI._rh_fraction_to_percent(np.asarray(context["RH"], dtype=float))
        ws = np.asarray(context["wind"], dtype=float)
        bg = HLI._resolve_bg_vectorized(context, ws)

        hli_hi = 8.62 + (0.38 * rh) + (1.55 * bg) + np.exp(2.4 - ws) - (0.5 * ws)
        hli_lo = 10.66 + (0.28 * rh) + (1.30 * bg) - ws

        return np.where(bg >= 25.0, hli_hi, hli_lo)
