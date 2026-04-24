import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

from psychchart.indexes.itu import ITU


# ---------------------------------------------------------------------
# Domain (literature-style Cartesian plane: T x RH)
# ---------------------------------------------------------------------
T = np.linspace(20.0, 46.0, 300)      # °C
RH = np.linspace(0.0, 1.0, 300)       # fraction [0, 1]

RH_grid, T_grid = np.meshgrid(RH, T)

# ---------------------------------------------------------------------
# Compute ITU
# ---------------------------------------------------------------------
# The current psychChart convention is RH as fraction [0, 1].
ITU_grid = ITU.compute_vectorized({
    "T": T_grid,
    "RH": RH_grid,
})

# ---------------------------------------------------------------------
# Stress class thresholds
# ---------------------------------------------------------------------
levels = [0, 72, 78, 84, 90, 120]

labels = [
    "Sem estresse",
    "Estresse leve",
    "Estresse moderado",
    "Estresse severo",
    "Fatal",
]

colors = [
    "#2166ac",  # blue
    "#67a9cf",  # light blue
    "#fddbc7",  # light warm
    "#f4a582",  # orange
    "#ca0020",  # red
]

cmap = ListedColormap(colors)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=False)

# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

cf = ax.contourf(
    RH_grid * 100.0,   # convert to %
    T_grid,
    ITU_grid,
    levels=levels,
    cmap=cmap,
    norm=norm,
    extend="max",
)

# Optional threshold isolines
cs = ax.contour(
    RH_grid * 100.0,
    T_grid,
    ITU_grid,
    levels=[72, 78, 84, 90],
    colors="black",
    linewidths=0.8,
)

ax.clabel(cs, fmt="%.0f", fontsize=8)

# ---------------------------------------------------------------------
# Colorbar
# ---------------------------------------------------------------------
class_centers = [(levels[i] + levels[i + 1]) / 2 for i in range(len(levels) - 1)]

cbar = fig.colorbar(cf, ax=ax, ticks=class_centers)
cbar.ax.set_yticklabels(labels)
cbar.set_label("ITU")

# ---------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------
ax.set_xlabel("Umidade relativa (%)")
ax.set_ylabel("Temperatura do ar (°C)")
ax.set_title("Índice de Temperatura e Umidade (ITU)\nPlano cartesiano T × RH")

ax.set_xlim(0, 100)
ax.set_ylim(20, 46)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
