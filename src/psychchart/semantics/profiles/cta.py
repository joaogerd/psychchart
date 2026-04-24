from __future__ import annotations

import math

from .base import ClassificationProfile, ClassificationRule


CTA_PROFILE = ClassificationProfile(
    name="CTA",
    rules=(
        ClassificationRule(22.4, "#a1d99b", "Recuperação"),
        ClassificationRule(83.6, "#fdbb84", "Alerta"),
        ClassificationRule(165.2, "#fc8d59", "Crítico"),
        ClassificationRule(math.inf, "#d7301f", "Fadiga térmica"),
    ),
)
