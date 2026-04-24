from __future__ import annotations

from .cta_trajectory import build_cta_trajectory


TEMPORAL_OVERLAY_REGISTRY = {
    "CTA_TRAJECTORY": build_cta_trajectory,
}
