"""
Visual integration test for PsychChart.

This script validates:
- points
- psychrometric path
- indexed (ITU) colored path
- density field

Run:
    python examples/visual_test_full.py
"""

import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# PsychChart imports
# ---------------------------------------------------------------------
from psychchart.chart import PsychChart
from psychchart.config import ChartConfig, Zone
from psychchart.data.config import ObservationsConfig
from psychchart.data.observations import Observations
from psychchart.config import PathConfig
from psychchart.config import DensityFieldConfig
from psychchart.density import DensityField

# Index (adjust import if needed)
from psychchart.indexes.itu import ITUIndex


# =====================================================================
# 1. Synthetic psychrometric data (24h daily cycle)
# =====================================================================
n = 24
hours = np.arange(n)

T = 25 + 7 * np.sin(2 * np.pi * hours / 24)
RH = 0.55 - 0.15 * np.sin(2 * np.pi * hours / 24)

time = [
    datetime(2023, 1, 1) + timedelta(hours=int(h))
    for h in hours
]

obs_cfg = ObservationsConfig(
    T=T,
    RH=RH,
    time=time,
    label="Synthetic day",
)

obs = Observations(obs_cfg)

# =====================================================================
# 2. Chart configuration
# =====================================================================
cfg = ChartConfig(
    t_min=15,
    t_max=35,
    pressure=101325,
    style="seaborn-v0_8",
)

# =====================================================================
# 3. Points (raw observations)
# =====================================================================
points = obs.to_points()

# =====================================================================
# 4. Simple psychrometric path
# =====================================================================
simple_path = obs.to_path(label="Daily cycle")

# =====================================================================
# 5. Indexed path (ITU)
# =====================================================================
itu = ITUIndex()

itu_path = obs.to_indexed_path(
    itu,
    label="Daily ITU cycle",
    cmap="plasma",
    vmin=70,
    vmax=90,
    linewidth=2.5,
)

# =====================================================================
# 6. Density field
# =====================================================================
density_cfg = DensityFieldConfig(
    bins=(40, 40),
    cmap="inferno",
    alpha=0.5,
)

density_data = obs.to_density_field(density_cfg, cfg)

density_field = DensityField(
    cfg=density_cfg,
    data=density_data,
)

# =====================================================================
# 7. Optional comfort zone (for reference)
# =====================================================================
comfort_zone = Zone(
    name="Comfort",
    t_range=(20, 27),
    rh_range=(0.4, 0.65),
    facecolor="lightgreen",
    edgecolor="green",
    linewidth=1.5,
)

# =====================================================================
# 8. Build and draw chart
# =====================================================================
chart = PsychChart(
    cfg=cfg,
    zones=[comfort_zone],
    points=points,
    paths=[
        simple_path,
        itu_path,
    ],
    density_fields=[density_field],
)

ax = chart.draw()

ax.set_title("PsychChart – Visual Integration Test")

plt.show()

