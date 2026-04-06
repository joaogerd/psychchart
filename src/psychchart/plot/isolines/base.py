"""
Base isoline rendering orchestration.

This module defines the **core orchestration layer** for psychrometric
isoline rendering. It provides the glue between:

- declarative user intent (:class:`IsoSet`),
- semantic visual defaults (:class:`IsolineProfile`),
- numerical isoline handlers,
- and the Matplotlib rendering backend.

Scope and responsibilities
--------------------------
This module is responsible for:

- resolving effective isoline rendering parameters by merging:
  - user overrides,
  - semantic profile defaults,
  - hard-coded safe fallbacks;
- dispatching isoline families to their registered handlers;
- providing a single public entry point for isoline rendering.

This module explicitly does NOT:

- perform psychrometric calculations;
- validate physical correctness of isolines;
- define numerical formulations of isolines;
- manage legends, colorbars, or axis configuration.

Architecture overview
---------------------
The isoline rendering pipeline is organized as follows:

1. **User intent**
   Declared via :class:`IsoSet`, typically loaded from YAML/JSON.

2. **Semantic defaults**
   Defined by :class:`IsolineProfile`, describing how a family of
   isolines *should look* by default.

3. **Resolution layer** (this module)
   Combines intent + semantics + safe defaults into a flat,
   deterministic rendering configuration.

4. **Numerical handlers**
   One handler per isoline family, responsible for:
   - computing isoline curves,
   - clipping them to the saturation domain,
   - rendering lines and labels.

5. **Public dispatcher**
   A single entry point that orchestrates the rendering of all
   configured isoline families.

Design principles
-----------------
- **Separation of concerns**:
  Visual semantics, numerical logic, and orchestration are isolated.
- **Extensibility**:
  New isoline families can be added without modifying this module.
- **Fail-safe behavior**:
  Unknown or partially configured isolines are ignored silently,
  never breaking chart rendering.
- **Declarative-first**:
  Rendering behavior is driven by configuration, not imperative code.

Public API
----------
The only public function exposed by this module is:

- :func:`draw_isolines`

All other helpers are considered internal and may change without
notice.

Examples
--------
Typical usage inside a chart renderer:

>>> fig, ax = plt.subplots()
>>> chart = PsychrometricChart(config)
>>> chart.prepare()
>>> draw_isolines(ax, chart)

Disabling a specific isoline family declaratively:

>>> chart.isolines["rh"].enabled = False
>>> draw_isolines(ax, chart)
"""


from matplotlib.axes import Axes
from typing import Dict

from psychchart.config import IsoSet, ChartConfig
from psychchart.plot.isolines.profiles import get_isoline_profile
from psychchart.plot.isolines.registry import ISOLINE_HANDLERS, LABEL_HANDLERS
from psychchart.plot.layers import ZORDER


def _resolve_iso_defaults(key: str, iso: IsoSet):
    """
    Resolve effective isoline rendering parameters by merging defaults
    and user overrides.

    This helper function computes the **final, effective rendering
    configuration** for a given isoline family by merging three layers,
    in strict priority order:

    1. User overrides provided via :class:`IsoSet`
    2. Semantic defaults from :class:`IsolineProfile`
    3. Hard-coded safe defaults (fallback of last resort)

    The result is a flat dictionary of resolved parameters, suitable
    for direct consumption by low-level rendering routines.

    Parameters
    ----------
    key : str
        Canonical isoline family name.

        This must match:
        - the key used by the renderer,
        - the key used in ``IsoSet``,
        - a registered semantic profile (if available).

        Example: ``"relative_humidity"``.

    iso : IsoSet
        User-provided isoline configuration.

        This object may partially override visual attributes such as
        color, line style, label behavior, or numerical values.

    Returns
    -------
    dict
        Dictionary containing the fully resolved isoline parameters.

        Guaranteed keys include:
        - ``color``
        - ``linewidth``
        - ``linestyle``
        - ``labels``
        - ``label_fontsize``
        - ``label_fmt``
        - ``zorder``
        - ``values``

        All values are guaranteed to be non-missing and safe for
        rendering.

    Notes
    -----
    Resolution precedence (highest to lowest priority):

    1. Explicit values in ``IsoSet``
    2. Defaults from ``IsolineProfile`` (if registered)
    3. Hard-coded safe defaults

    This function contains **no rendering logic** and performs
    **no validation** of numerical correctness. Its sole responsibility
    is deterministic resolution of defaults.

    Examples
    --------
    Basic usage inside a renderer:

    >>> iso = IsoSet(color="red", linewidth=2.0)
    >>> params = _resolve_iso_defaults("relative_humidity", iso)
    >>> params["color"]
    'red'
    >>> params["linewidth"]
    2.0

    Profile fallback when user does not override:

    >>> iso = IsoSet()
    >>> params = _resolve_iso_defaults("relative_humidity", iso)
    >>> params["linestyle"]
    '--'

    Safe fallback when profile is missing:

    >>> iso = IsoSet()
    >>> params = _resolve_iso_defaults("unknown_isoline", iso)
    >>> params["linestyle"]
    '-'
    """

    # ------------------------------------------------------------------
    # Resolve semantic profile (may be None if not registered)
    # ------------------------------------------------------------------
    profile = get_isoline_profile(key)

    # ------------------------------------------------------------------
    # Hard-coded safe defaults (last-resort fallback)
    # ------------------------------------------------------------------
    # These values guarantee that rendering never fails, even if:
    # - the isoline family is unknown,
    # - the profile is missing,
    # - the profile is incomplete.
    hard = {
        "color": "0.4",
        "linewidth": 1.0,
        "linestyle": "-",
        "alpha": 1.0,
        "labels": False,
        "label_fontsize": 6,
        "label_fmt": None,
        "zorder": ZORDER["isolines"],
        "values": None,
    }

    # ------------------------------------------------------------------
    # Base defaults: profile → hard fallback
    # ------------------------------------------------------------------
    if profile is None:
        # No semantic profile registered: use hard defaults directly
        base = dict(hard)
    else:
        # Start from semantic profile defaults
        base = {
            "color": profile.color,
            "linewidth": profile.linewidth,
            "linestyle": profile.linestyle,
            "alpha": profile.alpha,
            "labels": profile.labels,
            "label_fontsize": profile.label_fontsize,
            "label_fmt": profile.label_fmt,
            "zorder": profile.zorder,
            "values": profile.values,
        }

        # Fill missing profile attributes with hard defaults
        # This allows profiles to remain intentionally partial.
        for k, v in hard.items():
            if base.get(k) is None:
                base[k] = v

    # ------------------------------------------------------------------
    # Merge IsoSet overrides (highest priority)
    # ------------------------------------------------------------------
    resolved = dict(base)

    # Visual overrides
    if iso.color is not None:
        resolved["color"] = iso.color
    if iso.linewidth is not None:
        resolved["linewidth"] = iso.linewidth
    if iso.linestyle is not None:
        resolved["linestyle"] = iso.linestyle

    # Label behavior overrides
    # NOTE: iso.labels is currently a boolean, not Optional[bool],
    # so it is treated as an explicit override when provided.
    resolved["labels"] = iso.labels if iso.labels is not None else base["labels"]

    # Font size override
    # If IsoSet migrates label_fontsize to Optional[int], this logic
    # already supports that seamlessly.
    resolved["label_fontsize"] = (
        iso.label_fontsize
        if iso.label_fontsize is not None
        else base["label_fontsize"]
    )

    # Numerical values override
    # If user provides explicit isoline levels, they fully replace
    # profile defaults.
    resolved["values"] = (
        iso.values
        if (iso.values and len(iso.values) > 0)
        else base["values"]
    )
    return resolved

def _draw_isoline(ax, key, iso, T, W_sat, cfg):
    """
    Draw a single psychrometric isoline family on a Matplotlib axis.

    This is a **dispatcher-level helper** responsible for rendering one
    *family* of isolines (e.g., relative humidity, enthalpy, wet-bulb
    temperature). It does not perform any psychrometric calculations by
    itself; instead, it coordinates three steps:

    1. Resolve the appropriate isoline handler based on ``key``.
    2. Resolve effective style defaults and user overrides.
    3. Delegate the actual rendering to the resolved handler.

    If the isoline family is unknown or if no isoline values are defined,
    the function exits **silently** by design.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target Matplotlib axis where the isolines will be drawn.
    key : str
        Identifier of the isoline family (e.g., ``"rh"``, ``"enthalpy"``,
        ``"wetbulb"``). This key is used to resolve the correct handler
        from ``ISOLINE_HANDLERS``.
    iso : IsoSet
        Declarative configuration object describing the isoline family.
        This object typically defines:
        - which isoline values should be drawn,
        - base style information,
        - label behavior.
    T : numpy.ndarray
        Array of dry-bulb temperatures (°C) defining the computational
        domain of the chart.
    W_sat : numpy.ndarray
        Saturation humidity ratio corresponding to ``T``. Used by most
        isoline handlers to clip isolines to the physically valid domain
        (below the saturation curve).
    cfg : ChartConfig
        Global chart configuration object. Provides axis limits, pressure,
        labeling preferences, and other chart-level metadata.

    Returns
    -------
    None
        This function operates via side effects on ``ax`` and does not
        return any value.

    Notes
    -----
    - This function is intentionally **silent** when no handler is found
      or when no isoline values are defined. This allows flexible and
      partial configurations without forcing strict validation at the
      rendering stage.
    - All isoline-specific logic (computation, clipping, labeling) is
      encapsulated in the corresponding handler function.
    - This function should be called by a higher-level renderer that
      iterates over all configured isoline families.

    Examples
    --------
    Drawing a relative humidity isoline family inside a chart renderer:

    >>> fig, ax = plt.subplots()
    >>> _draw_isoline(
    ...     ax=ax,
    ...     key="rh",
    ...     iso=rh_iso_config,
    ...     T=T,
    ...     W_sat=W_sat,
    ...     cfg=chart_config,
    ... )

    Attempting to draw an unknown isoline family (silently ignored):

    >>> _draw_isoline(
    ...     ax=ax,
    ...     key="unknown_family",
    ...     iso=iso_config,
    ...     T=T,
    ...     W_sat=W_sat,
    ...     cfg=chart_config,
    ... )
    """

    # --------------------------------------------------------------
    # Resolve isoline handler
    # --------------------------------------------------------------
    handler = ISOLINE_HANDLERS.get(key)
    if handler is None:
        # Unknown isoline family → silently ignore
        return

    # --------------------------------------------------------------
    # Resolve effective style and defaults
    # --------------------------------------------------------------
    st = _resolve_iso_defaults(key, iso)
    if not st["values"]:
        # No isoline values defined → nothing to draw
        return

    # --------------------------------------------------------------
    # Delegate rendering to the handler
    # --------------------------------------------------------------
    geometries = handler(
                         ax=ax,
                         T=T,
                         W_sat=W_sat,
                         cfg=cfg,
                         st=st,
                        )

    # --------------------------------------------------------------
    # Draw labels (if enabled and supported)
    # --------------------------------------------------------------
    if st["labels"]:
        label_handler = LABEL_HANDLERS.get(key)
        if label_handler is not None:
            label_handler(
                    ax=ax,
                    geom=geometries,
                    cfg=cfg,
                    st=st,
            )

def draw_isolines(ax: Axes, chart) -> None:
    """
    Public isoline dispatcher for psychrometric charts.

    This function is the **single public entry point** responsible for
    rendering *all* psychrometric isoline families defined in a prepared
    chart object.

    Conceptually, this dispatcher sits at the **highest level of the
    isoline rendering pipeline**. It does not perform calculations,
    styling, or validation; instead, it coordinates the rendering flow
    by iterating over user-declared isolines and delegating each one to
    the appropriate low-level handler.

    Responsibilities
    ----------------
    This function:
    - iterates over all configured isoline families,
    - skips isolines explicitly disabled by the user,
    - delegates each isoline family to ``_draw_isoline``.

    This function explicitly does NOT:
    - perform psychrometric computations,
    - decide visual styles or defaults,
    - validate physical consistency,
    - manage labels, legends, or clipping logic.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes where isolines will be rendered.
        The axes are assumed to be already configured with limits,
        labels, and projection consistent with the chart.
    chart : object
        Fully prepared chart object.

        The chart object is expected to expose the following attributes:

        - ``chart.isolines`` : dict[str, IsoSet]
            Mapping between isoline family keys (e.g. ``"rh"``,
            ``"enthalpy"``, ``"wetbulb"``) and their corresponding
            :class:`IsoSet` configuration objects.
        - ``chart.T`` : numpy.ndarray
            Dry-bulb temperature grid (°C) used by all isoline families.
        - ``chart.W_sat`` : numpy.ndarray
            Saturation humidity ratio corresponding to ``chart.T``.
            Used to clip isolines to the physically valid domain.
        - ``chart.cfg`` : ChartConfig
            Global chart configuration object defining limits,
            pressure, labels, and metadata.

    Returns
    -------
    None
        This function operates via side effects on ``ax`` and does not
        return any value.

    Notes
    -----
    Architectural role
    ------------------
    This dispatcher enforces a **clean separation of concerns**:

    - User intent lives in :class:`IsoSet`
    - Visual defaults live in ``IsolineProfile``
    - Numerical logic lives in individual isoline handlers
    - Orchestration lives here

    This design makes the isoline system:
    - extensible (new isoline families require only a new handler),
    - testable (handlers can be tested independently),
    - declarative (YAML/JSON configuration maps cleanly to rendering).

    Examples
    --------
    Typical usage inside a chart renderer:

    >>> fig, ax = plt.subplots()
    >>> chart = PsychrometricChart(config)
    >>> chart.prepare()
    >>> draw_isolines(ax, chart)

    Disabling a specific isoline family via configuration:

    >>> chart.isolines["rh"].enabled = False
    >>> draw_isolines(ax, chart)
    """

    # --------------------------------------------------------------
    # Iterate over all configured isoline families
    # --------------------------------------------------------------
    for key, iso in chart.isolines.items():

        # ----------------------------------------------------------
        # Skip isolines explicitly disabled by the user
        # ----------------------------------------------------------
        if iso.enabled is False:
            continue

        # ----------------------------------------------------------
        # Delegate rendering of this isoline family
        # ----------------------------------------------------------
        _draw_isoline(
            ax=ax,
            key=key,
            iso=iso,
            T=chart.T,
            W_sat=chart.W_sat,
            cfg=chart.cfg,
        )

