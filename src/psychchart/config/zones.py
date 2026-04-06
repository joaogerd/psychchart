"""
Zone configuration models for psychchart.

This module defines the typed configuration models used to represent geometric
and semantic zones on the psychrometric chart.

Zones may be defined explicitly through polygon vertices or implicitly through
temperature and relative-humidity intervals. They are useful for representing
comfort regions, warning bands, admissible operating envelopes, and other
domain-specific regions in psychrometric space.

The main purpose of this module is to provide a declarative, strongly typed,
and semantically normalized representation of chart regions.

Notes
-----
This module belongs to the configuration layer.

It is responsible for:
- validating zone definitions
- storing explicit or interval-based region descriptions
- normalizing relative humidity interval values
- storing visual styling attributes for boundaries and fills

It is not responsible for:
- polygon construction
- curve following or geometric discretization
- psychrometric coordinate conversion
- region rendering

See Also
--------
app
    Root configuration model that aggregates zone definitions.
base
    Shared strict configuration base model.
utils
    Utility helpers used for relative humidity normalization.
indexes
    Index-related semantic configuration that may define index-derived zones.

Examples
--------
Define a zone using explicit vertices:

>>> zone = Zone(
...     name="comfort_polygon",
...     vertices=[[20.0, 0.006], [24.0, 0.007], [26.0, 0.009]],
...     edgecolor="green",
...     facecolor="lightgreen",
... )
>>> zone.name
'comfort_polygon'

Define a zone using temperature and relative humidity ranges:

>>> zone = Zone(
...     name="comfort_band",
...     t_range=(18.0, 26.0),
...     rh_range=(40, 70),
...     follow_rh=True,
... )
>>> zone.rh_range
(0.4, 0.7)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field, field_validator

from .base import StrictModel
from .utils import normalize_rh


class Zone(StrictModel):
    """
    Definition of a geometric zone on the chart.

    This model describes a geometric region to be drawn on the psychrometric
    chart. A zone may be defined explicitly as a polygon through its vertices,
    or implicitly through temperature and relative-humidity ranges.

    Typical use cases include:

    - comfort regions
    - warning or stress zones
    - admissible operating envelopes
    - empirically derived regions in the psychrometric plane

    Parameters
    ----------
    name : str
        Human-readable name of the zone.

        This value is also used as the semantic identifier for annotations,
        legends, or downstream processing.
    vertices : list of list of float or None, optional
        Explicit polygon vertices defining the zone geometry.

        Each inner list is expected to represent one point in chart
        coordinates, typically ``[temperature, humidity_ratio]`` or another
        coordinate pair interpreted by the rendering layer.
    t_range : tuple of float or None, optional
        Temperature interval used to define the zone implicitly.

        This is usually interpreted as ``(t_min, t_max)``.
    rh_range : tuple of float or None, optional
        Relative humidity interval used to define the zone implicitly.

        Values may be provided either as fractions in ``[0, 1]`` or as
        percentages in ``[0, 100]``. Internally, they are normalized to the
        fractional domain ``[0, 1]``.
    follow_rh : bool, default=False
        Whether the zone boundaries should follow relative-humidity curves
        instead of being interpreted as a simple rectangular region in the raw
        coordinate system.
    edgecolor : str, default="k"
        Edge color of the zone outline.

        The default ``"k"`` corresponds to black in Matplotlib notation.
    facecolor : str or None, optional
        Fill color of the zone interior.

        If ``None``, the plotting layer may render the zone without fill or use
        a higher-level default.
    linewidth : float, default=1.5
        Width of the zone boundary line.
    alpha : float, default=0.3
        Opacity of the filled region.

        This value is especially useful when multiple zones or background
        fields coexist in the same figure.

    Returns
    -------
    Zone
        Validated and semantically normalized zone configuration.

    Raises
    ------
    ValueError
        Raised indirectly when a relative humidity value in ``rh_range`` cannot
        be normalized into the valid fractional interval ``[0, 1]``.
    pydantic.ValidationError
        Raised when field values have invalid types or unsupported keys are
        provided, because this model inherits strict validation behavior from
        ``StrictModel``.

    Notes
    -----
    This class is declarative and does not construct the final polygon by
    itself. Geometry generation, coordinate conversion, and rendering are
    handled elsewhere in the pipeline.

    A zone may be represented in two broad ways:

    - **explicit geometry**, using ``vertices``
    - **semantic ranges**, using ``t_range`` and ``rh_range``

    The latter is particularly useful when the plotting layer knows how to
    convert a thermodynamic interval into a psychrometric region.

    See Also
    --------
    normalize_rh
        Utility used to normalize relative humidity interval values.
    IndexZone
        Semantic zone definition derived from a computed index range.

    Examples
    --------
    Define a zone using explicit vertices:

    >>> zone = Zone(
    ...     name="comfort_polygon",
    ...     vertices=[[20.0, 0.006], [24.0, 0.007], [26.0, 0.009]],
    ...     edgecolor="green",
    ...     facecolor="lightgreen",
    ... )
    >>> zone.name
    'comfort_polygon'
    >>> len(zone.vertices)
    3

    Define a zone using temperature and relative humidity ranges:

    >>> zone = Zone(
    ...     name="comfort_band",
    ...     t_range=(18.0, 26.0),
    ...     rh_range=(40, 70),
    ...     follow_rh=True,
    ... )
    >>> zone.rh_range
    (0.4, 0.7)

    Relative humidity fractions are also accepted:

    >>> zone = Zone(
    ...     name="fractional_rh_zone",
    ...     t_range=(22.0, 30.0),
    ...     rh_range=(0.45, 0.75),
    ... )
    >>> zone.rh_range
    (0.45, 0.75)
    """

    # -------------------------------------------------------------------------
    # Semantic identity and geometry definition
    # -------------------------------------------------------------------------
    # ``name`` is the human-readable identifier of the zone.
    # ``vertices`` can store an explicit polygon.
    # ``t_range`` and ``rh_range`` provide a higher-level semantic way to
    # define a zone without explicitly specifying every point.
    name: str
    vertices: Optional[List[List[float]]] = None
    t_range: Optional[Tuple[float, float]] = None
    rh_range: Optional[Tuple[float, float]] = None
    follow_rh: bool = False

    # -------------------------------------------------------------------------
    # Visual appearance
    # -------------------------------------------------------------------------
    # These settings control how the zone boundary and fill should appear.
    edgecolor: str = "k"
    facecolor: Optional[str] = None
    linewidth: float = 1.5
    alpha: float = 0.3

    @field_validator("rh_range", mode="before")
    @classmethod
    def validate_rh_range(cls, value: Any) -> tuple[float, float] | None:
        """
        Validate and normalize a relative humidity interval before field parsing.
    
        This validator is executed in ``before`` mode, meaning it receives the raw
        input exactly as provided by the configuration source before Pydantic
        performs standard coercion into the declared target type.
    
        Its purpose is to ensure that the ``rh_range`` field is always represented
        internally as a tuple of relative humidity fractions in the interval
        ``[0, 1]``, while still accepting the two most common user-facing
        conventions:
    
        - fractional values, such as ``(0.4, 0.7)``
        - percentage values, such as ``(40, 70)``
    
        Parameters
        ----------
        value : Any
            Raw value associated with the ``rh_range`` field.
    
            This is typically expected to be an iterable with two numeric values,
            representing the lower and upper bounds of the relative humidity
            interval.
    
        Returns
        -------
        tuple of float or None
            Normalized relative humidity interval in fractional form, or ``None``
            if the input is ``None``.
    
        Raises
        ------
        ValueError
            Raised indirectly by ``normalize_rh`` if one or both values fall
            outside the valid relative humidity domain after normalization.
        TypeError
            May be raised indirectly if ``value`` is not iterable when interval
            normalization is attempted.
    
        Notes
        -----
        This validator is especially useful for zone-like configuration models in
        which relative humidity is expressed as an interval instead of a single
        scalar.
    
        By normalizing the interval here, the rest of the system can safely assume
        that ``rh_range`` is always stored in fractional form, regardless of
        whether the user wrote the configuration using percentages or fractions.
    
        This function does not explicitly check that exactly two elements are
        provided. That structural validation is typically handled by Pydantic
        through the declared field type.
    
        See Also
        --------
        normalize_rh
            Utility function used to normalize a single relative humidity value
            into the fractional interval ``[0, 1]``.
        pydantic.field_validator
            Pydantic decorator used to define field-level validators.
    
        Examples
        --------
        Normalize a percentage-based interval:
    
        >>> validate_rh_range(None, (40, 70))
        (0.4, 0.7)
    
        Preserve an already fractional interval:
    
        >>> validate_rh_range(None, (0.4, 0.7))
        (0.4, 0.7)
    
        Keep ``None`` unchanged:
    
        >>> validate_rh_range(None, None) is None
        True
        """
        # Preserve ``None`` so optional RH intervals remain optional and can be
        # handled naturally by the rest of the validation pipeline.
        if value is None:
            return value
    
        # Normalize each bound individually so the internal representation always
        # uses fractional relative humidity values in the interval [0, 1].
        return tuple(normalize_rh(v) for v in value)

class IndexZone(StrictModel):
    """
    Definition of a zone derived from an index range.

    This model describes a semantic zone that is not defined directly by raw
    psychrometric geometry, but instead by an interval of a computed index such
    as THI, ITU, thermal excess, or any other registered scalar indicator.

    These zones are useful when the user wants to color or classify regions of
    the chart according to index thresholds rather than explicit polygons.

    Parameters
    ----------
    index : str
        Canonical identifier of the index used to derive the zone.

        This value should match the identifier expected by the runtime index
        computation backend.
    name : str
        Human-readable name of the zone.

        Examples might include ``"comfort"``, ``"alert"``, ``"danger"``, or
        domain-specific labels associated with threshold intervals.
    range : tuple of float
        Inclusive numeric interval associated with the zone.

        This is typically interpreted as ``(lower_bound, upper_bound)`` for the
        target index.
    color : str, default="gray"
        Color associated with the zone.
    alpha : float, default=0.3
        Opacity associated with the rendered zone.
    parameters : dict of str to Any, optional
        Optional index-specific parameters required to evaluate the index.

        This is useful when the same index family can be parameterized in
        different ways.

    Returns
    -------
    IndexZone
        Validated index-derived zone configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or unsupported keys are
        provided.

    Notes
    -----
    This model is semantic rather than geometric. It does not itself compute
    the spatial region corresponding to the index interval. That task belongs
    to the computation and rendering layers.

    The ``parameters`` field is intentionally flexible because some derived
    indices may require extra metadata, calibration coefficients, or other
    runtime-specific arguments.

    See Also
    --------
    Zone
        Geometric chart zone defined directly in chart coordinates.
    IndexConfig
        Configuration model describing the index computation and rendering.
    AppConfig
        Root configuration model that may aggregate multiple index zones.

    Examples
    --------
    Define an index zone for a comfort interval:

    >>> zone = IndexZone(
    ...     index="ITU",
    ...     name="comfort",
    ...     range=(20.0, 72.0),
    ...     color="green",
    ...     alpha=0.25,
    ... )
    >>> zone.index
    'ITU'
    >>> zone.range
    (20.0, 72.0)

    Define an index zone with custom parameters:

    >>> zone = IndexZone(
    ...     index="TE",
    ...     name="moderate_excess",
    ...     range=(1.5, 3.0),
    ...     color="orange",
    ...     parameters={"threshold": 72.0},
    ... )
    >>> zone.parameters["threshold"]
    72.0
    """

    # -------------------------------------------------------------------------
    # Semantic identity
    # -------------------------------------------------------------------------
    # ``index`` identifies the scalar field used to derive the zone.
    # ``name`` is the human-readable label associated with the interval.
    index: str
    name: str

    # -------------------------------------------------------------------------
    # Numeric interval and visual style
    # -------------------------------------------------------------------------
    # ``range`` defines the interval in index space.
    # ``color`` and ``alpha`` are typically used by the renderer when drawing
    # the corresponding classified region.
    range: Tuple[float, float]
    color: str = "gray"
    alpha: float = 0.3

    # -------------------------------------------------------------------------
    # Index-specific parameters
    # -------------------------------------------------------------------------
    # This dictionary supports configurable or parameterized indices without
    # forcing the configuration model to know every possible option in advance.
    parameters: Dict[str, Any] = Field(default_factory=dict)
