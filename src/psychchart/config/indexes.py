"""
Index configuration models for psychchart.

This module defines the typed configuration models used to describe computed
psychrometric or thermal indexes in the ``psychchart`` package.

It provides the semantic and rendering configuration for derived quantities
such as THI, ITU, thermal excess, and other registered indexes. The models in
this module organize index identity, numerical parameters, threshold levels,
colormap settings, and rendering options such as scalar fields and isolines.

The main purpose of this module is to keep index-related configuration
structured, reusable, and independent from procedural parsing logic in the
loader or plotting layers.

Notes
-----
This module is declarative and validation-oriented.

It is responsible for:
- validating computed-index configuration
- organizing rendering options for fields and isolines
- normalizing supported legacy index fields
- storing index parameters and semantic thresholds

It is not responsible for:
- numerical index computation
- psychrometric grid generation
- contour rendering
- colorbar creation

See Also
--------
app
    Root configuration model that aggregates configured indexes.
base
    Shared strict configuration base model.
chart
    Chart-level configuration used together with index settings.
observations
    Dataset-driven visualization settings that may complement computed indexes.

Examples
--------
Define an index with isolines:

>>> cfg = IndexConfig(
...     index="ITU",
...     label="ITU",
...     levels=[72, 78, 84],
... )
>>> cfg.index
'ITU'
>>> cfg.levels
[72.0, 78.0, 84.0]

Define an index with explicit render sections:

>>> cfg = IndexConfig(
...     index="THI",
...     render={
...         "field": {"alpha": 0.6, "colorbar": True},
...         "isolines": {"levels": [68, 72, 78], "color": "black"},
...     },
... )
>>> cfg.render.field.colorbar
True
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel


class FieldRenderConfig(StrictModel):
    """
    Rendering options for a continuous index field.

    This model stores the visual configuration used when an index is rendered
    as a filled or continuous scalar field over the psychrometric domain.
    Typical examples include thermal comfort maps, stress intensity
    backgrounds, or any gridded index visualization where color represents
    the magnitude of the computed index.

    Parameters
    ----------
    alpha : float or None, optional
        Opacity of the rendered field layer.

        Typical values are in the interval ``[0, 1]`` where:

        - ``0`` means fully transparent
        - ``1`` means fully opaque

        If ``None``, the plotting layer may apply a profile default or an
        internal renderer default.
    colorbar : bool or None, optional
        Whether a colorbar should be displayed for the field.

        If ``True``, the renderer is expected to expose a scale describing the
        mapping between colors and index values. If ``None``, the decision may
        be delegated to higher-level configuration or runtime defaults.

    Returns
    -------
    FieldRenderConfig
        Validated field rendering configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or when unexpected keys are
        supplied, because this class inherits strict validation behavior from
        ``StrictModel``.

    Notes
    -----
    This model is intentionally minimal. It describes only the field-specific
    rendering parameters that are commonly needed across different thermal or
    psychrometric index visualizations.

    More specialized styling options can be added later without changing the
    semantic role of this class.

    See Also
    --------
    IsolineRenderConfig
        Rendering options for contour-line representations of an index.
    IndexRenderConfig
        Composite rendering model that groups field and isoline options.

    Examples
    --------
    Create a semi-transparent field with a colorbar:

    >>> cfg = FieldRenderConfig(alpha=0.65, colorbar=True)
    >>> cfg.alpha
    0.65
    >>> cfg.colorbar
    True

    Create a configuration with unspecified options:

    >>> cfg = FieldRenderConfig()
    >>> cfg.alpha is None
    True
    """

    # Opacity of the continuous scalar field. This is useful when the field
    # must coexist visually with isolines, points, trajectories, or annotated
    # zones without overwhelming them.
    alpha: Optional[float] = None

    # Whether the renderer should display a colorbar associated with the field.
    # A colorbar is generally desirable for quantitative interpretation.
    colorbar: Optional[bool] = None


class IsolineRenderConfig(StrictModel):
    """
    Rendering options for index isolines.

    This model defines the visual properties used when a computed index is
    rendered as contour lines instead of, or in addition to, a continuous
    field. Isolines are especially useful when the user wants to emphasize
    threshold structure, semantic levels, or interpretable contour labels.

    Parameters
    ----------
    levels : list of float or None, optional
        Explicit contour levels to be rendered.

        When provided, these values define the exact index thresholds at which
        contour lines should be drawn.
    style : str or None, optional
        Matplotlib-compatible line style, such as ``"-"``, ``"--"``, ``":"``,
        or ``"-."``.
    color : str or None, optional
        Fixed line color used for the isolines.

        If ``None``, the plotting layer may fall back to another coloring
        strategy or use a default profile.
    linewidth : float or None, optional
        Width of the contour lines.
    alpha : float or None, optional
        Opacity of the isolines.
    label : bool or None, optional
        Whether numeric or semantic labels should be drawn on the contour
        lines.
    label_fontsize : int or None, optional
        Font size used for contour labels.
    label_fmt : str or None, optional
        Format string used to build contour labels.

        This is typically consumed by the plotting layer to generate readable
        labels such as ``"THI = 72"`` or ``"ITU = 78"``.

    Returns
    -------
    IsolineRenderConfig
        Validated isoline rendering configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when one or more field values have invalid types or when
        unexpected keys are provided.

    Notes
    -----
    Isolines are often the most interpretable representation when working with
    threshold-based thermal indices. This model keeps those rendering options
    grouped in a single semantic object so they can be reused consistently
    across profiles and renderers.

    See Also
    --------
    FieldRenderConfig
        Rendering configuration for continuous fields.
    IndexRenderConfig
        Composite rendering configuration that may include isolines.

    Examples
    --------
    Create labeled black isolines at fixed thresholds:

    >>> cfg = IsolineRenderConfig(
    ...     levels=[72, 78, 84],
    ...     style="-",
    ...     color="black",
    ...     linewidth=0.5,
    ...     alpha=0.8,
    ...     label=True,
    ...     label_fontsize=8,
    ...     label_fmt="{index} = {value:.0f}",
    ... )
    >>> cfg.levels
    [72, 78, 84]
    >>> cfg.label
    True

    Create a minimal configuration relying mostly on defaults:

    >>> cfg = IsolineRenderConfig(style="--")
    >>> cfg.style
    '--'
    """

    # Explicit contour levels are important when the scientific meaning of the
    # isolines depends on domain thresholds rather than automatic spacing.
    levels: Optional[List[float]] = None

    # Line style used by Matplotlib for contour rendering.
    style: Optional[str] = None

    # Fixed line color. Keeping this optional allows profiles or renderers to
    # define color strategies elsewhere.
    color: Optional[str] = None

    # Thickness of the contour lines.
    linewidth: Optional[float] = None

    # Opacity of the contour lines.
    alpha: Optional[float] = None

    # Whether to annotate contour lines with labels.
    label: Optional[bool] = None

    # Font size for the contour labels, when enabled.
    label_fontsize: Optional[int] = None

    # Formatting template for contour labels.
    label_fmt: Optional[str] = None


class IndexRenderConfig(StrictModel):
    """
    Composite rendering configuration for an index.

    This model groups the two main visual representations supported for a
    computed psychrometric or bioclimatic index:

    - a continuous scalar field
    - contour isolines

    The separation into nested objects is intentional. It allows the same
    index to be rendered in multiple ways while keeping the configuration
    semantically organized and easy to evolve.

    Parameters
    ----------
    field : FieldRenderConfig or None, optional
        Continuous field rendering configuration.

        If provided, the index may be rendered as a filled background or
        gridded scalar layer.
    isolines : IsolineRenderConfig or None, optional
        Isoline rendering configuration.

        If provided, the index may also be rendered as contour lines.

    Returns
    -------
    IndexRenderConfig
        Validated composite rendering configuration.

    Raises
    ------
    pydantic.ValidationError
        Raised when nested rendering sections are invalid or when unknown keys
        are supplied.

    Notes
    -----
    This model does not impose that both rendering modes be present. A given
    index may be configured with only a field, only isolines, or both.

    See Also
    --------
    FieldRenderConfig
        Rendering settings for continuous fields.
    IsolineRenderConfig
        Rendering settings for contour lines.
    IndexConfig
        Higher-level configuration object that owns the rendering section.

    Examples
    --------
    Configure an index with both field and isolines:

    >>> cfg = IndexRenderConfig(
    ...     field=FieldRenderConfig(alpha=0.6, colorbar=True),
    ...     isolines=IsolineRenderConfig(levels=[72, 78, 84], color="black"),
    ... )
    >>> cfg.field.colorbar
    True
    >>> cfg.isolines.levels
    [72, 78, 84]

    Configure an index with isolines only:

    >>> cfg = IndexRenderConfig(
    ...     isolines=IsolineRenderConfig(style="--", label=True)
    ... )
    >>> cfg.field is None
    True
    """

    # Continuous field rendering block.
    field: Optional[FieldRenderConfig] = None

    # Isoline rendering block.
    isolines: Optional[IsolineRenderConfig] = None


class IndexConfig(BaseModel):
    """
    Configuration of a computed thermal or bioclimatic index.

    This model defines the semantic and rendering configuration for an index
    evaluated over the psychrometric chart domain, such as THI, ITU, thermal
    excess, or other derived indicators.

    The class intentionally accepts a limited set of legacy fields so that old
    YAML configurations can still be loaded and normalized without requiring
    procedural parsing logic in the loader layer.

    Parameters
    ----------
    index : str or None, optional
        Canonical index identifier.

        This is the preferred modern field name and should match the runtime
        registry name expected by the computation backend.
    name : str or None, optional
        Legacy alias for ``index``.

        This field is preserved only for backward compatibility.
    label : str or None, optional
        Human-readable label used in legends, labels, or annotations.
    parameters : dict of str to Any, optional
        Index-specific parameters passed to the computation backend.

        This dictionary is useful for configurable formulas or parameterized
        derived indices.
    levels : list of float or None, optional
        Explicit contour or classification levels associated with the index.

        These may be used by field normalization, contour generation, semantic
        categorization, or legend construction depending on the renderer.
    cmap : str or None, optional
        Matplotlib colormap name used when rendering the index as a continuous
        field.
    vmin : float or None, optional
        Lower normalization bound for continuous rendering.
    vmax : float or None, optional
        Upper normalization bound for continuous rendering.
    render : IndexRenderConfig or None, optional
        Nested rendering configuration that describes how the index should be
        visualized.

    Returns
    -------
    IndexConfig
        Validated and normalized index configuration.

    Raises
    ------
    ValueError
        Raised during post-validation if neither ``index`` nor legacy ``name``
        is available.
    pydantic.ValidationError
        Raised when field types are invalid or when nested rendering sections
        fail validation.

    Notes
    -----
    Unlike the stricter configuration classes, this model uses
    ``extra="allow"`` intentionally. The reason is backward compatibility:
    older configuration documents may still contain legacy rendering keys that
    are normalized earlier in the root model before the final structure is
    fully stabilized.

    Legacy flat rendering keys are expected to be normalized in ``AppConfig``
    before field validation completes.

    See Also
    --------
    IndexRenderConfig
        Composite rendering configuration for fields and isolines.
    AppConfig
        Root configuration model responsible for legacy normalization.

    Examples
    --------
    Define a modern index configuration:

    >>> cfg = IndexConfig(
    ...     index="ITU",
    ...     label="Temperature-Humidity Index",
    ...     levels=[72, 78, 84],
    ...     cmap="Spectral_r",
    ...     vmin=68,
    ...     vmax=95,
    ...     render=IndexRenderConfig(
    ...         field=FieldRenderConfig(alpha=0.65, colorbar=True)
    ...     ),
    ... )
    >>> cfg.index
    'ITU'
    >>> cfg.render.field.colorbar
    True

    Define a legacy configuration using ``name``:

    >>> cfg = IndexConfig(name="THI")
    >>> cfg.index
    'THI'
    """

    # ``extra="allow"`` is deliberate here because this model plays a
    # transitional compatibility role for legacy configuration documents.
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        populate_by_name=True,
    )

    # Canonical identifier used by the runtime index registry.
    index: Optional[str] = None

    # Legacy alias preserved for backward compatibility. It is normalized into
    # ``index`` after validation.
    name: Optional[str] = None

    # Human-readable label used in plots, legends, or annotations.
    label: Optional[str] = None

    # Arbitrary index-specific parameters. Keeping this as a dictionary allows
    # flexible support for parameterized index definitions without procedural
    # parsing in the loader.
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Explicit numerical levels associated with the index.
    levels: Optional[List[float]] = None

    # Colormap name used for continuous field rendering.
    cmap: Optional[str] = None

    # Lower and upper bounds for normalization of continuous fields.
    vmin: Optional[float] = None
    vmax: Optional[float] = None

    # Nested rendering configuration for field and/or isolines.
    render: Optional[IndexRenderConfig] = None

    @model_validator(mode="after")
    def normalize(self) -> "IndexConfig":
        """
        Normalize legacy aliases after validation.

        This validator ensures that the canonical field ``index`` is always
        populated whenever a valid legacy ``name`` is present. It also enforces
        that an index definition cannot exist without any semantic identifier.

        Returns
        -------
        IndexConfig
            The normalized model instance.

        Raises
        ------
        ValueError
            If neither ``index`` nor legacy ``name`` is available after
            validation.

        Notes
        -----
        This post-validation step centralizes one of the most important
        backward-compatibility rules in the configuration system: old files may
        still use ``name``, but the validated internal representation should
        consistently prefer ``index``.

        Examples
        --------
        Legacy alias is promoted automatically:

        >>> cfg = IndexConfig(name="ITU")
        >>> cfg.index
        'ITU'

        Missing both identifiers is invalid:

        >>> IndexConfig()
        Traceback (most recent call last):
            ...
        pydantic_core._pydantic_core.ValidationError: ...
        """
        # Backward compatibility rule: if the user only provided the legacy
        # alias ``name``, promote it to the canonical ``index`` field.
        if not self.index and self.name:
            self.index = self.name

        # Every index configuration must end up with a canonical identifier.
        # Without that, the runtime cannot resolve the computation backend.
        if not self.index:
            raise ValueError(
                "Each index entry must define 'index' or legacy 'name'"
            )

        return self
