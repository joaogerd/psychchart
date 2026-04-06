from __future__ import annotations

import numpy as np
from matplotlib.path import Path
from matplotlib.patches import PathPatch


def clip_to_saturation(ax, artist, T, W_sat):
    """
    Clip a Matplotlib artist to the saturation curve (100% relative humidity).

    This helper function restricts the visible region of a Matplotlib
    artist (e.g., a heatmap, contour field, or filled polygon) to the
    **physically admissible region** of the psychrometric chart,
    i.e. the area *below* the saturation curve (RH = 100%).

    From a physical standpoint, any state above the saturation curve
    represents supersaturation and is therefore not meaningful for
    standard psychrometric analysis.

    From a visualization standpoint, clipping:
    - prevents misleading colors or contours above saturation,
    - reinforces the physical interpretation of the chart,
    - improves visual clarity and scientific correctness.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes instance to which the artist belongs.
        The axes transform is required so clipping is performed
        in **data coordinates**, not in display coordinates.
    artist : matplotlib.artist.Artist
        Any Matplotlib artist supporting ``set_clip_path``, such as:
        - QuadMesh (returned by ``pcolormesh``)
        - PolyCollection (used internally by ``contourf``)
        - Patch or Collection objects
    T : numpy.ndarray
        One-dimensional array of dry-bulb temperature values.
        Unit: degrees Celsius [°C].

        This array defines the x-coordinates of the saturation curve.
    W_sat : numpy.ndarray
        One-dimensional array of saturation humidity ratio values.
        Unit: kg/kg.

        Must correspond point-by-point to ``T``.

    Notes
    -----
    - The clipping polygon is constructed explicitly in data coordinates.
    - The visible region is defined as:
        * W >= 0 (chart baseline)
        * W <= W_sat(T) (saturation curve)
    - The saturation curve itself is **not altered** by this function.
    - This function does not validate array consistency
      (shape, monotonicity, or physical bounds).
      Validation must be handled by the caller.
    - The artist data are not modified; only its visible region is clipped.

    Design considerations
    ---------------------
    - The polygon is explicitly closed to ensure correct clipping behavior.
    - The saturation curve is traversed left-to-right.
    - The lower boundary (W = 0) is traversed right-to-left.
    - The function is intentionally low-level and imperative.
    - Placed in ``plot.utils`` to avoid circular dependencies
      with zones, indexes, or chart orchestration logic.

    Examples
    --------
    Clipping a continuous index field created with ``pcolormesh``:

    >>> cs = ax.pcolormesh(TT, WW, Z, cmap="inferno")
    >>> clip_to_saturation(ax, cs, chart.T, chart.W_sat)

    Clipping a filled contour plot:

    >>> cs = ax.contourf(TT, WW, Z, levels=20)
    >>> for coll in cs.collections:
    ...     clip_to_saturation(ax, coll, chart.T, chart.W_sat)

    Typical usage inside the PsychChart rendering pipeline:

    >>> cs = ax.contourf(...)
    >>> clip_to_saturation(self.ax, cs, self.T, self.W_sat)
    """

    # ------------------------------------------------------------------
    # Build clipping polygon vertices
    # ------------------------------------------------------------------
    # Polygon definition:
    #   1) Follow the saturation curve from Tmin to Tmax
    #   2) Return along the baseline W = 0 from Tmax to Tmin
    #
    # This encloses the physically valid region of the chart.
    verts = np.column_stack([
        np.concatenate([T, T[::-1]]),                  # x-coordinates (T)
        np.concatenate([W_sat, np.zeros_like(W_sat)]), # y-coordinates (W)
    ])

    # ------------------------------------------------------------------
    # Path codes
    # ------------------------------------------------------------------
    # MOVETO : start polygon at first saturation point
    # LINETO : draw saturation curve
    # LINETO : draw baseline back to start
    codes = np.concatenate([
        [Path.MOVETO],
        np.full(len(T) - 1, Path.LINETO),
        np.full(len(T), Path.LINETO),
    ])

    # ------------------------------------------------------------------
    # Create clipping path and patch
    # ------------------------------------------------------------------
    path = Path(verts, codes)

    # Ensure clipping is applied in data coordinates
    patch = PathPatch(path, transform=ax.transData)

    # ------------------------------------------------------------------
    # Apply clipping to the artist
    # ------------------------------------------------------------------
    artist.set_clip_path(patch)

def debug_array_stats(name: str, arr: np.ndarray) -> None:
    """Print a compact statistical summary for a NumPy array."""
    arr = np.asarray(arr)

    finite_mask = np.isfinite(arr)
    finite_values = arr[finite_mask]

    print(f"\n[DEBUG] Array: {name}")
    print(f"  shape        : {arr.shape}")
    print(f"  dtype        : {arr.dtype}")
    print(f"  size         : {arr.size}")
    print(f"  nan_count    : {np.isnan(arr).sum()}")
    print(f"  inf_count    : {np.isinf(arr).sum()}")
    print(f"  finite_count : {finite_values.size}")

    if finite_values.size == 0:
        print("  min          : <no finite values>")
        print("  max          : <no finite values>")
        print("  mean         : <no finite values>")
        print("  std          : <no finite values>")
        return

    print(f"  min          : {finite_values.min()}")
    print(f"  max          : {finite_values.max()}")
    print(f"  mean         : {finite_values.mean()}")
    print(f"  std          : {finite_values.std()}")
    print(f"  p01          : {np.percentile(finite_values, 1)}")
    print(f"  p05          : {np.percentile(finite_values, 5)}")
    print(f"  p50          : {np.percentile(finite_values, 50)}")
    print(f"  p95          : {np.percentile(finite_values, 95)}")
    print(f"  p99          : {np.percentile(finite_values, 99)}")
