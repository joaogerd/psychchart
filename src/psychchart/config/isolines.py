"""
Isoline configuration models for psychchart.

This module defines the typed configuration models used to represent semantic
families of isolines in the ``psychchart`` package.

An isoline family groups together contour values that share the same meaning
and visual role, such as relative humidity, enthalpy, specific volume, or
dry-bulb temperature. The models in this module keep those definitions
declarative, strongly typed, and semantically normalized so the rendering
pipeline can work with a consistent internal representation.

The main goal of this module is to provide a clean configuration contract for
isoline definitions, independent of the plotting backend.

Notes
-----
This module belongs to the configuration layer.

It is responsible for:
- validating isoline-family definitions
- storing contour values and style attributes
- normalizing semantic values such as relative humidity
- exposing a reusable typed representation of isolines

It is not responsible for:
- contour generation
- line drawing
- psychrometric transformations
- figure rendering

See Also
--------
app
    Root configuration model that aggregates isoline families.
base
    Shared strict configuration base model.
utils
    Utility helpers used for semantic normalization.
chart
    Chart-level configuration used together with isoline definitions.

Examples
--------
Define a generic isoline family:

>>> iso = IsoSet(
...     name="enthalpy",
...     values=[20.0, 40.0, 60.0],
...     color="gray",
...     linestyle="--",
... )
>>> iso.name
'enthalpy'
>>> iso.values
[20.0, 40.0, 60.0]

Relative humidity values are normalized automatically:

>>> iso = IsoSet(
...     name="relative_humidity",
...     values=[30, 50, 70],
... )
>>> iso.values
[0.3, 0.5, 0.7]
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field, field_validator

from .base import StrictModel
from .utils import normalize_rh


class IsoSet(StrictModel):
    """
    Definition of a family of isolines.

    This model describes one semantic isoline family used by the psychrometric
    chart renderer. An isoline family groups together a set of contour values
    that share the same meaning and visual style, such as relative humidity,
    enthalpy, specific volume, or dry-bulb temperature.

    The goal of this model is to keep semantic configuration declarative and
    strongly typed, avoiding ad hoc dictionaries scattered across the loader
    and plotting pipeline.

    Parameters
    ----------
    name : str
        Semantic identifier of the isoline family.

        This identifier is used as the canonical key for the family across the
        configuration and rendering pipeline. Examples include
        ``"relative_humidity"`` and other registered isoline types.
    enabled : bool or None, optional
        Whether the isoline family is enabled.

        If ``None``, the runtime or the merged profile configuration may decide
        the effective behavior.
    values : list of float, optional
        Numerical isoline values associated with this family.

        These values define the contour levels to be rendered. Their semantic
        interpretation depends on the family ``name``. For example, relative
        humidity values may be given either as fractions or percentages and are
        normalized automatically.
    color : str or None, optional
        Fixed line color for the family.
    linewidth : float or None, optional
        Width of the isoline strokes.
    linestyle : str or None, optional
        Matplotlib-compatible line style, such as ``"-"``, ``"--"``, or
        ``":"``.
    alpha : float or None, optional
        Line opacity for the isolines.
    cmap : str or None, optional
        Optional colormap name.

        This may be used when the isoline family is colored according to its
        levels instead of using a single fixed color.
    labels : bool or None, optional
        Whether text labels should be drawn on the isolines.
    label_fontsize : int or None, optional
        Font size used for isoline labels.
    label_fmt : str or None, optional
        Format string used to build isoline labels.

        This is typically consumed by the plotting layer to produce labels such
        as percentages or family-specific formatted values.

    Returns
    -------
    IsoSet
        Validated and semantically normalized isoline family configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported fields
        are passed, because this class inherits strict validation behavior from
        ``StrictModel``.

    Notes
    -----
    A special semantic normalization rule applies when
    ``name == "relative_humidity"``:

    - values expressed as fractions, such as ``0.5``, are accepted
    - values expressed as percentages, such as ``50``, are also accepted
    - all values are normalized internally to the fractional interval
      ``[0, 1]``

    This behavior is useful because relative humidity is commonly represented
    in both conventions across scientific datasets and YAML configuration
    files.

    See Also
    --------
    normalize_rh
        Utility function used to normalize relative humidity values.
    StrictModel
        Strict base configuration model used across the package.

    Examples
    --------
    Define a generic isoline family:

    >>> iso = IsoSet(
    ...     name="enthalpy",
    ...     values=[20.0, 40.0, 60.0],
    ...     color="gray",
    ...     linewidth=0.8,
    ...     linestyle="--",
    ... )
    >>> iso.name
    'enthalpy'
    >>> iso.values
    [20.0, 40.0, 60.0]

    Relative humidity values are normalized automatically:

    >>> iso = IsoSet(
    ...     name="relative_humidity",
    ...     values=[30, 50, 70],
    ... )
    >>> iso.values
    [0.3, 0.5, 0.7]

    Fractional relative humidity values are preserved:

    >>> iso = IsoSet(
    ...     name="relative_humidity",
    ...     values=[0.3, 0.5, 0.7],
    ... )
    >>> iso.values
    [0.3, 0.5, 0.7]
    """

    # -------------------------------------------------------------------------
    # Semantic identity
    # -------------------------------------------------------------------------
    # The name is the canonical semantic identifier of the isoline family.
    # It tells the rest of the system what these values mean.
    name: str

    # -------------------------------------------------------------------------
    # Activation and contour levels
    # -------------------------------------------------------------------------
    # ``enabled`` controls whether the family should be rendered.
    # ``values`` stores the actual contour levels associated with the family.
    enabled: Optional[bool] = None
    values: List[float] = Field(default_factory=list)

    # -------------------------------------------------------------------------
    # Visual line styling
    # -------------------------------------------------------------------------
    # These fields define the base line appearance of the isolines.
    color: Optional[str] = None
    linewidth: Optional[float] = None
    linestyle: Optional[str] = None
    alpha: Optional[float] = None
    cmap: Optional[str] = None

    # -------------------------------------------------------------------------
    # Label styling
    # -------------------------------------------------------------------------
    # These fields control whether labels are shown and how they are formatted.
    labels: Optional[bool] = None
    label_fontsize: Optional[int] = None
    label_fmt: Optional[str] = None
    
    @field_validator("values", mode="before")
    @classmethod
    def validate_values(cls, value: Any, info):
        """
        Validate and normalize raw isoline values before standard field parsing.
    
        This validator is executed in ``before`` mode, meaning it receives the raw
        input exactly as provided in the configuration source, before Pydantic
        coerces it into the declared target type.
    
        Its main responsibilities are:
    
        - convert ``None`` into an empty list for convenience,
        - apply semantic normalization for the ``relative_humidity`` isoline
          family, allowing both fractional and percentage inputs,
        - leave all other isoline families unchanged so they can be parsed
          normally by Pydantic afterward.
    
        Parameters
        ----------
        value : Any
            Raw value provided for the ``values`` field.
    
            This is typically expected to be an iterable of numeric values, but
            because this validator runs before standard parsing, the input may
            still be in any raw form accepted by the configuration source.
        info : pydantic.ValidationInfo
            Validation context object provided by Pydantic.
    
            The ``info.data`` mapping contains already available sibling fields
            for the current model. In this validator, it is used to inspect the
            isoline family ``name`` so the normalization behavior can be made
            semantic rather than purely structural.
    
        Returns
        -------
        Any
            Preprocessed value ready for normal Pydantic parsing.
    
            The returned value is:
    
            - ``[]`` when the raw input is ``None``,
            - a list of normalized fractional RH values when
              ``name == "relative_humidity"``,
            - the original raw value for all other isoline families.
    
        Raises
        ------
        ValueError
            Raised indirectly by ``normalize_rh`` if a relative humidity value
            falls outside the accepted domain after normalization.
    
        Notes
        -----
        This validator is intentionally written in ``mode="before"`` because
        semantic normalization of relative humidity is easier and safer when done
        on the raw user input before the final list typing is enforced.
    
        A key design detail is that normalization depends on the sibling field
        ``name``. This allows the same ``values`` field to remain generic for all
        isoline families while still supporting special behavior for
        ``relative_humidity``.
    
        See Also
        --------
        normalize_rh
            Utility function used to normalize relative humidity values into the
            fractional domain ``[0, 1]``.
        pydantic.field_validator
            Pydantic decorator used to define field-level validators.
    
        Examples
        --------
        Normalize relative humidity percentages:
    
        >>> class Dummy:
        ...     pass
        >>> info = Dummy()
        >>> info.data = {"name": "relative_humidity"}
        >>> validate_values(None, [30, 50, 70], info)
        [0.3, 0.5, 0.7]
    
        Preserve non-RH values as provided:
    
        >>> info.data = {"name": "enthalpy"}
        >>> validate_values(None, [10, 20, 30], info)
        [10, 20, 30]
    
        Convert ``None`` into an empty list:
    
        >>> info.data = {"name": "relative_humidity"}
        >>> validate_values(None, None, info)
        []
        """
        # A missing ``values`` field is normalized to an empty list so downstream
        # code can work with a predictable collection type rather than having to
        # handle ``None`` as a special case.
        if value is None:
            return []
    
        # Relative humidity isolines are a semantic special case because users may
        # provide values either as fractions (0.5) or percentages (50). We inspect
        # the sibling ``name`` field to detect that isoline family and normalize
        # every entry to the canonical fractional representation.
        if info.data.get("name") == "relative_humidity":
            return [normalize_rh(v) for v in value]
    
        # For every other isoline family, the raw value is returned unchanged and
        # will be parsed normally by Pydantic according to the declared field type.
        return value
