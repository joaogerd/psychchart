import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

from psychchart.indexes.iti import ITU


# ---------------------------------------------------------------------
# Domain (same as literature)
# ---------------------------------------------------------------------
T = np.linspace(20, 46, 300)        # °C
RH = np.linspace(0.0, 1.0, 300)     # fraction (0–1)

RH_grid, T_grid = np.meshgrid(RH, T)

# ---------------------------------------------------------------------
# Compute ITU using the class
# ---------------------------------------------------------------------
ITU_grid = ITU.compute(T_grid, RH_grid)

# ---------------------------------------------------------------------
# Stress class thresholds (classical)
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
    "#fddbc7",  # light yellow
    "#f4a582",  # orange
    "#ca0020",  # red
]

cmap = ListedColormap(colors)
norm = BoundaryNorm(levels, cmap.N)

# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

cs = ax.contourf(
    RH_grid * 100,  # %
    T_grid,
    ITU_grid,
    levels=levels,
    cmap=cmap,
    norm=norm,
    extend="max",
)

# ---------------------------------------------------------------------
# Colorbar
# ---------------------------------------------------------------------
cbar = fig.colorbar(cs, ax=ax, ticks=[72, 78, 84, 90])
cbar.ax.set_yticklabels(labels[1:])
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

