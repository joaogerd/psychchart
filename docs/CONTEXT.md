# PsychChart – Architectural Context

## Purpose
Scientific psychrometric chart engine with support for:
- classical psychrometric isolines
- geometric comfort zones
- bioclimatic indexes (ITU, HLI, etc.)
- continuous index fields clipped to saturation curve

## Core Design Principles
- Imperative rendering pipeline (Matplotlib-style)
- Clear semantic layering via zorder
- No circular imports
- Index computation decoupled from visualization
- All psychrometric logic centralized in Psychrometrics

## Rendering Order (zorder)
index_field   -> background (heatmaps)
isolines      -> psychrometric isolines
zones         -> comfort zones
points        -> reference points
saturation    -> 100% RH curve (top)

## ITU Index
- Formula: Thom (1959), Fahrenheit-based
- Input: T [°C], RH [0–1]
- Used in:
  - index isolines
  - index fields (psychrometric space)
- Canonical thresholds:
  < 72  : no stress
  72–78 : mild stress
  78–84 : moderate stress
  > 84  : severe / fatal

## Known Decisions
- Index fields are computed in (T, RH) space,
  then mapped to (T, W)
- Fields are clipped to saturation curve
- Zones follow RH curves when follow_rh = true

