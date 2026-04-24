"""
Root configuration model for psychchart.

This module defines the top-level validated application configuration used by
the ``psychchart`` package.

It provides the canonical entry point for configuration validation after the
base profile and user YAML documents have been loaded and deep-merged. The
root model centralizes the structure of the full configuration document and
connects all major configuration sections, including chart settings, isolines,
zones, points, indexes, legacy observations, legacy temporal overlays, and the
canonical unified ``data_layers`` section.

The main goal of this module is to ensure that the rest of the codebase can
operate on a stable, strongly typed, and semantically normalized configuration
object instead of raw nested dictionaries.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field, model_validator

from .base import StrictModel
from .chart import ChartConfig
from .data_layers import DataLayerConfig
from .indexes import IndexConfig
from .observations import ObservationsConfig
from .overlays import TemporalOverlayConfig
from .points import Point
from .zones import Zone, IndexZone
from .isolines import IsoSet
from .operations import (
    DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME,
    OperationalOverlayConfig,
    OperationalProfileConfig,
    default_dairy_operational_profile,
)


# =============================================================================
# Legacy compatibility helpers
# =============================================================================
def _observation_to_data_layer(obs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert one legacy ``observations`` entry into a canonical data layer.
    """
    fields: List[Dict[str, Any]] = []
    render: List[Dict[str, Any]] = []

    for idx_cfg in obs.get("data_indexes", []):
        index_name = idx_cfg["index"]

        if index_name == "ICF":
            fields.append(
                {
                    "type": "data_index",
                    "name": index_name,
                    "index": index_name,
                    "source_col": "behavior",
                    "parameters": {},
                }
            )
        else:
            fields.append(
                {
                    "type": "direct_column",
                    "name": index_name,
                    "col": index_name,
                }
            )

        if idx_cfg.get("scatter", True):
            render.append(
                {
                    "type": "scatter",
                    "value": index_name,
                    "cmap": idx_cfg.get("cmap", "viridis"),
                    "size": 20.0,
                    "alpha": idx_cfg.get("alpha", 0.6),
                    "edgecolor": "black",
                    "edgewidth": 0.3,
                    "colorbar": idx_cfg.get("colorbar", True),
                    "zorder": 45,
                }
            )

        if idx_cfg.get("scalar_field", False):
            render.append(
                {
                    "type": "scalar_field",
                    "value": index_name,
                    "bins": idx_cfg.get("bins", (40, 40)),
                    "cmap": idx_cfg.get("cmap", "viridis"),
                    "alpha": idx_cfg.get("alpha", 0.6),
                    "colorbar": idx_cfg.get("colorbar", True),
                    "zorder": 25,
                }
            )

    density = obs.get("density")
    if density is not None:
        render.append(
            {
                "type": "density",
                "bins": density.get("bins", (60, 60)),
                "cmap": density.get("cmap", "viridis"),
                "vmin": density.get("vmin"),
                "vmax": density.get("vmax"),
                "alpha": density.get("alpha", 0.6),
                "colorbar": density.get("colorbar", True),
                "normalize": density.get("normalize", True),
                "zorder": 20,
            }
        )

    return {
        "data": obs["file"],
        "format": obs.get("format", "parquet"),
        "projection": {
            "t_col": "T",
            "rh_col": "RH",
            "rh_unit": "auto",
        },
        "fields": fields,
        "render": render,
    }


def _temporal_to_data_layer(overlay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert one legacy ``temporal_overlays`` entry into a canonical data layer.
    """
    render: List[Dict[str, Any]] = []

    if overlay.get("show_path", True):
        render.append(
            {
                "type": "path",
                "order_by": overlay["time_col"],
                "color": overlay.get("path_color", "blue"),
                "alpha": overlay.get("path_alpha", 0.6),
                "linewidth": overlay.get("path_linewidth", 1.2),
                "zorder": overlay.get("path_zorder", 20),
            }
        )

    render.append(
        {
            "type": "scatter",
            "value": "CTA",
            "cmap": "viridis",
            "size": overlay.get("point_size", 42.0),
            "alpha": 1.0,
            "edgecolor": overlay.get("point_edgecolor", "black"),
            "edgewidth": overlay.get("point_edgewidth", 0.8),
            "colorbar": False,
            "zorder": overlay.get("point_zorder", 25),
        }
    )

    annotate_every = overlay.get("annotate_every", 3)
    if annotate_every is not None:
        render.append(
            {
                "type": "annotate",
                "every": annotate_every,
                "template": overlay.get(
                    "annotation_template",
                    "{time}h\n(CTA:{value:.0f})",
                ),
                "time_field": overlay["time_col"],
                "value_field": "CTA",
                "dx": overlay.get("annotation_dx", 0.35),
                "dy": overlay.get("annotation_dy", 0.0005),
                "fontsize": overlay.get("annotation_fontsize", 8.0),
                "fontweight": overlay.get("annotation_fontweight", "bold"),
                "color": overlay.get("annotation_color", "black"),
                "zorder": overlay.get("annotation_zorder", 30),
            }
        )

    return {
        "data": overlay["data"],
        "format": "csv",
        "projection": {
            "t_col": overlay["t_col"],
            "rh_col": overlay["rh_col"],
            "rh_unit": "auto",
        },
        "temporal": {
            "time_col": overlay["time_col"],
            "sort": True,
        },
        "fields": [
            {
                "type": "direct_column",
                "name": "CTA",
                "col": overlay["cta_col"],
            }
        ],
        "render": render,
    }


def _inject_default_operational_profile(data: Dict[str, Any]) -> None:
    """
    Inject the built-in dairy operational profile when it is referenced.

    The operational layer is designed to be declarative, but most examples and
    routine use cases should not need to repeat the full default dairy cooling
    policy. When an overlay references ``dairy_cooling_default`` and the profile
    is not explicitly provided, this helper inserts a validated default mapping
    before Pydantic model validation.
    """
    overlays = data.get("operational_overlays") or []
    if not overlays:
        return

    if not isinstance(overlays, list):
        raise TypeError("'operational_overlays' must be a list when provided")

    profiles = data.get("operational_profiles") or {}
    if not isinstance(profiles, dict):
        raise TypeError("'operational_profiles' must be a mapping/dict when provided")

    default_needed = False
    for overlay in overlays:
        if not isinstance(overlay, dict):
            raise TypeError("Each operational overlay must be a mapping/dict")
        profile_name = overlay.get("profile", DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME)
        if profile_name == DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME:
            default_needed = True

    if default_needed and DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME not in profiles:
        profiles = dict(profiles)
        profiles[DEFAULT_DAIRY_OPERATIONAL_PROFILE_NAME] = default_dairy_operational_profile()
        data["operational_profiles"] = profiles


class AppConfig(StrictModel):
    """
    Root validated application configuration for ``psychchart``.

    The canonical runtime-facing dataset layer is ``data_layers``. Legacy
    ``observations`` and ``temporal_overlays`` are still accepted as input and
    normalized into canonical data-layer definitions when ``data_layers`` is not
    explicitly provided.
    """

    chart: ChartConfig
    isolines: Dict[str, IsoSet] = Field(default_factory=dict)
    zones: List[Zone] = Field(default_factory=list)
    points: List[Point] = Field(default_factory=list)
    indexes: List[IndexConfig] = Field(default_factory=list)
    index_zones: List[IndexZone] = Field(default_factory=list)

    data_layers: List[DataLayerConfig] = Field(default_factory=list)

    observations: List[ObservationsConfig] = Field(default_factory=list)
    temporal_overlays: List[TemporalOverlayConfig] = Field(default_factory=list)

    operational_profiles: dict[str, OperationalProfileConfig] = Field(default_factory=dict)
    operational_overlays: list[OperationalOverlayConfig] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_shapes(cls, data: Any) -> Any:
        """
        Normalize supported legacy configuration shapes before validation.
        """
        if not isinstance(data, dict):
            raise TypeError("Top-level configuration must be a mapping/dict")

        _inject_default_operational_profile(data)

        raw_isolines = data.get("isolines", {})

        if isinstance(raw_isolines, list):
            normalized: Dict[str, Dict[str, Any]] = {}

            for item in raw_isolines:
                if not isinstance(item, dict):
                    raise TypeError("Each isoline entry must be a mapping/dict")

                name = item.get("name")
                if not name:
                    raise ValueError("Each legacy isoline entry must define 'name'")

                normalized[name] = dict(item)

            data["isolines"] = normalized

        elif raw_isolines is None:
            data["isolines"] = {}

        elif not isinstance(raw_isolines, dict):
            raise TypeError("'isolines' must be a mapping/dict or a list")

        data["isolines"] = {
            key: {"name": key, **value}
            for key, value in data.get("isolines", {}).items()
        }

        normalized_indexes: List[Dict[str, Any]] = []

        for raw_idx in data.get("indexes", []):
            if not isinstance(raw_idx, dict):
                raise TypeError("Each index entry must be a mapping/dict")

            idx = dict(raw_idx)

            if "index" not in idx and "name" in idx:
                idx["index"] = idx["name"]

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

                elif legacy_mode == "filled" or has_legacy_field_fields:
                    idx["render"] = {
                        "field": {
                            "alpha": idx.get("alpha"),
                            "colorbar": idx.get("colorbar"),
                        }
                    }

            normalized_indexes.append(idx)

        data["indexes"] = normalized_indexes

        raw_data_layers = data.get("data_layers", None)

        if raw_data_layers is None:
            synthesized_layers: List[Dict[str, Any]] = []

            raw_observations = data.get("observations", []) or []
            if not isinstance(raw_observations, list):
                raise TypeError("'observations' must be a list when provided")

            for item in raw_observations:
                if not isinstance(item, dict):
                    raise TypeError("Each observation entry must be a mapping/dict")
                synthesized_layers.append(_observation_to_data_layer(item))

            raw_temporal = data.get("temporal_overlays", []) or []
            if not isinstance(raw_temporal, list):
                raise TypeError("'temporal_overlays' must be a list when provided")

            for item in raw_temporal:
                if not isinstance(item, dict):
                    raise TypeError("Each temporal overlay entry must be a mapping/dict")
                synthesized_layers.append(_temporal_to_data_layer(item))

            data["data_layers"] = synthesized_layers

        elif not isinstance(raw_data_layers, list):
            raise TypeError("'data_layers' must be a list when provided")

        return data

    def to_runtime_payload(self) -> Dict[str, Any]:
        """
        Convert the validated model into the canonical runtime payload.
        """
        return {
            "cfg": self.chart,
            "isolines": {
                key: value.model_copy(update={"name": key})
                for key, value in self.isolines.items()
            },
            "zones": self.zones,
            "points": self.points,
            "indexes": self.indexes,
            "index_zones": self.index_zones,
            "data_layers": self.data_layers,
            "operational_profiles": self.operational_profiles,
            "operational_overlays": self.operational_overlays,
        }

    @model_validator(mode="after")
    def validate_operational_sections(self):
        """
        Validate references between operational overlays and profiles.
        """
        if not self.operational_overlays:
            return self

        if not self.operational_profiles:
            raise ValueError(
                "operational_overlays were declared, but no operational_profiles "
                "section was provided."
            )

        for overlay in self.operational_overlays:
            if overlay.profile not in self.operational_profiles:
                raise ValueError(
                    f"Operational overlay references unknown profile {overlay.profile!r}."
                )

            profile_cfg = self.operational_profiles[overlay.profile]
            load_class_names = {item.name for item in profile_cfg.load_classes}

            if overlay.load_class not in load_class_names:
                raise ValueError(
                    f"Operational overlay for profile {overlay.profile!r} references "
                    f"unknown load_class {overlay.load_class!r}. "
                    f"Available classes: {sorted(load_class_names)}."
                )

        return self
