import numpy as np
from psychchart.psychrometrics import Psychrometrics

def draw_relative_humidity(ax, T, W_sat, cfg, st):
    """
    Draw constant relative-humidity (RH = const) isolines on a
    psychrometric chart.

    Thermodynamic background
    ------------------------
    Relative humidity (RH) is defined as the ratio between the actual
    partial pressure of water vapor and the saturation vapor pressure
    at the same temperature:

        RH = p_v / p_vs(T)

    For a given dry-bulb temperature ``T`` and fixed relative humidity
    value ``RH``, the corresponding humidity ratio ``W`` is obtained
    from standard psychrometric relations:

        W(T, RH) = f(T, RH, p)

    where ``p`` is the ambient pressure.

    Unlike enthalpy isolines, relative humidity isolines are *not*
    straight lines in the T–W plane and do not generally require
    explicit intersection detection with the saturation curve, since
    the saturation curve itself corresponds to RH = 100%.

    Physical domain
    ---------------
    For any relative humidity value ``0 < RH <= 1``, the computed
    humidity ratio satisfies:

        0 <= W(T, RH) <= W_sat(T)

    provided the underlying psychrometric formulation is physically
    consistent.

    As a result, relative humidity isolines lie entirely within the
    physically admissible region of the psychrometric chart and do not
    require explicit clipping or intersection handling at this stage.

    Scope and responsibility
    ------------------------
    This function is responsible solely for:
        - evaluating the RH isolines over the temperature domain,
        - rendering them on the provided Matplotlib axes,
        - returning their geometric representation for downstream use
          (e.g., labeling).

    It explicitly does NOT:
        - perform masking or clipping against chart limits,
        - enforce axis bounds,
        - position or rotate labels,
        - validate the temperature domain.

    Any further clipping or semantic processing is expected to be
    handled by higher-level orchestration logic.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes for plotting.
    T : ndarray
        Dry-bulb temperature array (°C).
    W_sat : ndarray
        Saturation humidity ratio evaluated at ``T``.
        Included for API consistency; not explicitly used here.
    cfg : ChartConfig
        Global chart configuration, including pressure.
    st : dict
        Style and configuration dictionary defining the isoline family.
        Expected keys include:
            - ``values`` : iterable of RH values (0–1)
            - ``color`` : line color
            - ``linewidth`` : line width
            - ``linestyle`` : Matplotlib line style
            - ``zorder`` : drawing order

    Returns
    -------
    dict[float, tuple[np.ndarray, np.ndarray]]
        Mapping from relative humidity value ``RH`` to its isoline
        geometry ``(T, W)``, where ``T`` and ``W`` are arrays of equal
        length representing the curve in data coordinates.

    Notes
    -----
    - The saturation curve itself corresponds to RH = 1 and is typically
      rendered separately.
    - No attempt is made here to truncate isolines at the saturation
      boundary or chart limits; this behavior is intentional.
    - The returned geometries preserve the full temperature domain
      provided by ``T``.

    See Also
    --------
    draw_enthalpy
        Computes and clips enthalpy isolines with explicit intersection
        handling at the saturation curve.
    label_relative_humidity
        Places RH labels using the geometry returned by this function.
    """

    geometries = {}
    for rh in st["values"]:
        # Compute humidity ratio for given RH across all temperatures
        w = Psychrometrics.humidity_ratio(T, rh, cfg.pressure)

        ax.plot(
            T,
            w,
            color=st["color"],
            lw=st["linewidth"],
            linestyle=st["linestyle"],
            alpha=st["alpha"],
            zorder=st["zorder"],
        )

        geometries[rh] = (T,w)
        
    return geometries


def draw_enthalpy(ax, T, W_sat, cfg, st):
    """
    Draw constant-enthalpy (h = const) isolines on a psychrometric chart,
    ensuring physically correct termination at the saturation curve.

    Thermodynamic background
    ------------------------
    The specific enthalpy of moist air (per unit mass of dry air) is given by:

        h = c_p * T + W * (h_fg + c_pv * T)

    where:
        T     : dry-bulb temperature (°C)
        W     : humidity ratio (kg_vapor / kg_dry_air)
        c_p   : specific heat of dry air at constant pressure
        c_pv  : specific heat of water vapor at constant pressure
        h_fg  : latent heat of vaporization of water

    For a fixed enthalpy value h, this relation can be inverted to obtain
    the equation of an enthalpy isoline in the T–W plane:

        W_h(T) = (h - c_p * T) / (h_fg + c_pv * T)

    This equation defines a straight line in (T, W) coordinates.

    Physical domain of validity
    ----------------------------
    Not all points of the line W_h(T) represent physically admissible
    thermodynamic states. For moist air at equilibrium, the following
    constraints must be satisfied:

        1) W >= 0
        2) W <= W_sat(T)

    where W_sat(T) is the saturation humidity ratio at temperature T.

    Points where W_h(T) > W_sat(T) correspond to supersaturated states,
    which are thermodynamically unstable and therefore excluded from
    the psychrometric chart.

    Intersection with the saturation curve
    ---------------------------------------
    For many enthalpy values, the enthalpy isoline lies above the saturation
    curve at low temperatures (supersaturated region), intersects the
    saturation curve at a specific temperature T*, and only then enters
    the physically admissible sub-saturated region.

    The intersection condition is:

        W_h(T*) = W_sat(T*)

    Numerically, this is detected by a sign change of:

        diff(T) = W_h(T) - W_sat(T)

    from positive (supersaturated) to negative (sub-saturated).

    To ensure thermodynamic and geometric correctness of the chart,
    the isoline must:
        - start exactly at the intersection point (T*, W_sat(T*)),
        - and be plotted only within the physically admissible region
          0 <= W <= W_sat(T).

    Simply masking points where W_h(T) <= W_sat(T) is insufficient,
    because it removes the exact intersection point and causes the
    isoline to appear disconnected from the saturation curve.

    Numerical treatment
    -------------------
    This function therefore:
        1) Computes W_h(T) over the temperature domain,
        2) Detects the first crossing of W_h(T) with W_sat(T),
        3) Linearly interpolates the exact intersection point,
        4) Prepends this point to the physically admissible segment
           of the isoline,
        5) Plots the resulting curve.

    This guarantees that each enthalpy isoline:
        - touches the saturation curve exactly when a physical
          intersection exists within the temperature domain,
        - never enters the supersaturated region,
        - reproduces the classical appearance of psychrometric
          charts as found in ASHRAE and Mollier diagrams.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes for plotting.
    T : ndarray
        Dry-bulb temperature array (°C).
    W_sat : ndarray
        Saturation humidity ratio evaluated at T.
    cfg : ChartConfig
        Global chart configuration.
    st : dict
        Dictionary defining isoline values and plotting style
        (e.g., enthalpy levels, color, linewidth, linestyle).

    Notes
    -----
    - Not all enthalpy values necessarily intersect the saturation
      curve within the chosen temperature range. In such cases,
      only the physically admissible portion (if any) is plotted.
    - This behavior is thermodynamically correct and should not
      be interpreted as a plotting error.
    """
    """
    Draw enthalpy isolines (h = const), forcing the LEFT end to touch
    the saturation curve when a crossing exists inside the T-domain.

    Physically admissible region: 0 <= W <= W_sat.
    """

    geometries = {}

    for h in st["values"]:
        W_line = (h - Psychrometrics.cp * T) / (
            Psychrometrics.Hfg + Psychrometrics.cp_v * T
        )

        # Consider only where W is non-negative (otherwise not physical)
        mask_wpos = (W_line >= 0)
        if not np.any(mask_wpos):
            continue

        T0 = T[mask_wpos]
        W0 = W_line[mask_wpos]
        Ws0 = W_sat[mask_wpos]

        diff = W0 - Ws0  # >0 supersaturated, <0 sub-saturated

        # Find first crossing from + to - (touching saturation entering the physical region)
        cross = np.where((diff[:-1] > 0) & (diff[1:] <= 0))[0]

        if len(cross) == 0:
            # Two possibilities:
            # (a) already fully below saturation (diff<=0) -> just plot the physical part
            # (b) fully above saturation (diff>0) -> no physical segment in this domain
            if np.all(diff > 0):
                continue  # never enters sub-saturated region
            else:
                # already sub-saturated where W>=0, plot where W<=Ws
                mask_phys = (W0 <= Ws0)
                T_plot = T0[mask_phys]
                W_plot = W0[mask_phys]
                if len(T_plot) < 2:
                    continue
        else:
            i = cross[0]

            # Linear interpolation for intersection T* where diff(T*)=0
            T1, T2 = T0[i], T0[i + 1]
            d1, d2 = diff[i], diff[i + 1]
            T_int = T1 - d1 * (T2 - T1) / (d2 - d1)

            # Interpolate W on the enthalpy line at T_int
            W_int = np.interp(T_int, T0, W0)

            # Now take the sub-saturated branch from i+1 onward (diff<=0),
            # and prepend the intersection point.
            mask_after = (np.arange(len(T0)) >= (i + 1)) & (W0 <= Ws0)
            T_tail = T0[mask_after]
            W_tail = W0[mask_after]

            if len(T_tail) == 0:
                # edge case: intersection happens at the last interval
                T_plot = np.array([T_int])
                W_plot = np.array([W_int])
            else:
                T_plot = np.concatenate(([T_int], T_tail))
                W_plot = np.concatenate(([W_int], W_tail))

        ax.plot(
            T_plot,
            W_plot,
            color=st["color"],
            lw=st["linewidth"],
            linestyle=st["linestyle"],
            alpha=st["alpha"],
            zorder=st["zorder"],
        )

        

        geometries[h] = (T_plot, W_plot)

    return geometries

def draw_wet_bulb(ax, T, W_sat, cfg, st):
    """
    Draw wet-bulb temperature isolines (Twb = const).

    Wet-bulb isolines are computed by:
    1. computing saturation humidity ratio at Twb,
    2. computing corresponding enthalpy,
    3. projecting that enthalpy across the temperature range.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes for plotting.
    T : ndarray
        Dry-bulb temperature array (°C).
    W_sat : ndarray
        Saturation humidity ratio curve.
    cfg : ChartConfig
        Global chart configuration.
    st : dict
        Resolved isoline style and behavior dictionary.

    Notes
    -----
    Wet-bulb isolines are enthalpy-equivalent lines passing through
    the saturation point at ``Twb``.
    """

    for twb in st["values"]:
        # Saturation humidity ratio at wet-bulb temperature
        W_sat_wb = Psychrometrics.humidity_ratio(twb, 1.0, cfg.pressure)

        # Enthalpy at wet-bulb saturation point
        h_wb = Psychrometrics.enthalpy(twb, W_sat_wb)

        # Project enthalpy line across temperature domain
        W_line = (h_wb - Psychrometrics.cp * T) / (
            Psychrometrics.Hfg + Psychrometrics.cp_v * T
        )

        mask = (W_line > 0) & (W_line < W_sat)

        ax.plot(
            T[mask],
            W_line[mask],
            color=st["color"],
            lw=st["linewidth"],
            linestyle=st["linestyle"],
            alpha=st["alpha"],
            zorder=st["zorder"],
        )


def draw_specific_volume(ax, T, W_sat, cfg, st):
    """
    Draw specific volume isolines (v = const).

    Specific volume isolines represent constant moist-air
    specific volume (m³/kg of dry air).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes for plotting.
    T : ndarray
        Dry-bulb temperature array (°C).
    W_sat : ndarray
        Saturation humidity ratio curve.
    cfg : ChartConfig
        Global chart configuration.
    st : dict
        Resolved isoline style and behavior dictionary.

    Notes
    -----
    The formulation used is derived from the equation of state:

    v = R_d * T_K * (1 + 1.6078 W) / p

    Solved here for W.
    """

    T_K = T + 273.15  # Convert to Kelvin

    for v in st["values"]:
        W_line = (
            v * cfg.pressure / (Psychrometrics.Rd * T_K) - 1
        ) / 1.6078

        mask = (W_line > 0) & (W_line < W_sat)

        ax.plot(
            T[mask],
            W_line[mask],
            color=st["color"],
            lw=st["linewidth"],
            linestyle=st["linestyle"],
            alpha=st["alpha"],
            zorder=st["zorder"],
        )


def draw_moisture_quantity(ax, T, W_sat, cfg, st):
    """
    Draw constant humidity-ratio isolines (W = const).

    These isolines appear as horizontal lines on the psychrometric chart.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes for plotting.
    T : ndarray
        Dry-bulb temperature array (°C).
    W_sat : ndarray
        Saturation humidity ratio curve.
    cfg : ChartConfig
        Global chart configuration.
    st : dict
        Resolved isoline style and behavior dictionary.

    Notes
    -----
    Lines are clipped so that they only appear below the saturation curve.
    """

    for w_val in st["values"]:
        mask = W_sat >= w_val
        if not mask.any():
            # Entire line lies above saturation → skip
            continue

        ax.hlines(
            y=w_val,
            xmin=T[mask].min(),
            xmax=T[mask].max(),
            colors=st["color"],
            linewidths=st["linewidth"],
            linestyles=st["linestyle"],
            alpha=st["alpha"],
            zorder=st["zorder"],
        )

