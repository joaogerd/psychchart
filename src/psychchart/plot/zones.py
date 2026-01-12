import numpy as np
from typing import Tuple

from psychchart.psychrometrics import Psychrometrics
from psychchart.config import Zone
from .layers import ZORDER


# =============================================================================
# Internal helper: RH-following polygon
# =============================================================================
def _zone_polygon_rh(
    zone: Zone,
    pressure: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a psychrometric polygon for a rectangular T–RH zone.

    This helper function constructs a **rectangular zone defined in
    (T, RH) space** and converts it into a **closed polygon in
    psychrometric space (T, W)**.

    The rectangle is defined by:
    - a dry-bulb temperature range (T_min, T_max)
    - a relative humidity range (RH_min, RH_max)

    Internally, the rectangle is represented by its four corner
    vertices in (T, RH) space and then passed to
    :func:`_zone_polygon_vertices`, which:
    - interpolates edges appropriately,
    - follows RH curves where applicable,
    - converts all points to humidity ratio (W),
    - returns a closed polygon ready for plotting.

    This function is typically used for **zones that explicitly
    follow relative humidity boundaries**, such as:
    - thermal comfort zones,
    - regulatory envelopes,
    - operational decision regions.

    Parameters
    ----------
    zone : Zone
        Zone configuration object.
        Must define:
        - ``zone.t_range = (T_min, T_max)``
        - ``zone.rh_range = (RH_min, RH_max)``
        where RH values are fractions in the range [0, 1].
    pressure : float
        Atmospheric pressure (Pa) used for psychrometric conversions.

    Returns
    -------
    T_poly : numpy.ndarray
        One-dimensional array of dry-bulb temperature coordinates (°C)
        defining the polygon vertices.
    W_poly : numpy.ndarray
        One-dimensional array of humidity ratio coordinates (kg/kg)
        defining the polygon vertices.

    Notes
    -----
    - The polygon is explicitly closed (first vertex repeated).
    - RH boundaries are treated as **constant RH curves**, not straight
      lines in (T, W) space.
    - No plotting or validation is performed here.
    - This function is a thin convenience wrapper around
      :func:`_zone_polygon_vertices`.

    Design considerations
    ---------------------
    - Defining the zone in (T, RH) space keeps configuration intuitive.
    - Conversion to (T, W) is deferred to ensure physical correctness.
    - This helper exists mainly for clarity and reuse.

    Examples
    --------
    Typical internal usage when drawing RH-following zones:

    >>> zone = Zone(
    ...     name="Comfort zone",
    ...     t_range=(18.0, 26.0),
    ...     rh_range=(0.40, 0.70),
    ...     follow_rh=True,
    ... )
    >>> T_poly, W_poly = _zone_polygon_rh(
    ...     zone,
    ...     pressure=101325,
    ... )
    >>> ax.fill(T_poly, W_poly, alpha=0.3)

    The caller is responsible for:
    - deciding when this helper should be used
      (e.g., ``zone.follow_rh is True``),
    - clipping against saturation if required,
    - managing visual attributes (color, alpha, z-order).
    """

    # ------------------------------------------------------------------
    # Unpack rectangular limits from zone configuration
    # ------------------------------------------------------------------
    t_lo, t_hi = zone.t_range
    rh_lo, rh_hi = zone.rh_range

    # ------------------------------------------------------------------
    # Define rectangle vertices in (T, RH) space
    # ------------------------------------------------------------------
    # Vertex order:
    #   bottom-left  → bottom-right → top-right → top-left → close
    #
    # This ordering guarantees a non-self-intersecting polygon.
    vertices = np.array(
        [
            [t_lo, rh_lo],
            [t_hi, rh_lo],
            [t_hi, rh_hi],
            [t_lo, rh_hi],
            [t_lo, rh_lo],  # explicit closure
        ]
    )

    # ------------------------------------------------------------------
    # Delegate geometry construction to generic helper
    # ------------------------------------------------------------------
    return _zone_polygon_vertices(vertices, pressure)


# =============================================================================
# Internal helper: Polygon from vertices defined
# =============================================================================
def _zone_polygon_vertices(
    vertices: np.ndarray,
    pressure: float,
    n: int = 80,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a psychrometric polygon from vertices defined in (T, RH) space.

    This helper function converts a polygon defined by vertices in
    **dry-bulb temperature (T)** and **relative humidity (RH)** into a
    **closed polygon in psychrometric space (T, W)**, where:

    - T : dry-bulb temperature (°C)
    - RH: relative humidity (0–1)
    - W : humidity ratio (kg_vapor / kg_dry_air)

    Each edge between consecutive vertices is interpreted according
    to its physical meaning:

    Edge interpretation rules
    -------------------------
    For each consecutive pair of vertices (T0, RH0) → (T1, RH1):

    - **Case A – Constant RH (RH0 ≈ RH1)**  
      The edge follows a *relative humidity curve*, which is
      **curvilinear in (T, W) space**.

    - **Case B – Varying RH**  
      The edge is linearly interpolated in *(T, RH)* space and then
      converted pointwise to *(T, W)*.

    This hybrid strategy allows the polygon to represent realistic
    psychrometric regions such as:
    - comfort zones,
    - envelopes bounded by RH curves,
    - design regions defined in T–RH coordinates.

    The resulting polygon is:
    - returned in *(T, W)* space,
    - explicitly closed,
    - suitable for direct use with Matplotlib (``ax.plot``, ``ax.fill``).

    Parameters
    ----------
    vertices : numpy.ndarray
        Array of polygon vertices with shape (N, 2), where each row
        represents ``(T, RH)``.

        Example:
            ``[[18, 0.4], [26, 0.4], [26, 0.7], [18, 0.7]]``

    pressure : float
        Atmospheric pressure (Pa) used for psychrometric conversions.

    n : int, optional
        Number of interpolation points per edge (default: 80).

        Larger values produce smoother curves at the cost of
        computational overhead.

    Returns
    -------
    T_poly : numpy.ndarray
        One-dimensional array of dry-bulb temperature coordinates (°C)
        defining the polygon vertices.
    W_poly : numpy.ndarray
        One-dimensional array of humidity ratio coordinates (kg/kg)
        defining the polygon vertices.

    Notes
    -----
    - Relative humidity values are assumed to be in the range [0, 1].
    - No validation of monotonicity or physical consistency is
      performed here.
    - The polygon is explicitly closed by repeating the first vertex
      if necessary.
    - This function performs **no plotting**.

    Design considerations
    ---------------------
    - Geometry is defined in (T, RH) space, which is intuitive
      for users and configuration.
    - Conversion to (T, W) is deferred until the last possible moment
      to preserve physical meaning.
    - The function is private (prefixed with ``_``) to allow
      refactoring without breaking public APIs.

    Examples
    --------
    Example: RH-following rectangular comfort zone

    >>> vertices = np.array([
    ...     [18.0, 0.40],
    ...     [26.0, 0.40],
    ...     [26.0, 0.70],
    ...     [18.0, 0.70],
    ...     [18.0, 0.40],
    ... ])
    >>> T_poly, W_poly = _zone_polygon_vertices(
    ...     vertices,
    ...     pressure=101325,
    ... )

    The resulting ``T_poly`` and ``W_poly`` can be used directly:

    >>> ax.fill(T_poly, W_poly, alpha=0.3)
    """

    # ------------------------------------------------------------------
    # Containers for concatenated polygon segments
    # ------------------------------------------------------------------
    T_all = []
    W_all = []

    # ------------------------------------------------------------------
    # Iterate over consecutive vertex pairs
    # ------------------------------------------------------------------
    for (T0, RH0), (T1, RH1) in zip(vertices[:-1], vertices[1:]):

        # ==============================================================
        # Case A: Constant relative humidity
        # ==============================================================
        # Physically, this corresponds to following an RH curve,
        # which is nonlinear in (T, W) space.
        if np.isclose(RH0, RH1):
            T_seg = np.linspace(T0, T1, n)
            RH_seg = np.full_like(T_seg, RH0)

        # ==============================================================
        # Case B: Linear edge in (T, RH) space
        # ==============================================================
        # Used when RH varies between vertices.
        else:
            T_seg = np.linspace(T0, T1, n)
            RH_seg = np.linspace(RH0, RH1, n)

        # --------------------------------------------------------------
        # Convert segment from (T, RH) to humidity ratio (W)
        # --------------------------------------------------------------
        W_seg = Psychrometrics.humidity_ratio(
            T_seg,
            RH_seg,
            pressure,
        )

        # Accumulate segment
        T_all.append(T_seg)
        W_all.append(W_seg)

    # ------------------------------------------------------------------
    # Concatenate all segments into a single polygon
    # ------------------------------------------------------------------
    T_poly = np.concatenate(T_all)
    W_poly = np.concatenate(W_all)

    # ------------------------------------------------------------------
    # Explicit polygon closure (safety)
    # ------------------------------------------------------------------
    if (
        not np.isclose(T_poly[0], T_poly[-1])
        or not np.isclose(W_poly[0], W_poly[-1])
    ):
        T_poly = np.append(T_poly, T_poly[0])
        W_poly = np.append(W_poly, W_poly[0])

    return T_poly, W_poly

# =============================================================================
# Public zone drawing dispatcher
# =============================================================================
def draw_zones(ax, chart) -> None:
    """
    Draw all geometric zones defined in the chart configuration.

    This function iterates over all ``Zone`` objects and renders
    them according to their geometric definition:

    Supported zone definitions
    --------------------------
    1. Explicit polygon vertices
    2. RH-following polygon (curvilinear)
    3. Rectangular zone in T–RH space

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes where zones will be drawn.
    chart : PsychChart
        Chart object providing:
        - zone definitions
        - global configuration
        - atmospheric pressure

    Notes
    -----
    - This function performs **geometry construction**, not validation.
    - Saturation clipping must be handled elsewhere if required.
    - Z-order and legend handling are minimal by design.
    """

    # --------------------------------------------------------------
    # Iterate over all defined zones in the chart configuration
    #
    # Each zone can be defined in different ways, depending on the
    # desired geometric and physical complexity:
    #
    #   1) Explicit polygon vertices in (T, RH) space
    #   2) Curvilinear zone bounded by relative humidity curves
    #   3) Simple rectangular zone in (T, RH) space
    #
    # All cases must ultimately produce a CLOSED polygon in
    # psychrometric space (T, W), suitable for plotting and filling.
    # --------------------------------------------------------------
    for z in chart.zones:
    
        # ==========================================================
        # Case 1: Explicit polygon defined by vertices in (T, RH)
        # ==========================================================
        #
        # This is the most general and flexible definition.
        #
        # - The geometry is explicitly defined in (T, RH) space,
        #   which is intuitive for users and configuration files.
        # - Each edge of the polygon is interpreted physically:
        #     * constant RH  -> follows a psychrometric RH curve
        #     * varying RH   -> linear interpolation in (T, RH)
        # - Conversion to (T, W) is performed only after edge
        #   interpretation, ensuring physical correctness.
        #
        # This approach supports:
        # - arbitrary polygon shapes,
        # - zones from literature,
        # - inclined envelopes,
        # - future index-based or adaptive zones.
        #
        if z.vertices:
            # Convert user-provided vertices to a NumPy array.
            # Expected shape: (N, 2), with columns (T, RH).
            verts = np.asarray(z.vertices)
    
            # Build a physically consistent polygon in (T, W) space.
            # The helper:
            # - walks edge by edge,
            # - applies the appropriate interpolation rule,
            # - ensures explicit polygon closure.
            t_poly, w_poly = _zone_polygon_vertices(
                verts,
                chart.cfg.pressure,
            )
    
        # ==========================================================
        # Case 2: Curvilinear zone following RH boundaries
        # ==========================================================
        #
        # This is a specialized but common case, representing zones
        # bounded by two relative humidity curves between two
        # temperature limits.
        #
        # - Geometry is implicitly defined by:
        #     * T ∈ [T_min, T_max]
        #     * RH ∈ [RH_min, RH_max]
        # - Both lower and upper boundaries follow true RH curves,
        #   which are nonlinear in (T, W) space.
        # - The polygon is constructed in a consistent orientation
        #   and explicitly closed.
        #
        # Internally, this case can be seen as a convenience wrapper
        # around the general polygon logic.
        #
        elif z.follow_rh and z.t_range and z.rh_range:
            t_poly, w_poly = _zone_polygon_rh(
                z,
                chart.cfg.pressure,
            )
    
        # ==========================================================
        # Case 3: Simple rectangular zone in (T, RH) space
        # ==========================================================
        #
        # This is the simplest and least flexible definition.
        #
        # - The zone is a rectangle in (T, RH) space.
        # - The four corners are converted directly to (T, W).
        # - Polygon edges are straight lines in (T, W) space,
        #   which is a reasonable approximation for simple or
        #   illustrative zones.
        #
        # This case exists mainly for:
        # - backward compatibility,
        # - quick prototyping,
        # - very simple comfort envelopes.
        #
        elif z.t_range and z.rh_range:
            t_lo, t_hi = z.t_range
            rh_lo, rh_hi = z.rh_range
    
            # Explicitly define rectangle corners in clockwise order
            # and repeat the first point to ensure closure.
            t_poly = [t_lo, t_hi, t_hi, t_lo, t_lo]
            w_poly = [
                Psychrometrics.humidity_ratio(
                    t_lo, rh_lo, chart.cfg.pressure
                ),
                Psychrometrics.humidity_ratio(
                    t_hi, rh_lo, chart.cfg.pressure
                ),
                Psychrometrics.humidity_ratio(
                    t_hi, rh_hi, chart.cfg.pressure
                ),
                Psychrometrics.humidity_ratio(
                    t_lo, rh_hi, chart.cfg.pressure
                ),
                Psychrometrics.humidity_ratio(
                    t_lo, rh_lo, chart.cfg.pressure
                ),
            ]
    
        # ==========================================================
        # Invalid or incomplete zone definition
        # ==========================================================
        #
        # If none of the valid definitions applies, the zone cannot
        # be rendered safely or consistently.
        #
        # Failing early here prevents silent errors and ensures that
        # invalid configurations are detected during development.
        #
        else:
            raise ValueError(
                f"Zone '{z.name}' is ill-defined and cannot be rendered."
            )


        # ----------------------------------------------------------
        # Draw zone boundary
        # ----------------------------------------------------------
        ax.plot(
            t_poly,
            w_poly,
            lw=z.linewidth,
            color=z.edgecolor,
            label=z.name,
            zorder=ZORDER['zone_edge'],
        )

        # ----------------------------------------------------------
        # Fill zone interior (optional)
        # ----------------------------------------------------------
        if z.facecolor and z.facecolor.lower() != "none":
            ax.fill(
                t_poly,
                w_poly,
                facecolor=z.facecolor,
                alpha=0.20,
                zorder=ZORDER['zone_fill'],
            )

