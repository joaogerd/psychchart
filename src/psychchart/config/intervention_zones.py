"""Configuration models for psychrometric intervention zones."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .base import StrictModel


class ComfortReferenceConfig(StrictModel):
    """Reference rectangle used to document the target comfort region."""

    t_min: float | None = None
    t_max: float | None = None
    w_min: float | None = None
    w_max: float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "ComfortReferenceConfig":
        """Validate optional comfort-reference bounds."""
        if self.t_min is not None and self.t_max is not None and self.t_min >= self.t_max:
            raise ValueError("comfort_reference.t_min must be smaller than t_max")
        if self.w_min is not None and self.w_max is not None and self.w_min >= self.w_max:
            raise ValueError("comfort_reference.w_min must be smaller than w_max")
        return self


class InterventionConditionConfig(StrictModel):
    """Threshold predicates evaluated in dry-bulb temperature and humidity ratio."""

    t_lt: float | None = None
    t_lte: float | None = None
    t_gt: float | None = None
    t_gte: float | None = None
    w_lt: float | None = None
    w_lte: float | None = None
    w_gt: float | None = None
    w_gte: float | None = None

    @model_validator(mode="after")
    def validate_predicates(self) -> "InterventionConditionConfig":
        """Require at least one active predicate."""
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("An intervention condition must define at least one predicate")
        return self


class InterventionLabelConfig(StrictModel):
    """Optional text placement and style for an intervention rule."""

    enabled: bool = True
    position: tuple[float, float] | None = None
    fontsize: float = 9.0
    color: str = "black"
    alpha: float = Field(default=0.78, ge=0.0, le=1.0)
    fontweight: str | None = None
    ha: str = "center"
    va: str = "center"


class InterventionVectorStyleConfig(StrictModel):
    """Visual style for a physical displacement vector."""

    enabled: bool = True
    color: str = "black"
    alpha: float = Field(default=0.58, ge=0.0, le=1.0)
    linewidth: float = Field(default=1.1, ge=0.0)
    head_width: float = Field(default=0.00045, gt=0.0)
    head_length: float = Field(default=0.35, gt=0.0)
    width: float = Field(default=0.000025, gt=0.0)
    position: tuple[float, float] | None = None


class InterventionRuleConfig(StrictModel):
    """One intervention region evaluated as a boolean mask in T-W space."""

    name: str
    label: str
    when: InterventionConditionConfig
    kind: Literal["recommended", "inappropriate"] = "recommended"
    reason: str | None = None
    vector: tuple[float, float] | None = None
    vector_style: InterventionVectorStyleConfig = Field(default_factory=InterventionVectorStyleConfig)
    facecolor: str = "#cccccc"
    edgecolor: str = "#666666"
    alpha: float = Field(default=0.20, ge=0.0, le=1.0)
    linewidth: float = Field(default=0.8, ge=0.0)
    linestyle: str = "-"
    hatch: str | None = None
    label_style: InterventionLabelConfig = Field(default_factory=InterventionLabelConfig)
    priority: int = 0
    zorder: float | None = None


class InterventionZonesConfig(StrictModel):
    """Root configuration for explicit psychrometric intervention zones."""

    enabled: bool = True
    method: Literal["operational_psychrometric"] = "operational_psychrometric"
    comfort_reference: ComfortReferenceConfig | None = None
    n_t: int = Field(default=420, ge=20)
    n_w: int = Field(default=320, ge=20)
    clip_to_saturation: bool = True
    alpha_scale: float = Field(default=1.0, ge=0.0, le=1.0)
    zorder: float = 1.35
    inappropriate_zorder: float = 1.70
    label_zorder: float = 4.60
    vector_zorder: float = 4.70
    show_labels: bool = True
    show_vectors: bool = True
    show_boundaries: bool = True
    rules: list[InterventionRuleConfig] = Field(default_factory=list)
    inappropriate_rules: list[InterventionRuleConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_inappropriate_rules(self) -> "InterventionZonesConfig":
        """Force rules declared under inappropriate_rules to the inappropriate kind."""
        for rule in self.inappropriate_rules:
            rule.kind = "inappropriate"
        return self

    @property
    def all_rules(self) -> list[InterventionRuleConfig]:
        """Return all rules sorted by priority."""
        return sorted([*self.rules, *self.inappropriate_rules], key=lambda item: item.priority)
