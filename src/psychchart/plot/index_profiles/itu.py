# psychchart/plot/index_profiles/itu.py

"""
Semantic profile for the Temperature–Humidity Index (ITU).

This module defines the **canonical semantic and visual profile**
for the ITU (Índice de Temperatura e Umidade), widely used to assess
thermal stress conditions, especially in livestock and human comfort
studies.

The profile specifies:
- classification thresholds (levels),
- associated colors for visualization,
- human-readable labels for interpretation.

This file contains **no computation logic**.
It only defines *how ITU values should be interpreted and visualized*.
"""

from .base import IndexProfile


# =============================================================================
# ITU semantic profile
# =============================================================================
ITU_PROFILE = IndexProfile(
    # ------------------------------------------------------------------
    # Index identifier
    # ------------------------------------------------------------------
    # Must match the identifier used by:
    # - IndexConfig.name
    # - IndexField.index
    # - index computation backend (ITU.compute)
    name="ITU",

    # ------------------------------------------------------------------
    # Classification thresholds
    # ------------------------------------------------------------------
    # These values define the numeric boundaries used to classify
    # ITU values into stress categories.
    #
    # Intervals defined by these levels:
    #   [  0, 72 ) → Sem estresse
    #   [ 72, 78 ) → Estresse leve
    #   [ 78, 84 ) → Estresse moderado
    #   [ 84, 90 ) → Estresse severo
    #   [ 90, ∞  ) → Fatal
    #
    # The upper bound (200) is intentionally exaggerated to
    # guarantee coverage of all physically plausible values.
    levels = [0, 72, 78, 84, 90, 200],
    
    # ------------------------------------------------------------------
    # Colors associated with each interval
    # ------------------------------------------------------------------
    # Classic thermal stress palette for livestock:
    #   green  → comfort
    #   yellow → alert
    #   orange → danger
    #   red    → severe
    #   dark red → critical / fatal
    #
    # One color per interval (len = len(levels) - 1)
    colors = [
        "#1a9850",  # Sem estresse (verde)
        "#fee08b",  # Estresse leve (amarelo)
        "#fdae61",  # Estresse moderado (laranja)
        "#d73027",  # Estresse severo (vermelho)
        "#7f0000",  # Fatal (vermelho escuro)
    ],

    # ------------------------------------------------------------------
    # Human-readable labels
    # ------------------------------------------------------------------
    # These labels can be used for:
    # - legends
    # - annotations
    # - reports
    # - automatic captions
    labels=[
        "Confort",
        "Warning",
        "Danger",
        "Extreme",
        "Fatal",
    ],
)

