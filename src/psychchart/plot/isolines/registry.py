"""
Central registry for psychrometric isoline handlers.

This module defines the **mapping between isoline family identifiers**
and their corresponding low-level drawing functions (handlers).

Each handler is responsible for:
- computing the isoline geometry,
- applying physical masks (e.g. saturation limits),
- drawing the isoline on a Matplotlib axis.

Design philosophy
-----------------
This registry acts as a **dispatcher lookup table**, enabling the
rendering pipeline to remain fully generic and declarative.

It allows:
- isoline families to be added or removed without touching the dispatcher,
- clean separation between orchestration and numerical logic,
- avoidance of ``if/elif`` chains in rendering code.

This module does NOT:
- resolve styling defaults,
- place labels,
- validate configuration.

Those responsibilities live elsewhere in the pipeline.
"""

from .handlers import (
    draw_relative_humidity,
    draw_enthalpy,
    draw_wet_bulb,
    draw_specific_volume,
    draw_moisture_quantity,
)

from .labels import (
        label_relative_humidity,
        label_enthalpy,
)

# =============================================================================
# Isoline handler registry
# =============================================================================
# Keys:
#   Canonical isoline family names (strings)
#
# Values:
#   Callable handler functions with signature:
#
#       handler(ax, T, W_sat, cfg, st)
#
# Where:
#   - ax     : matplotlib.axes.Axes
#   - T      : temperature array (°C)
#   - W_sat  : saturation humidity ratio
#   - cfg    : ChartConfig
#   - st     : resolved style dictionary
#
# This mapping is intentionally explicit and flat.
ISOLINE_HANDLERS = {
    "relative_humidity": draw_relative_humidity,
    "enthalpy": draw_enthalpy,
    "wet_bulb": draw_wet_bulb,
    "specific_volume": draw_specific_volume,
    "moisture_quantity": draw_moisture_quantity,
}

LABEL_HANDLERS = {
    "relative_humidity": label_relative_humidity,
    "enthalpy": label_enthalpy,
}
