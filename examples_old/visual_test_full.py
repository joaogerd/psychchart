"""
Visual integration test for PsychChart (current architecture).

This script validates:
- zones
- points
- domain ITU field + isolines
- observation density field
- manually overlaid psychrometric path
- manually overlaid ITU-colored path

Run:
    python examples/visual_test_full.py
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from psychchart import PsychChart
from psychchart.config import (
    AppConfig,
    ChartConfig,
    DensityFieldConfig,
    FieldRenderConfig,
    IndexConfig,
    IndexRenderConfig,
    IsolineRenderConfig,
    ObservationsConfig,
    Point,
    Zone,
)
from psychchart.indexes.itu import ITU
from psychchart.psychrometrics import Psychrometrics


# =====================================================================
# 1. Synthetic psychrometric data (24h daily cycle)
# =====================================================================
n = 24
hours = np.arange(n)

T = 25.0 + 7.0 * np.sin(2.0 * np.pi * hours / 24.0)
RH = 0.55 - 0.15 * np.sin(2.0 * np.pi * hours / 24.0)

time = [
    datetime(2023, 1, 1) + timedelta(hours=int(h))
    for h in hours
]

# ---------------------------------------------------------------------
# Save synthetic observations to a temporary CSV file
# Current ObservationsConfig is file-based.
# ---------------------------------------------------------------------
tmpdir = Path(tempfile.mkdtemp(prefix="psychchart_visual_test_"))
csv_file = tmpdir / "synthetic_day.csv"

df = pd.DataFrame(
    {
        "T": T,
        "RH": RH,
        "time": time,
    }
)
df.to_csv(csv_file, index=False)

# =====================================================================
# 2. Chart configuration
# =====================================================================
chart_cfg = ChartConfig(
    t_min=15,
    t_max=35,
    y_min=0.0,
    y_max=0.030,
    pressure=101325.0,
    xlabel="Dry-bulb temperature (°C)",
    ylabel="Humidity ratio (kg/kg)",
    output="visual_test_full.png",
    dpi=160,
    style="seaborn-v0_8",
)

# =====================================================================
# 3. Points (sample a few raw observations for annotation)
# =====================================================================
points = [
    Point(
        t=float(T[i]),
        rh=float(RH[i]),
        label=f"{hours[i]:02d}h",
        marker="o",
        color="black",
        size=28.0,
    )
    for i in [0, 6, 12, 18]
]

# =====================================================================
# 4. Optional comfort zone
# =====================================================================
comfort_zone = Zone(
    name="Comfort",
    t_range=(20.0, 27.0),
    rh_range=(0.40, 0.65),
    follow_rh=True,
    facecolor="lightgreen",
    edgecolor="green",
    linewidth=1.5,
    alpha=0.20,
)

# =====================================================================
# 5. Domain index (ITU field + isolines)
# =====================================================================
itu_cfg = IndexConfig(
    index="ITU",
    label="ITU",
    cmap="Spectral_r",
    vmin=60.0,
    vmax=90.0,
    render=IndexRenderConfig(
        field=FieldRenderConfig(
            alpha=0.35,
            colorbar=True,
        ),
        isolines=IsolineRenderConfig(
            levels=[68, 72, 78, 84],
            color="black",
            style=":",
            linewidth=0.9,
            label=True,
            label_fontsize=8,
            label_fmt="{index} = {value:.0f}",
        ),
    ),
)

# =====================================================================
# 6. Observation density field
# =====================================================================
obs_cfg = ObservationsConfig(
    file=str(csv_file),
    format="csv",
    density=DensityFieldConfig(
        bins=(40, 40),
        cmap="inferno",
        alpha=0.40,
        colorbar=True,
        normalize=True,
    ),
)

# =====================================================================
# 7. Build validated application configuration
# =====================================================================
app_cfg = AppConfig.model_validate(
    {
        "chart": chart_cfg.model_dump(),
        "zones": [comfort_zone.model_dump()],
        "points": [p.model_dump() for p in points],
        "indexes": [itu_cfg.model_dump()],
        "observations": [obs_cfg.model_dump()],
    }
)
# =====================================================================
# 8. Build and draw chart
# =====================================================================
chart = PsychChart(**app_cfg.to_runtime_payload())
ax = chart.draw()

# =====================================================================
# 9. Manual path overlays
# =====================================================================
# Convert RH -> humidity ratio W for overlay in psychrometric coordinates.
W = Psychrometrics.humidity_ratio(T, RH, pressure=chart_cfg.pressure)

# 9a) simple path
ax.plot(
    T,
    W,
    color="royalblue",
    linewidth=1.4,
    alpha=0.65,
    zorder=20,
    label="Daily cycle",
)

# 9b) ITU-colored path (manual overlay)
itu_values = np.array(
    [ITU.compute({"T": float(t), "RH": float(rh)}) for t, rh in zip(T, RH)]
)

sc = ax.scatter(
    T,
    W,
    c=itu_values,
    cmap="plasma",
    vmin=70,
    vmax=90,
    s=55,
    edgecolors="black",
    linewidths=0.6,
    zorder=25,
    label="Daily ITU cycle",
)

# annotate a few points
for i in [0, 6, 12, 18]:
    ax.text(
        T[i] + 0.25,
        W[i] + 0.0004,
        f"{hours[i]:02d}h",
        fontsize=8,
        color="black",
        zorder=30,
    )

cbar = plt.colorbar(sc, ax=ax, pad=0.02)
cbar.set_label("ITU along path")

ax.set_title("PsychChart – Visual Integration Test")
ax.legend(loc="upper left")

plt.tight_layout()
plt.show()
