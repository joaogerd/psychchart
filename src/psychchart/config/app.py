"""
Root configuration model for psychchart.

This module defines the top-level validated application configuration used by
the ``psychchart`` package.

It provides the canonical entry point for configuration validation after the
base profile and user YAML documents have been loaded and deep-merged. The
root model centralizes the structure of the full configuration document and
connects all major configuration sections, including chart settings, isolines,
zones, points, indexes, observations, and temporal overlays.

The main goal of this module is to ensure that the rest of the codebase can
operate on a stable, strongly typed, and semantically normalized configuration
object instead of raw nested dictionaries.

Notes
-----
This module is part of the configuration layer only.

It is responsible for:
- validating the overall configuration structure
- normalizing supported legacy shapes
- coercing nested sections into typed models
- exposing a consistent root configuration contract

It is not responsible for:
- file I/O
- YAML parsing
- plotting
- psychrometric calculations
- runtime rendering

See Also
--------
chart
    Chart-level configuration models.
isolines
    Typed models for isoline families.
indexes
    Typed models for thermal or psychrometric indexes.
observations
    Dataset-oriented observation models.
overlays
    Temporal overlay configuration models.
zones
    Geometric and semantic zone models.
points
    Reference-point configuration models.

Examples
--------
Validate a minimal application configuration:

>>> raw = {
...     "chart": {
...         "t_min": 0,
...         "t_max": 40,
...         "pressure": 101325,
...         "xlabel": "Dry-bulb temperature (°C)",
...         "ylabel": "Humidity ratio (kg/kg)",
...         "output": "chart.png",
...         "dpi": 150,
...     },
...     "isolines": {
...         "relative_humidity": {
...             "values": [30, 50, 70]
...         }
...     },
... }
>>> cfg = AppConfig.model_validate(raw)
>>> cfg.chart.t_min
0.0
>>> cfg.isolines["relative_humidity"].values
[0.3, 0.5, 0.7]
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field, model_validator

from .base import StrictModel
from .chart import ChartConfig
from .indexes import IndexConfig
from .observations import ObservationsConfig
from .overlays import TemporalOverlayConfig
from .points import Point
from .zones import Zone, IndexZone
from .isolines import IsoSet


class AppConfig(StrictModel):
    """
    Root validated application configuration for ``psychchart``.

    This model represents the fully resolved configuration document after
    the following pipeline has been completed:

    1. A base profile YAML is loaded.
    2. A user YAML is loaded.
    3. Both documents are deep-merged.
    4. The merged structure is validated and normalized by this model.
    5. The validated data is converted into the payload expected by the
       runtime chart object.

    The class acts as the canonical entry point for configuration validation.
    It centralizes the shape of the application configuration and absorbs a
    limited set of legacy formats so the rest of the codebase can operate on
    a stable and strongly typed structure.

    Parameters
    ----------
    chart : ChartConfig
        Chart-level configuration, including axes limits, labels, output
        settings, pressure, and other top-level plotting options.
    isolines : dict of str to IsoSet, optional
        Dictionary of isoline families keyed by their semantic identifier.
        Each value describes one isoline set, such as relative humidity,
        enthalpy, specific volume, or dry-bulb temperature.
    zones : list of Zone, optional
        List of geometric zones drawn on the psychrometric chart.
    points : list of Point, optional
        List of annotated reference points to be displayed on the chart.
    indexes : list of IndexConfig, optional
        List of computed index configurations, such as ITU/THI or custom
        indices, including rendering options.
    index_zones : list of IndexZone, optional
        List of semantic zones derived from index intervals.
    observations : list of ObservationsConfig, optional
        List of observational datasets to be plotted on the chart.
    temporal_overlays : list of TemporalOverlayConfig, optional
        List of temporal trajectory overlays, typically used to represent
        time-evolving observations or animal/environmental histories.

    Returns
    -------
    AppConfig
        A validated and normalized root configuration object.

    Raises
    ------
    TypeError
        Raised by pre-validation when the top-level configuration is not a
        mapping or when a legacy structure has the wrong type.
    ValueError
        Raised by pre-validation when a required legacy key is missing, such
        as an isoline entry without a ``name`` field.

    Notes
    -----
    This model is a configuration model, not a plotting engine and not a
    numerical solver.

    Responsibilities include:

    - validating the structure of the full configuration
    - coercing nested dictionaries into typed Pydantic models
    - normalizing supported legacy configuration formats
    - producing a runtime payload compatible with the current chart API

    Responsibilities explicitly excluded from this class include:

    - file I/O
    - YAML loading
    - plotting execution
    - psychrometric calculations
    - numerical evaluation of thermal indices

    Legacy normalization currently supports:

    - ``isolines`` provided as a list of dictionaries instead of a mapping
    - ``indexes`` using legacy ``name`` instead of ``index``
    - flat legacy rendering fields remapped into nested ``render`` sections

    See Also
    --------
    ChartConfig
        Model that defines chart-level configuration.
    IsoSet
        Model representing one isoline family.
    IndexConfig
        Model describing a computed psychrometric or thermal index.
    to_runtime_payload
        Method that converts the validated model into the runtime contract.

    Examples
    --------
    Validate a complete configuration dictionary:

    >>> raw = {
    ...     "chart": {
    ...         "t_min": 0,
    ...         "t_max": 50,
    ...         "pressure": 101325,
    ...         "xlabel": "Dry-bulb temperature (°C)",
    ...         "ylabel": "Humidity ratio (kg/kg)",
    ...         "output": "chart.png",
    ...         "dpi": 150,
    ...     },
    ...     "isolines": {
    ...         "relative_humidity": {
    ...             "values": [30, 50, 70]
    ...         }
    ...     },
    ... }
    >>> cfg = AppConfig.model_validate(raw)
    >>> cfg.isolines["relative_humidity"].values
    [0.3, 0.5, 0.7]

    Legacy isolines given as a list are normalized automatically:

    >>> raw = {
    ...     "chart": {
    ...         "t_min": 0,
    ...         "t_max": 40,
    ...         "pressure": 101325,
    ...         "xlabel": "T",
    ...         "ylabel": "W",
    ...         "output": "out.png",
    ...         "dpi": 100,
    ...     },
    ...     "isolines": [
    ...         {"name": "relative_humidity", "values": [40, 60, 80]}
    ...     ],
    ... }
    >>> cfg = AppConfig.model_validate(raw)
    >>> list(cfg.isolines)
    ['relative_humidity']
    """

    # -------------------------------------------------------------------------
    # Core top-level sections
    # -------------------------------------------------------------------------
    # These fields define the canonical structure of the merged and validated
    # application configuration.
    chart: ChartConfig
    isolines: Dict[str, IsoSet] = Field(default_factory=dict)
    zones: List[Zone] = Field(default_factory=list)
    points: List[Point] = Field(default_factory=list)
    indexes: List[IndexConfig] = Field(default_factory=list)
    index_zones: List[IndexZone] = Field(default_factory=list)
    observations: List[ObservationsConfig] = Field(default_factory=list)
    temporal_overlays: List[TemporalOverlayConfig] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_shapes(cls, data: Any) -> Any:
        """
        Normalize supported legacy configuration shapes before validation.

        This validator runs before standard field parsing and is responsible
        for transforming a small set of historical configuration layouts into
        the canonical structure expected by the strongly typed models.

        Supported transformations include:

        - converting ``isolines`` from list form to dict form
        - injecting the isoline key as the canonical ``name``
        - converting legacy index key ``name`` into ``index``
        - remapping flat legacy rendering fields into nested ``render``
          structures

        Parameters
        ----------
        data : Any
            Raw merged configuration object, typically obtained from the
            deep-merge of a base profile and a user configuration file.

        Returns
        -------
        Any
            A normalized mapping ready for standard Pydantic validation.

        Raises
        ------
        TypeError
            If the top-level configuration is not a mapping/dict, if
            ``isolines`` has an unsupported type, or if a legacy item is not
            a mapping.
        ValueError
            If a legacy isoline entry does not define the required ``name``
            field.

        Notes
        -----
        This method is intentionally conservative: it supports a limited set of
        compatibility transformations while still enforcing a clear and
        maintainable canonical configuration shape for the rest of the system.

        Examples
        --------
        Normalize legacy isolines stored as a list:

        >>> raw = {
        ...     "chart": {"t_min": 0, "t_max": 10, "pressure": 101325,
        ...               "xlabel": "T", "ylabel": "W",
        ...               "output": "x.png", "dpi": 100},
        ...     "isolines": [{"name": "relative_humidity", "values": [50]}],
        ... }
        >>> normalized = AppConfig.normalize_legacy_shapes(raw)
        >>> "relative_humidity" in normalized["isolines"]
        True

        Normalize a legacy index using ``name`` instead of ``index``:

        >>> raw = {
        ...     "chart": {"t_min": 0, "t_max": 10, "pressure": 101325,
        ...               "xlabel": "T", "ylabel": "W",
        ...               "output": "x.png", "dpi": 100},
        ...     "indexes": [{"name": "ITU", "mode": "filled", "colorbar": True}],
        ... }
        >>> normalized = AppConfig.normalize_legacy_shapes(raw)
        >>> normalized["indexes"][0]["index"]
        'ITU'
        """
        # The root of the application configuration must be a mapping. This is
        # the minimum structural contract required for all subsequent parsing.
        if not isinstance(data, dict):
            raise TypeError("Top-level configuration must be a mapping/dict")

        # ------------------------------------------------------------------
        # Legacy isolines normalization
        # ------------------------------------------------------------------
        # Historically, isolines may have been defined as a list of entries:
        #
        #   isolines:
        #     - name: relative_humidity
        #       values: [...]
        #
        # The canonical representation is now a mapping keyed by semantic name:
        #
        #   isolines:
        #     relative_humidity:
        #       values: [...]
        #
        # This conversion removes ambiguity and makes downstream lookup much
        # simpler and more efficient.
        raw_isolines = data.get("isolines", {})

        if isinstance(raw_isolines, list):
            normalized: Dict[str, Dict[str, Any]] = {}

            for item in raw_isolines:
                if not isinstance(item, dict):
                    raise TypeError("Each isoline entry must be a mapping/dict")

                name = item.get("name")
                if not name:
                    raise ValueError(
                        "Each legacy isoline entry must define 'name'"
                    )

                # The dict key becomes the structural identity of the isoline.
                # We keep a copy of the original mapping to avoid mutating the
                # input item directly.
                normalized[name] = dict(item)

            data["isolines"] = normalized

        elif raw_isolines is None:
            # Treat explicit null as an empty mapping for convenience and to
            # simplify downstream code.
            data["isolines"] = {}

        elif not isinstance(raw_isolines, dict):
            raise TypeError("'isolines' must be a mapping/dict or a list")

        # Even in canonical dict form, the key is the authoritative semantic
        # identity. We inject it into each nested object as ``name`` so the
        # nested Pydantic model can validate it as a regular typed field.
        data["isolines"] = {
            key: {"name": key, **value}
            for key, value in data.get("isolines", {}).items()
        }

        # ------------------------------------------------------------------
        # Legacy indexes normalization
        # ------------------------------------------------------------------
        # Older configurations may use:
        # - ``name`` instead of ``index``
        # - flat rendering attributes at the same level as the index config
        #
        # Newer configurations group rendering information under a nested
        # ``render`` section. We normalize older shapes here so the rest of the
        # application only needs to reason about one structure.
        normalized_indexes: List[Dict[str, Any]] = []

        for raw_idx in data.get("indexes", []):
            if not isinstance(raw_idx, dict):
                raise TypeError("Each index entry must be a mapping/dict")

            # Copy to avoid mutating the original user-provided structure.
            idx = dict(raw_idx)

            # Backward compatibility: promote legacy ``name`` to canonical
            # ``index`` when necessary.
            if "index" not in idx and "name" in idx:
                idx["index"] = idx["name"]

            # Only synthesize ``render`` when it is absent. If the user already
            # provided the modern nested structure, we preserve it as-is.
            if idx.get("render") is None:
                legacy_mode = idx.get("mode")

                has_legacy_isoline_fields = any(
                    key in idx
                    for key in (
                        "isoline_levels",
                        "style",
                        "color",
                        "linewidth",
                        "alpha",
                        "label",
                        "label_fontsize",
                        "label_fmt",
                    )
                )

                has_legacy_field_fields = "colorbar" in idx

                # Legacy isoline rendering fields are grouped under
                # ``render["isolines"]``.
                if legacy_mode == "isolines" or has_legacy_isoline_fields:
                    idx["render"] = {
                        "isolines": {
                            "levels": idx.get("isoline_levels"),
                            "style": idx.get("style"),
                            "color": idx.get("color"),
                            "linewidth": idx.get("linewidth"),
                            "alpha": idx.get("alpha"),
                            "label": idx.get("label"),
                            "label_fontsize": idx.get("label_fontsize"),
                            "label_fmt": idx.get("label_fmt"),
                        }
                    }

                # Legacy filled-field rendering options are grouped under
                # ``render["field"]``.
                elif legacy_mode == "filled" or has_legacy_field_fields:
                    idx["render"] = {
                        "field": {
                            "alpha": idx.get("alpha"),
                            "colorbar": idx.get("colorbar"),
                        }
                    }

            normalized_indexes.append(idx)

        data["indexes"] = normalized_indexes
        return data

    def to_runtime_payload(self) -> Dict[str, Any]:
        """
        Convert the validated model into the payload expected by the runtime.

        The plotting runtime currently expects the chart configuration under
        the key ``cfg`` rather than ``chart``. This method preserves that
        contract while exposing all other validated sections in their already
        normalized form.

        Returns
        -------
        dict of str to Any
            Dictionary compatible with the current runtime initialization
            pattern, typically something conceptually equivalent to
            ``PsychChart(**data)``.

        Notes
        -----
        The returned structure is an integration boundary between the validated
        configuration layer and the runtime plotting API.

        A subtle but important detail is that the isoline dictionary key remains
        the structural source of truth for identity. For safety and consistency,
        each nested ``IsoSet`` object is copied with its ``name`` field forced
        to match the corresponding dictionary key.

        See Also
        --------
        AppConfig
            Root configuration model that owns this conversion.
        normalize_legacy_shapes
            Pre-validation step that ensures canonical internal structure.

        Examples
        --------
        >>> raw = {
        ...     "chart": {
        ...         "t_min": 0,
        ...         "t_max": 50,
        ...         "pressure": 101325,
        ...         "xlabel": "Dry-bulb temperature (°C)",
        ...         "ylabel": "Humidity ratio (kg/kg)",
        ...         "output": "chart.png",
        ...         "dpi": 150,
        ...     }
        ... }
        >>> cfg = AppConfig.model_validate(raw)
        >>> payload = cfg.to_runtime_payload()
        >>> "cfg" in payload
        True
        >>> "chart" in payload
        False
        """
        return {
            # The runtime still expects the chart section under the legacy key
            # ``cfg``. This method isolates that compatibility concern so the
            # rest of the configuration code can keep the clearer name
            # ``chart`` internally.
            "cfg": self.chart,
            "isolines": {
                # The dictionary key is the authoritative identity of each
                # isoline family. We therefore force the nested object's
                # ``name`` field to match the key before handing it to the
                # runtime layer.
                key: value.model_copy(update={"name": key})
                for key, value in self.isolines.items()
            },
            "zones": self.zones,
            "points": self.points,
            "indexes": self.indexes,
            "index_zones": self.index_zones,
            "observations": self.observations,
            "temporal_overlays": self.temporal_overlays,
        }
