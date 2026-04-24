"""
Legend configuration models for psychchart.

This module defines the typed configuration models used to describe chart
legends in the ``psychchart`` package.

It provides declarative models for manually defined legend entries and for
global legend assembly settings. These models make it possible to describe
legend content, styling, and layout in a structured and validated way, keeping
legend behavior consistent with the rest of the configuration system.

The main purpose of this module is to provide a strongly typed and declarative
configuration contract for legend-related chart elements.

Notes
-----
This module belongs to the configuration layer.

It is responsible for:
- validating chart-level legend configuration
- defining declarative legend entry models
- supporting patch, line, marker, and colormap-marker legend semantics
- storing layout and typography options for legend rendering

It is not responsible for:
- collecting runtime Matplotlib handles
- drawing the legend
- resolving renderer state
- plotting chart elements

See Also
--------
base
    Shared strict configuration base model.
chart
    Chart-level configuration models used together with legend settings.
points
    Configuration model for annotated point elements that may appear in legends.
paths
    Configuration model for trajectories that may contribute line semantics.
zones
    Configuration models for area-based regions that may contribute patch
    semantics.

Examples
--------
Create a legend with manual entries:

>>> legend = LegendConfig(
...     show=True,
...     title="Chart legend",
...     entries=[
...         LegendPatchEntry(label="Comfort", facecolor="#7fc97f"),
...         LegendLineEntry(label="ITU isoline", color="black"),
...         LegendMarkerEntry(label="Observations", marker="o"),
...     ],
... )
>>> legend.show
True
>>> len(legend.entries)
3
"""

from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import Field, field_validator

from .base import StrictModel


# =============================================================================
# Declarative legend models
# =============================================================================
class LegendPatchEntry(StrictModel):
    """
    Declarative patch legend entry.

    This model represents a filled legend element, usually associated with
    polygonal or area-based semantics such as comfort zones, warning regions,
    or fatigue regions.

    Parameters
    ----------
    type : {"patch"}, default="patch"
        Discriminator used by Pydantic to identify this legend entry variant
        inside the ``LegendEntry`` discriminated union.
    label : str
        Human-readable label shown in the legend.
    facecolor : str
        Fill color of the legend patch, typically any Matplotlib-compatible
        color specification.
    edgecolor : str, default="none"
        Border color of the legend patch.

    Notes
    -----
    Patch entries are useful when the legend must explain colored regions drawn
    with ``fill``, ``fill_between``, ``Polygon``, or similar area-based
    primitives.

    See Also
    --------
    LegendLineEntry
        Legend entry for line-based semantics.
    LegendMarkerEntry
        Legend entry for marker-only semantics.
    LegendMarkerScaleEntry
        Legend entry for compact colormap-based marker semantics.
    LegendConfig
        Global legend assembly model.

    Examples
    --------
    >>> entry = LegendPatchEntry(
    ...     label="Thermal comfort",
    ...     facecolor="#66c2a5",
    ...     edgecolor="black",
    ... )
    >>> entry.type
    'patch'
    >>> entry.label
    'Thermal comfort'
    """

    # The discriminator value allows Pydantic to resolve this class when the
    # user provides a heterogeneous list of legend entries.
    type: Literal["patch"] = "patch"

    # Text displayed to the user in the legend.
    label: str

    # Fill color of the patch handle.
    facecolor: str

    # Optional edge color. "none" is a reasonable default for semantic areas.
    edgecolor: str = "none"


class LegendLineEntry(StrictModel):
    """
    Declarative line legend entry.

    This model represents a line-style legend handle, typically used for
    isolines, trajectories, thresholds, or any semantic element whose visual
    identity is primarily conveyed by stroke properties.

    Parameters
    ----------
    type : {"line"}, default="line"
        Discriminator used by Pydantic to identify this legend entry variant
        inside the ``LegendEntry`` discriminated union.
    label : str
        Human-readable label shown in the legend.
    color : str, default="black"
        Matplotlib-compatible line color.
    alpha : float, default=1.0
        Line opacity.
    linewidth : float, default=1.5
        Width of the legend line handle.
    linestyle : str, default="-"
        Matplotlib line style string.

    Notes
    -----
    This model is especially useful when the legend must expose semantic lines
    that are not automatically harvested from Matplotlib artists.

    See Also
    --------
    LegendPatchEntry
        Legend entry for filled semantic regions.
    LegendMarkerEntry
        Legend entry for point-like semantics.
    LegendMarkerScaleEntry
        Legend entry for compact colormap-based marker semantics.
    LegendConfig
        Global legend assembly model.

    Examples
    --------
    >>> entry = LegendLineEntry(
    ...     label="ITU isoline",
    ...     color="black",
    ...     linewidth=2.0,
    ...     linestyle="--",
    ... )
    >>> entry.linestyle
    '--'
    >>> entry.linewidth
    2.0
    """

    # Discriminator for the legend union.
    type: Literal["line"] = "line"

    # User-facing legend label.
    label: str

    # Default visual choices are intentionally conservative and readable.
    color: str = "black"
    alpha: float = 1.0
    linewidth: float = 1.5
    linestyle: str = "-"


class LegendMarkerEntry(StrictModel):
    """
    Declarative marker-only legend entry.

    This model represents point-like legend semantics, such as observations,
    stations, events, or categorical point layers.

    Parameters
    ----------
    type : {"marker"}, default="marker"
        Discriminator used by Pydantic to identify this legend entry variant
        inside the ``LegendEntry`` discriminated union.
    label : str
        Human-readable label shown in the legend.
    marker : str, default="o"
        Matplotlib marker symbol.
    markerfacecolor : str, default="white"
        Fill color of the marker.
    markeredgecolor : str, default="black"
        Border color of the marker.
    markeredgewidth : float, default=0.8
        Width of the marker border.
    markersize : float, default=7.0
        Marker size used in the legend handle.

    Notes
    -----
    Marker entries are useful when the semantic meaning is tied to individual
    points rather than continuous lines or filled areas.

    See Also
    --------
    LegendPatchEntry
        Legend entry for area-based semantics.
    LegendLineEntry
        Legend entry for line-based semantics.
    LegendMarkerScaleEntry
        Legend entry for compact colormap-based marker semantics.
    LegendConfig
        Global legend assembly model.

    Examples
    --------
    >>> entry = LegendMarkerEntry(
    ...     label="Observations",
    ...     marker="s",
    ...     markerfacecolor="red",
    ... )
    >>> entry.marker
    's'
    >>> entry.markersize
    7.0
    """

    # Discriminator for the legend union.
    type: Literal["marker"] = "marker"

    # User-facing legend label.
    label: str

    # Marker styling mirrors common Matplotlib naming.
    marker: str = "o"
    markerfacecolor: str = "white"
    markeredgecolor: str = "black"
    markeredgewidth: float = 0.8
    markersize: float = 7.0


class LegendMarkerScaleEntry(StrictModel):
    """
    Declarative legend entry representing multiple colored observation markers.

    This configuration model defines a compact legend entry intended for
    point-like layers whose markers are colored by a colormap rather than by a
    single fixed color. Instead of showing only one proxy marker in the legend,
    this entry stores a small sequence of representative scalar samples that can
    later be rendered as multiple colored markers under a single semantic label.

    The main goal of this model is to preserve the visual meaning of
    colormapped observation layers in the legend without requiring a full
    colorbar for every scatter-like dataset.

    Parameters
    ----------
    type : {"marker_scale"}, default="marker_scale"
        Canonical legend entry type identifier.

        This field is used by the legend rendering layer to dispatch the entry
        to the appropriate proxy-artist builder.
    label : str
        Human-readable legend label associated with the marker scale.
    cmap : str, default="viridis"
        Matplotlib colormap name used to color the representative markers.
    samples : list of float, optional
        Ordered representative scalar samples used to select colors from the
        colormap.

        These values must lie in the normalized interval ``[0, 1]``, where:

        - ``0.0`` corresponds to the low end of the colormap
        - ``1.0`` corresponds to the high end of the colormap

        The default values provide a compact low-mid-high visual summary of the
        colormap.
    marker : str, default="o"
        Matplotlib marker style used for each representative sample.
    markeredgecolor : str, default="black"
        Edge color applied to each legend marker.
    markeredgewidth : float, default=0.8
        Edge width applied to each legend marker.
    markersize : float, default=7.0
        Size of each representative legend marker.

    Returns
    -------
    LegendMarkerScaleEntry
        Validated legend entry configuration for a colormapped marker scale.

    Raises
    ------
    ValueError
        If one or more entries in ``samples`` fall outside the interval
        ``[0, 1]``.
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported fields
        are provided, because this model inherits strict validation behavior
        from ``StrictModel``.

    Notes
    -----
    This model is declarative. It does not build the actual Matplotlib legend
    artist by itself. Its responsibility is only to store validated semantic
    and style information required by the legend rendering layer.

    The ``samples`` field is intentionally normalized to the interval
    ``[0, 1]`` because the legend entry is meant to represent positions inside
    a colormap, not raw physical values. The actual mapping from physical
    values to normalized colormap positions should happen upstream.

    See Also
    --------
    LegendMarkerEntry
        Simpler marker legend entry for a single marker style.
    LegendConfig
        Global legend assembly model that can include this entry type.

    Examples
    --------
    Create a default marker-scale legend entry:

    >>> entry = LegendMarkerScaleEntry(label="Observed thermal states")
    >>> entry.type
    'marker_scale'
    >>> entry.samples
    [0.1, 0.5, 0.9]

    Create a custom entry with five representative samples:

    >>> entry = LegendMarkerScaleEntry(
    ...     label="Stress gradient",
    ...     cmap="plasma",
    ...     samples=[0.0, 0.25, 0.5, 0.75, 1.0],
    ...     marker="s",
    ...     markersize=8.0,
    ... )
    >>> entry.cmap
    'plasma'
    >>> len(entry.samples)
    5
    """

    # -------------------------------------------------------------------------
    # Semantic identity
    # -------------------------------------------------------------------------
    # ``type`` is the canonical discriminator used by the legend-entry union.
    # It is fixed because this class represents one specific legend-entry kind.
    type: Literal["marker_scale"] = "marker_scale"

    # Human-readable label displayed next to the compact marker scale.
    label: str

    # -------------------------------------------------------------------------
    # Colormap summary
    # -------------------------------------------------------------------------
    # ``cmap`` identifies the colormap to sample.
    # ``samples`` stores normalized positions inside that colormap.
    cmap: str = "viridis"
    samples: List[float] = Field(default_factory=lambda: [0.1, 0.5, 0.9])

    # -------------------------------------------------------------------------
    # Marker appearance
    # -------------------------------------------------------------------------
    # These settings define the visual style of each representative marker
    # rendered inside the compact legend handle.
    marker: str = "o"
    markeredgecolor: str = "black"
    markeredgewidth: float = 0.8
    markersize: float = 7.0

    @field_validator("samples")
    @classmethod
    def validate_samples(cls, value: List[float]) -> List[float]:
        """
        Validate normalized colormap sample positions.

        Parameters
        ----------
        value : list of float
            Candidate normalized sample positions inside the colormap.

        Returns
        -------
        list of float
            Validated sample positions.

        Raises
        ------
        ValueError
            If one or more sample values fall outside the interval ``[0, 1]``.

        Notes
        -----
        The values stored in ``samples`` are normalized colormap coordinates,
        not raw physical measurements. Therefore, every element must remain
        inside the closed interval ``[0, 1]``.

        Examples
        --------
        >>> LegendMarkerScaleEntry.validate_samples([0.1, 0.5, 0.9])
        [0.1, 0.5, 0.9]

        >>> LegendMarkerScaleEntry.validate_samples([0.0, 1.0])
        [0.0, 1.0]
        """
        # Validate every representative colormap sample so downstream legend
        # rendering can safely assume normalized colormap coordinates.
        for sample in value:
            if not (0.0 <= sample <= 1.0):
                raise ValueError(
                    "Legend marker-scale samples must lie in the interval [0, 1]."
                )

        # Preserve the declared order because the legend renderer may display
        # the samples from left to right following this exact sequence.
        return value

class LegendClassesFromProfileEntry(StrictModel):
    """
    Declarative legend entry that expands semantic classes from a profile.

    This configuration model defines a legend entry whose visible items are not
    specified manually one by one, but instead derived from a named semantic
    profile. The intended use case is to keep legend construction consistent
    with profile-driven classification systems, where the same profile already
    defines ordered classes, labels, and colors used elsewhere in the chart.

    Rather than duplicating those classes in the legend YAML, this entry acts as
    a declarative request saying: "build legend rows from the semantic classes
    of this profile".

    Parameters
    ----------
    type : {"classes_from_profile"}, default="classes_from_profile"
        Canonical legend entry type identifier.

        This discriminator is used by the legend-entry union and by the legend
        assembly layer to route this entry to the corresponding expansion logic.
    profile : str
        Name of the semantic profile whose classes should be expanded into
        legend entries.

        This value is expected to match a profile identifier known by the
        profile registry or runtime profile-resolution layer.

    Returns
    -------
    LegendClassesFromProfileEntry
        Validated declarative legend entry requesting class expansion from a
        semantic profile.

    Raises
    ------
    pydantic.ValidationError
        Raised when field values have invalid types or when unsupported fields
        are provided, because this model inherits strict validation behavior
        from ``StrictModel``.

    Notes
    -----
    This model is intentionally declarative and does not resolve the profile by
    itself. Its responsibility is only to store the semantic request in a typed
    and validated form.

    The actual expansion step is expected to happen later in the legend
    assembly/runtime layer, which may use the referenced profile to generate
    one or more patch/line/marker legend rows depending on profile semantics.

    This approach has two main advantages:

    - it avoids duplicating semantic class definitions in multiple places
    - it keeps the legend synchronized with the same profile used by fields,
      isolines, or classified renderers

    See Also
    --------
    LegendPatchEntry
        Declarative legend entry for filled semantic regions.
    LegendLineEntry
        Declarative legend entry for line-based semantics.
    LegendMarkerEntry
        Declarative legend entry for point-like semantics.
    LegendConfig
        Global chart-level legend configuration that can aggregate this entry.

    Examples
    --------
    Create a legend entry that expands classes from the ITU profile:

    >>> entry = LegendClassesFromProfileEntry(profile="ITU")
    >>> entry.type
    'classes_from_profile'
    >>> entry.profile
    'ITU'

    Create a legend entry for another semantic profile:

    >>> entry = LegendClassesFromProfileEntry(profile="TE")
    >>> entry.profile
    'TE'
    """

    # Fixed discriminator used by the legend-entry union and runtime dispatch.
    type: Literal["classes_from_profile"] = "classes_from_profile"

    # Name of the semantic profile whose classes should be expanded into legend
    # items by the legend assembly layer.
    profile: str

# ``LegendEntry`` is a discriminated union. Pydantic will inspect the ``type``
# field and instantiate the correct model automatically.
LegendEntry = Annotated[
    Union[
        LegendPatchEntry,
        LegendLineEntry,
        LegendMarkerEntry,
        LegendMarkerScaleEntry,
        LegendClassesFromProfileEntry,
    ],
    Field(discriminator="type"),
]


class LegendConfig(StrictModel):
    """
    Global declarative legend configuration.

    This model centralizes chart-level legend assembly. Instead of forcing each
    renderer to manage its own legend state, the chart can collect automatic
    handles and combine them with optional declarative entries defined here.

    Parameters
    ----------
    show : bool, default=False
        Whether the legend should be drawn.
    loc : str, default="best"
        Matplotlib legend location string.
    title : str or None, optional
        Optional legend title.
    frameon : bool, default=True
        Whether a legend frame should be drawn.
    fancybox : bool, default=True
        Whether the legend frame should use rounded corners.
    framealpha : float, default=0.95
        Opacity of the legend frame.
    borderpad : float, default=0.8
        Padding between legend content and frame.
    labelspacing : float, default=0.6
        Vertical spacing between legend rows.
    handlelength : float, default=2.2
        Length of line handles in the legend.
    handletextpad : float, default=0.8
        Padding between handle and label text.
    borderaxespad : float, default=0.8
        Padding between the legend and the axes boundary.
    fontsize : float, default=9.0
        Font size of legend labels.
    title_fontsize : float, default=10.0
        Font size of the legend title.
    entries : list of LegendEntry, optional
        Manually declared legend entries appended after automatically collected
        renderer handles.

    Notes
    -----
    The legend is intentionally modeled as a chart-level concern because this
    avoids duplicated assembly logic across independent renderers and keeps YAML
    configuration easier to reason about.

    The ``entries`` field uses a discriminated union, so each item must contain
    a ``type`` key with one of the following values:

    - ``"patch"``
    - ``"line"``
    - ``"marker"``
    - ``"marker_scale"``

    See Also
    --------
    LegendPatchEntry
        Filled legend entry.
    LegendLineEntry
        Line legend entry.
    LegendMarkerEntry
        Marker legend entry.
    LegendMarkerScaleEntry
        Compact colormap-marker legend entry.

    Examples
    --------
    >>> legend = LegendConfig(
    ...     show=True,
    ...     loc="upper right",
    ...     title="Legend",
    ...     entries=[
    ...         LegendPatchEntry(label="Comfort", facecolor="#66c2a5"),
    ...         LegendLineEntry(label="Trajectory", color="blue"),
    ...         LegendMarkerEntry(label="Station", marker="^"),
    ...         LegendMarkerScaleEntry(label="Stress gradient"),
    ...     ],
    ... )
    >>> legend.show
    True
    >>> len(legend.entries)
    4
    """

    # A disabled-by-default legend is safer for generic charts, because some
    # charts may not need one or may prefer automatic artist labels only.
    show: bool = False

    # Matplotlib legend placement keyword.
    loc: str = "best"

    # Optional title shown above the legend entries.
    title: Optional[str] = None

    # Frame options are exposed because they are often adjusted in publications.
    frameon: bool = True
    fancybox: bool = True
    framealpha: float = 0.95

    # Spacing controls help keep the legend readable across dense figures.
    borderpad: float = 0.8
    labelspacing: float = 0.6
    handlelength: float = 2.2
    handletextpad: float = 0.8
    borderaxespad: float = 0.8

    # Typography options are kept explicit to make exported figures more stable.
    fontsize: float = 9.0
    title_fontsize: float = 10.0

    # ``default_factory=list`` avoids sharing a mutable default across
    # instances, which is essential for safe model reuse.
    entries: List[LegendEntry] = Field(default_factory=list)
