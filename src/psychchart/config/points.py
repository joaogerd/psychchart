"""
Point configuration models for psychchart.

This module defines the typed configuration model used to represent annotated
reference points on the psychrometric chart.

A point is typically defined by dry-bulb temperature and relative humidity,
with optional label and styling metadata. The model provides a strongly typed
representation of user-defined point annotations and ensures that relative
humidity values are normalized into a consistent internal convention.

The main purpose of this module is to avoid raw ad hoc dictionaries in the
plotting pipeline and provide a reusable declarative contract for point-based
chart elements.

Notes
-----
This module belongs to the configuration layer.

It is responsible for:
- validating point coordinates and styling options
- normalizing relative humidity values
- storing annotation visibility metadata
- exposing a typed point representation for downstream use

It is not responsible for:
- humidity-ratio computation
- coordinate transformation
- marker rendering
- label placement logic

See Also
--------
base
    Shared strict configuration base model.
utils
    Utility helpers used for relative humidity normalization.
paths
    Ordered trajectory model for multi-point paths.
app
    Root configuration model that aggregates point definitions.

Examples
--------
Create a point using fractional relative humidity:

>>> p = Point(t=25.0, rh=0.60, label="Reference")
>>> p.t
25.0
>>> p.rh
0.6

Create a point using percentage relative humidity:

>>> p = Point(t=30.0, rh=65, color="red", marker="s")
>>> p.rh
0.65
>>> p.marker
's'
"""

from __future__ import annotations

from typing import Optional

from pydantic import field_validator

from .base import StrictModel
from .utils import normalize_rh


class Point(StrictModel):
    """
    Definition of a reference point on the chart.

    This model represents a single annotated point in psychrometric space.
    A point is usually defined by dry-bulb temperature and relative humidity,
    and may optionally include a label and visual styling parameters.

    The main purpose of this class is to provide a strongly typed and
    semantically normalized representation of user-defined reference points,
    avoiding raw dictionaries in the plotting pipeline.

    Parameters
    ----------
    t : float
        Dry-bulb temperature coordinate of the point.

        This value is interpreted in the same temperature unit used by the
        chart configuration, typically degrees Celsius.
    rh : float
        Relative humidity associated with the point.

        The input may be provided either as:

        - a fraction in the interval ``[0, 1]``, such as ``0.65``
        - a percentage in the interval ``[0, 100]``, such as ``65``

        Internally, this field is normalized to the fractional domain
        ``[0, 1]``.
    label : str or None, optional
        Optional text label associated with the point.

        This label may be displayed next to the marker when
        ``show_label=True``.
    marker : str, default="o"
        Matplotlib marker style used to render the point.
    color : str, default="k"
        Marker color.

        The default ``"k"`` corresponds to black in Matplotlib notation.
    size : float, default=20.0
        Marker size used when drawing the point.
    alpha : float, default=1.0
        Marker opacity.

        Values closer to ``0`` make the point more transparent, while ``1``
        means fully opaque.
    zorder : int, default=5
        Drawing order of the point.

        Larger values usually cause the point to be drawn on top of lower
        z-order elements.
    show_label : bool, default=True
        Whether the label should be shown if a label is available.

    Returns
    -------
    Point
        Validated and normalized point configuration.

    Raises
    ------
    ValueError
        Raised indirectly when the relative humidity value cannot be
        normalized into the valid fractional interval ``[0, 1]``.
    pydantic.ValidationError
        Raised when field values have invalid types or unsupported fields are
        provided, because this model inherits strict validation behavior from
        ``StrictModel``.

    Notes
    -----
    Relative humidity normalization is handled automatically after regular
    validation using ``normalize_rh``. This allows configuration files to use
    either fractions or percentages without changing the internal
    representation expected by the rest of the system.

    This model is purely declarative. It does not compute humidity ratio,
    transform coordinates, or perform any rendering directly.

    See Also
    --------
    normalize_rh
        Utility function used to normalize relative humidity values.
    StrictModel
        Strict base configuration model shared by all configuration sections.

    Examples
    --------
    Create a point using fractional relative humidity:

    >>> p = Point(t=25.0, rh=0.60, label="Reference")
    >>> p.t
    25.0
    >>> p.rh
    0.6

    Create a point using percentage relative humidity:

    >>> p = Point(t=30.0, rh=65, color="red", marker="s")
    >>> p.rh
    0.65
    >>> p.marker
    's'

    Disable label rendering explicitly:

    >>> p = Point(t=22.0, rh=50, label="A", show_label=False)
    >>> p.show_label
    False
    """

    # Dry-bulb temperature coordinate of the point on the chart.
    t: float

    # Relative humidity associated with the point. This value is normalized to
    # the fractional domain [0, 1] after validation.
    rh: float

    # Optional human-readable label shown near the point.
    label: Optional[str] = None

    # Marker appearance controls.
    marker: str = "o"
    color: str = "k"
    size: float = 20.0
    alpha: float = 1.0

    # Drawing order and label visibility.
    zorder: int = 5
    show_label: bool = True
    
    
    @field_validator("rh", mode="before")
    @classmethod
    def validate_rh(cls, value: float) -> float:
        """
        Validate and normalize a raw relative humidity value before field parsing.
    
        This validator is executed in ``before`` mode, which means it receives the
        raw input exactly as provided in the configuration source before Pydantic
        applies the standard field coercion logic.
    
        The main purpose of this validator is to ensure that the ``rh`` field is
        always normalized to the canonical fractional domain ``[0, 1]``, while
        still accepting the two most common user-facing conventions for relative
        humidity:
    
        - fraction, such as ``0.65``
        - percentage, such as ``65``
    
        Parameters
        ----------
        value : float
            Raw relative humidity value.
    
            This value may be provided either as a fraction in ``[0, 1]`` or as a
            percentage in ``[0, 100]``.
    
        Returns
        -------
        float
            Relative humidity normalized to the fractional interval ``[0, 1]``.
    
        Raises
        ------
        ValueError
            Raised indirectly by ``normalize_rh`` if the value is outside the valid
            relative humidity domain after normalization.
    
        Notes
        -----
        Using a field validator in ``before`` mode is appropriate here because the
        goal is semantic normalization of the raw input, not just post-processing
        of an already parsed value.
    
        This keeps the model's internal representation consistent and ensures that
        all downstream code can safely assume ``rh`` is always stored as a
        fraction.
    
        See Also
        --------
        normalize_rh
            Utility function that converts relative humidity values to the
            canonical fractional representation.
    
        Examples
        --------
        Percentage input is converted automatically:
    
        >>> validate_rh(None, 65)
        0.65
    
        Fractional input is preserved:
    
        >>> validate_rh(None, 0.65)
        0.65
    
        Boundary values are accepted:
    
        >>> validate_rh(None, 0)
        0.0
        >>> validate_rh(None, 100)
        1.0
        """
        # Delegate all semantic normalization rules to the shared helper so the
        # relative humidity convention remains consistent across the configuration
        # system.
        return normalize_rh(value)
