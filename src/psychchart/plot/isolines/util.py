import numpy as np
from typing import Optional, Tuple, Literal

ExitSide = Literal["top", "right", "left"]

def find_curve_exit(
    T_line: np.ndarray,
    W_line: np.ndarray,
    *,
    t_min: Optional[float],
    t_max: Optional[float],
    y_max: Optional[float],
) -> Optional[Tuple[float, float, ExitSide, float]]:
    """
    Find the first point where a (T, W) curve exits the visible
    psychrometric domain.

    Parameters
    ----------
    T_line, W_line : ndarray
        Curve coordinates in psychrometric space.
    t_min : float or None
        Left boundary (e.g. saturation curve proxy or fixed T_min).
    t_max : float or None
        Right boundary (dry-bulb max).
    y_max : float or None
        Top boundary (maximum humidity ratio).

    Returns
    -------
    (T_exit, W_exit, side, angle_deg) or None
        Exit point, boundary side and local curve angle.
    """

    if len(T_line) < 2:
        return None

    for i in range(len(T_line) - 1):
        T0, W0 = T_line[i],   W_line[i+1]
        T1, W1 = T_line[i+1], W_line[i+1]

        T_exit = W_exit = side = None

        # --------------------------------------------------
        # TOP boundary (W = y_max)
        # --------------------------------------------------
        if y_max is not None:
            if (W0 < y_max) and (W1 >= y_max):
                T_exit = np.interp(y_max, [W0, W1], [T0, T1])
                W_exit = y_max
                side = "top"

        # --------------------------------------------------
        # RIGHT boundary (T = t_max)
        # --------------------------------------------------
        if side is None and t_max is not None:
            if (T0 < t_max) and (T1 >= t_max):
                W_exit = np.interp(t_max, [T0, T1], [W0, W1])
                T_exit = t_max
                side = "right"

        # --------------------------------------------------
        # LEFT boundary (T = t_min)
        # --------------------------------------------------
        if side is None and t_min is not None:
            if (T0 > t_min) and (T1 <= t_min):
                W_exit = np.interp(t_min, [T0, T1], [W0, W1])
                T_exit = t_min
                side = "left"

        if side is None:
            continue

        # ângulo local da curva
        dT = T1 - T0
        dW = W1 - W0
        angle = np.degrees(np.arctan2(dW, dT))

        return T_exit, W_exit, side, angle

    return None

