import matplotlib.pyplot as plt
import numpy as np
import pytest

from psychchart.config.intervention_zones import (
    ComfortReferenceConfig,
    InterventionConditionConfig,
    InterventionRuleConfig,
    InterventionZonesConfig,
)
from psychchart.plot.intervention_zones import (
    condition_mask,
    draw_intervention_zones,
    physical_grid,
    rule_center_from_condition,
)


def test_intervention_condition_requires_at_least_one_predicate():
    """An intervention condition without predicates is ambiguous."""
    with pytest.raises(ValueError):
        InterventionConditionConfig()


def test_comfort_reference_validates_bounds():
    """Comfort reference bounds must be ordered when provided."""
    with pytest.raises(ValueError):
        ComfortReferenceConfig(t_min=30.0, t_max=20.0)

    with pytest.raises(ValueError):
        ComfortReferenceConfig(w_min=0.020, w_max=0.010)


def test_condition_mask_combines_temperature_and_humidity_predicates():
    """Rule masks should combine T and W predicates with logical AND."""
    T = np.array([[20.0, 30.0], [35.0, 40.0]])
    W = np.array([[0.010, 0.018], [0.022, 0.030]])
    condition = InterventionConditionConfig(t_gte=30.0, w_gte=0.020)

    mask = condition_mask(T, W, condition)

    assert mask.tolist() == [[False, False], [True, True]]


def test_inappropriate_rules_are_normalized():
    """Rules declared under inappropriate_rules should be marked accordingly."""
    cfg = InterventionZonesConfig(
        inappropriate_rules=[
            InterventionRuleConfig(
                name="avoid_evaporative",
                label="Avoid evaporative cooling",
                when=InterventionConditionConfig(t_gte=30.0, w_gte=0.020),
            )
        ]
    )

    assert cfg.inappropriate_rules[0].kind == "inappropriate"
    assert cfg.all_rules[0].kind == "inappropriate"


def test_rule_center_from_condition_uses_threshold_bounds():
    """Rule center should be estimated from active threshold bounds."""
    rule = InterventionRuleConfig(
        name="ventilation",
        label="Ventilation",
        when=InterventionConditionConfig(t_gte=28.0, t_lt=36.0, w_lt=0.020),
    )

    x, y = rule_center_from_condition(
        rule,
        t_min=10.0,
        t_max=45.0,
        w_min=0.0,
        w_max=0.035,
    )

    assert x == pytest.approx(32.0)
    assert y == pytest.approx(0.010)


def test_physical_grid_can_clip_above_saturation():
    """Grid clipping should mask humidity-ratio values above saturation."""
    T, W = physical_grid(
        t_min=10.0,
        t_max=20.0,
        w_min=0.0,
        w_max=0.080,
        pressure=101325.0,
        n_t=8,
        n_w=8,
        clip_to_saturation=True,
    )

    assert T.shape == (8, 8)
    assert W.shape == (8, 8)
    assert np.isnan(W).any()


def test_draw_intervention_zones_smoke():
    """Renderer should draw recommended and inappropriate rules without failing."""
    fig, ax = plt.subplots()
    ax.set_xlim(10.0, 45.0)
    ax.set_ylim(0.0, 0.035)

    cfg = InterventionZonesConfig(
        n_t=32,
        n_w=24,
        rules=[
            InterventionRuleConfig(
                name="ventilation",
                label="Ventilation",
                when=InterventionConditionConfig(t_gte=28.0, w_lt=0.020),
                vector=(-3.0, 0.0),
                facecolor="#A8E67A",
                edgecolor="#5B8F3A",
            )
        ],
        inappropriate_rules=[
            InterventionRuleConfig(
                name="avoid_evaporative",
                label="Avoid evaporative",
                reason="hot and humid",
                when=InterventionConditionConfig(t_gte=30.0, w_gte=0.020),
                hatch="///",
                facecolor="#fdae61",
                edgecolor="#7f0000",
            )
        ],
    )

    try:
        artists = draw_intervention_zones(ax, cfg, pressure=101325.0)
        assert artists
        text_values = {text.get_text() for text in ax.texts}
        assert "Ventilation" in text_values
        assert "Avoid evaporative\nhot and humid" in text_values
    finally:
        plt.close(fig)
