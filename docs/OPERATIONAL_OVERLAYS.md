# Operational overlays

Operational overlays turn a psychrometric chart into a decision-support chart.
They are designed for cases where the question is not only where a point lies
in the T x RH space, but which cooling action should be considered for a given
thermal state.

## Concept

The operational layer is intentionally separated from physical psychrometrics
and from thermal-index definitions.

A complete operational decision may depend on:

- the current dry-bulb temperature;
- the current relative humidity;
- a thermal index such as ITU;
- an accumulated thermal-load class;
- the recent trend of accumulated load;
- explicit management rules.

For this reason, operational overlays are configured through two sections:

```yaml
operational_profiles:
  dairy_cooling_default:
    ...

operational_overlays:
  - profile: dairy_cooling_default
    load_class: A2
    trend: steady
```

The profile defines the policy. The overlay projects one representative state
of that policy onto the psychrometric chart.

Internally, the renderer resolves the validated `OperationalProfile` and uses
the same deterministic decision engine exposed by `psychchart.operations.engine`.
This keeps YAML validation, policy evaluation, colors, labels, legends and
rendered regions tied to a single declarative source of truth.

## Built-in dairy profile

psychChart includes a built-in profile named `dairy_cooling_default`.

For routine examples, the full profile does not need to be repeated. When an
operational overlay omits `profile`, psychChart uses this default profile:

```yaml
operational_overlays:
  - load_class: A2
    trend: steady
    alpha: 0.18
    zorder: 0.55
    show_boundaries: true
```

Define `operational_profiles` explicitly only when a custom management policy
is needed.

A minimal runnable example is available at:

```bash
psychchart examples/operational_overlay_minimal.yaml
```

## Profiles

An operational profile contains:

```yaml
itu_classes:
  - {name: I0, min: null, max: 72.0}
  - {name: I1, min: 72.0, max: 78.0}

humidity_classes:
  - {name: H0, min: 0.00, max: 0.60}
  - {name: H1, min: 0.60, max: 0.75}

load_classes:
  - {name: A2, min: 0.010, max: 0.015, floor_action: O2, representative: 0.0125}
```

The `base_matrix` maps ITU class and humidity class to an operational action:

```yaml
base_matrix:
  I0: {H0: O0, H1: O0, H2: O0}
  I1: {H0: O1, H1: O2, H2: O3}
  I2: {H0: O2, H1: O3, H2: O4}
```

The accumulated-load class enforces a minimum action through `floor_action`.
This prevents a persistent or accumulated heat state from being underestimated
only because the instantaneous T x RH point temporarily improved.

## Actions

The current stable action codes are:

| Code | Meaning |
|---|---|
| O0 | Monitoring |
| O1 | Basic ventilation |
| O2 | Reinforced ventilation |
| O3 | Ventilation plus sprinkling/aspersion |
| O4 | Maximum cooling |
| O5 | Emergency |

Labels and colors are user-configurable:

```yaml
action_styles:
  O0: {label: "Monitoramento", facecolor: "#d9f0d3"}
  O1: {label: "Ventilação básica", facecolor: "#78c679"}
  O2: {label: "Ventilação reforçada", facecolor: "#ffd92f"}
  O3: {label: "Ventilação + aspersão", facecolor: "#fdae61"}
  O4: {label: "Resfriamento máximo", facecolor: "#f46d43"}
  O5: {label: "Emergência", facecolor: "#d73027"}
```

These style definitions are also used by the overlay renderer for categorical
filled regions, colorbars and legends.

## Modifiers

Modifiers escalate or de-escalate the base action.

Examples:

```yaml
modifiers:
  high_temp_humidity:
    temp_ge: 30.0
    rh_ge: 0.75
    add_levels: 1

  rising_load:
    dca_dt_gt: 0.001
    add_levels: 1

  recovery:
    dca_dt_lt: -0.001
    ca_lt: 0.010
    itu_lt: 78.0
    add_levels: -1
```

This makes the policy dynamic: the same T x RH point can receive different
actions depending on accumulated load and trend.

For static overlays, `trend` is converted to a representative derivative:

| trend | representative `dca_dt` |
|---|---:|
| falling | -0.002 |
| steady | 0.000 |
| rising | 0.002 |

This allows the same declarative decision engine to be used both for static
chart overlays and future time-series operational diagnostics.

## Rendering

Operational overlays are rendered as clean classified regions using filled
contours. This avoids the fine raster texture that appears when categorical
decision grids are rendered with individual quadrilateral cells.

Example:

```yaml
operational_overlays:
  - profile: dairy_cooling_default
    load_class: A2
    trend: steady
    alpha: 0.18
    zorder: 0.55
    show_boundaries: true
```

The overlay should normally be drawn with moderate transparency so it can be
combined with ITU isolines, observed trajectories, and accumulated-load point
classes.

## Interpretation

Operational overlays do not replace physiological thresholds. They translate a
thermal state into a management action according to an explicit policy.

The recommended interpretation is:

1. Use ITU/HLI/BGHI/TE fields to understand instantaneous thermal intensity.
2. Use observed trajectories and accumulated-load classes to understand the
   temporal burden on the animal.
3. Use operational overlays to interpret which cooling response is consistent
   with the declared management policy.

This separation keeps the chart scientifically auditable and avoids confusing
observed environmental envelopes, physiological thresholds, accumulated load,
and management decisions.
