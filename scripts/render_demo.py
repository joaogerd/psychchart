from psychchart import load_chart_config, PsychChart
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Exemplo de configuração completa (você pode trocar pelo seu YAML real)
# ---------------------------------------------------------------------
yaml = """
# =============================================================================
# Psychrometric chart – ITU full visualization
# =============================================================================

chart:
  t_min: 0
  t_max: 50
  pressure: 101325

  y_min: 0.0
  y_max: 0.085

  output: psychchart_itu.png
  dpi: 200

    #style: seaborn-v0_8
    #title: "Psychrometric Chart with Temperature–Humidity Index (ITU)"


# -----------------------------------------------------------------------------
# Psychrometric isolines
# -----------------------------------------------------------------------------
isos:

  - name: relative_humidity
    enabled: true
    values: [0.2, 0.4, 0.6, 0.8]
    color: crimson
    style: "-"
    linewidth: 1.0
    alpha: 0.9

  - name: wet_bulb
    enabled: true
    values: [10, 15, 20, 25, 30, 35]
    color: goldenrod
    style: "--"
    linewidth: 0.9
    alpha: 0.8

  - name: moisture_quantity
    enabled: true
    values: [0.005, 0.010, 0.015, 0.020]
    color: forestgreen
    style: "-"
    linewidth: 1.0
    alpha: 0.9

  - name: enthalpy
    enabled: false

  - name: specific_volume
    enabled: false


# -----------------------------------------------------------------------------
# Continuous ITU field (background)
# -----------------------------------------------------------------------------
index_fields:
  - index: ITU

    # Carefully chosen palette (literature-like)
    cmap: Spectral_r

    alpha: 0.45
    colorbar: true

    # Optional explicit range (keeps colors stable across plots)
    vmin: 68
    vmax: 95


# -----------------------------------------------------------------------------
# ITU isolines (over the field)
# -----------------------------------------------------------------------------
#indexes:
#  - name: ITU
#    mode: isolines
#    levels: [72, 78, 84]
#    style: "-"
#    color: black
#    linewidth: 1.2


# -----------------------------------------------------------------------------
# Comfort zones (example – management-oriented)
# -----------------------------------------------------------------------------
zones:

  - name: Taurinos
    t_range: [15, 25]
    rh_range: [0.40, 0.70]
    follow_rh: true
    edgecolor: darkred
    facecolor: none
    linewidth: 2.0

  - name: Girolando
    t_range: [15, 28]
    rh_range: [0.40, 0.75]
    follow_rh: true
    edgecolor: magenta
    facecolor: none
    linewidth: 2.0


# -----------------------------------------------------------------------------
# Reference points
# -----------------------------------------------------------------------------
points:

  - label: Sample_A
    t: 32
    rh: 0.55
    marker: "o"
    color: black

  - label: Sample_B
    t: 26
    rh: 0.65
    marker: "s"
    color: navy
"""

# ---------------------------------------------------------------------
# Carregar configuração (via loader oficial)
# ---------------------------------------------------------------------
import tempfile
from pathlib import Path

tmp = Path(tempfile.gettempdir()) / "psychchart_demo.yaml"
tmp.write_text(yaml)

data = load_chart_config(tmp)

# ---------------------------------------------------------------------
# Criar e renderizar o gráfico
# ---------------------------------------------------------------------
chart = PsychChart(**data)
ax = chart.draw()

ax.set_title("Psychrometric Chart – Full Pipeline Demo")

plt.tight_layout()
plt.show()

# Para salvar:
# plt.savefig("psychchart_full_demo.png", dpi=200)

