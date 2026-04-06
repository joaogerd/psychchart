from __future__ import annotations

from .itu import ITU
from .iti import ITI
from .hli import HLI
from .icf import ICF
from .thermal_excess import ThermalExcess

# =============================================================================
# Central registry of available indexes
# =============================================================================
INDEX_REGISTRY = {
    ITU.name: ITU,
    ITI.name: ITI,
    HLI.name: HLI,
    ICF.name: ICF,
    ThermalExcess.name: ThermalExcess,
}
