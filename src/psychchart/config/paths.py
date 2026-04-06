"""
Path configuration models for psychchart.

This module defines the typed configuration model used to represent ordered
paths in psychrometric space within the ``psychchart`` package.

A path is defined by sequences of dry-bulb temperature and relative humidity
values, optionally accompanied by a scalar sequence for progressive coloring.
This abstraction is useful for visualizing trajectories, exposure histories,
experimental sequences, or any ordered evolution of states across the
psychrometric plane.

The main purpose of this module is to provide a strongly typed and semantically
normalized representation of path-based chart elements.

Notes
-----
This module is declarative and validation-oriented.

It is responsible for:
- validating ordered psychrometric trajectories
- normalizing relative humidity values
- storing optional scalar values for color mapping
- storing path-level visual styling parameters

It is not responsible for:
- humidity-ratio conversion
- interpolation
- segment generation
- plotting execution

See Also
--------
base
    Shared strict configuration base model.
utils
    Utility helpers used for relative humidity normalization.
points
    Configuration model for individual reference points.
overlays
    Temporal overlay configuration that may use path-like trajectories.

Examples
--------
Define a simple path with fixed color:

>>> cfg = PathConfig(
...     label="Morning trajectory",
...     T=[20.0, 22.0, 24.0],
...     RH=[80, 70, 60],
...     color="blue",
... )
>>> cfg.label
'Morning trajectory'
>>> cfg.RH
[0.8, 0.7, 0.6]

Define a path with scalar values for progressive coloring:

>>> cfg = PathConfig(
...     label="CTA path",
...     T=[25.0, 26.0, 27.5],
...     RH=[0.65, 0.60, 0.58],
...     values=[10.0, 15.0, 22.0],
...     cmap="viridis",
... )
>>> cfg.cmap
'viridis'
"""

from typing import Optional, Sequence, Any

from pydantic import Field, field_validator

from .base import StrictModel
from .utils import normalize_rh


class PathConfig(StrictModel):
    """
    Declarative definition of a psychrometric path (trajectory).

    This model represents an ordered trajectory in psychrometric space, where
    each point is defined by dry-bulb temperature and relative humidity. It is
    designed for use cases in which the temporal or logical evolution of a
    system must be visualized as a connected path on the chart.

    Typical applications include:

    - environmental trajectories over time
    - animal exposure paths
    - experimental chamber sequences
    - state transitions in psychrometric analyses

    Parameters
    ----------
    label : str
        Human-readable label associated with the path.

        This label is typically used in legends, annotations, or figure
        metadata.
    T : sequence of float
        Ordered sequence of dry-bulb temperatures, usually expressed in
        degrees Celsius.

        The sequence order is preserved and defines the trajectory direction.
    RH : sequence of float
        Ordered sequence of relative humidity values associated with ``T``.

        Values may be given either as:

        - fractions in the interval ``[0, 1]``
        - percentages in the interval ``[0, 100]``

        Internally, all values are normalized to the fractional domain
        ``[0, 1]``.
    values : sequence of float or None, optional
        Optional scalar sequence associated with the path points.

        This sequence is typically used to color-map the trajectory
        progressively, for example by time, cumulative thermal load, or any
        other scalar quantity defined along the path.
    color : str or None, optional
        Fixed path color.

        This is typically used when the full path should have a single visual
        color instead of a scalar-dependent color mapping.
    cmap : str or None, optional
        Matplotlib colormap name used when ``values`` is provided and the path
        should be colored progressively.
    vmin : float or None, optional
        Lower normalization bound for ``values``.

        If ``None``, the plotting layer may infer the lower bound from the data.
    vmax : float or None, optional
        Upper normalization bound for ``values``.

        If ``None``, the plotting layer may infer the upper bound from the data.
    linewidth : float, default=1.5
        Width of the path line.
    linestyle : str, default="-"
        Matplotlib line style used to render the trajectory.
    alpha : float, default=1.0
        Opacity of the path.

        Values closer to ``0`` make the path more transparent, while ``1``
        means fully opaque.

    Returns
    -------
    PathConfig
        Validated and semantically normalized path configuration.

    Raises
    ------
    ValueError
        Raised indirectly when one or more relative humidity values cannot be
        normalized into the valid fractional interval ``[0, 1]``.
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported fields
        are provided, because this class inherits strict validation behavior
        from ``StrictModel``.

    Notes
    -----
    This model is declarative. It does not compute humidity ratio, build line
    segments, interpolate values, or render the path directly.

    Relative humidity normalization is performed after regular validation so
    that downstream code can safely assume a consistent internal representation.

    This class does not currently enforce sequence-length consistency between
    ``T``, ``RH``, and ``values``. If desired, that validation can be added in
    a future refinement.

    See Also
    --------
    normalize_rh
        Utility function used to normalize relative humidity values.
    Point
        Configuration model for a single reference point on the chart.

    Examples
    --------
    Define a simple path with fixed color:

    >>> cfg = PathConfig(
    ...     label="Morning trajectory",
    ...     T=[20.0, 22.0, 24.0],
    ...     RH=[80, 70, 60],
    ...     color="blue",
    ... )
    >>> cfg.label
    'Morning trajectory'
    >>> cfg.RH
    [0.8, 0.7, 0.6]

    Define a path with scalar values for progressive coloring:

    >>> cfg = PathConfig(
    ...     label="CTA path",
    ...     T=[25.0, 26.0, 27.5],
    ...     RH=[0.65, 0.60, 0.58],
    ...     values=[10.0, 15.0, 22.0],
    ...     cmap="viridis",
    ...     vmin=10.0,
    ...     vmax=25.0,
    ... )
    >>> cfg.cmap
    'viridis'
    >>> cfg.values[1]
    15.0
    """

    # -------------------------------------------------------------------------
    # Semantic identity
    # -------------------------------------------------------------------------
    # ``label`` is the human-readable identifier used in legends or metadata.
    label: str

    # -------------------------------------------------------------------------
    # Ordered psychrometric coordinates
    # -------------------------------------------------------------------------
    # ``T`` and ``RH`` together define the trajectory in psychrometric space.
    # Their order is meaningful and should reflect the intended path sequence.
    T: Sequence[float]
    RH: Sequence[float]

    # -------------------------------------------------------------------------
    # Optional scalar support for color mapping
    # -------------------------------------------------------------------------
    # ``values`` may store a scalar associated with each path point, enabling
    # progressive coloring or scalar-aware rendering.
    values: Optional[Sequence[float]] = None

    # -------------------------------------------------------------------------
    # Visual styling
    # -------------------------------------------------------------------------
    # ``color`` supports a fixed-color path.
    # ``cmap`` + ``values`` support scalar-based coloring.
    # ``vmin`` and ``vmax`` control normalization bounds for scalar mapping.
    color: Optional[str] = None
    cmap: Optional[str] = None
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    linewidth: float = 1.5
    linestyle: str = "-"
    alpha: float = 1.0


    @field_validator("RH", mode="before")
    @classmethod
    def validate_rh_series(cls, value: Any) -> list[float] | None:
        """
        Validate and normalize a sequence of relative humidity values before parsing.
    
        This validator is executed in ``before`` mode, meaning it receives the raw
        input exactly as provided by the configuration source, before Pydantic
        coerces it into the declared target type.
    
        Its purpose is to ensure that every value in the ``RH`` sequence is
        converted to the canonical fractional domain ``[0, 1]`` while still
        accepting the two most common user-facing conventions for relative
        humidity:
    
        - fractions, such as ``0.65``
        - percentages, such as ``65``
    
        Parameters
        ----------
        value : Any
            Raw value associated with the ``RH`` field.
    
            This is typically expected to be an iterable of numeric relative
            humidity values, but because this validator runs before standard
            parsing, the input may still be in any raw form accepted by the
            configuration loader.
    
        Returns
        -------
        list of float or None
            A list of normalized relative humidity values in the interval
            ``[0, 1]``, or ``None`` if the input is ``None``.
    
        Raises
        ------
        ValueError
            Raised indirectly by ``normalize_rh`` if one or more values fall
            outside the valid relative humidity domain after normalization.
        TypeError
            May be raised indirectly if ``value`` is not iterable when sequence
            normalization is attempted.
    
        Notes
        -----
        This validator is useful for path- or trajectory-like models where
        relative humidity is represented as an ordered series rather than a single
        scalar value.
    
        By normalizing the sequence here, downstream code can safely assume that
        all values stored in ``RH`` are already in fractional form, regardless of
        whether the user originally provided percentages or fractions.
    
        See Also
        --------
        normalize_rh
            Utility function that normalizes a single relative humidity value to
            the fractional domain ``[0, 1]``.
    
        Examples
        --------
        Normalize a percentage-based sequence:
    
        >>> validate_rh_series(None, [40, 60, 80])
        [0.4, 0.6, 0.8]
    
        Preserve fractional values:
    
        >>> validate_rh_series(None, [0.4, 0.6, 0.8])
        [0.4, 0.6, 0.8]
    
        Keep ``None`` unchanged:
    
        >>> validate_rh_series(None, None) is None
        True
        """
        # Preserve ``None`` so optional RH sequences remain optional and are not
        # silently converted into empty lists or other structures.
        if value is None:
            return value
    
        # Normalize each element individually so the internal representation is
        # always a list of fractional relative humidity values in [0, 1].
        return [normalize_rh(v) for v in value]
