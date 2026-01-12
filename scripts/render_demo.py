from psychchart import load_chart_config, PsychChart
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Exemplo de configuração completa (você pode trocar pelo seu YAML real)
# ---------------------------------------------------------------------
yaml = """
chart:
  # ---------------------------------------------------------------------------
  # Global chart parameters
  # ---------------------------------------------------------------------------

  t_min: 0
  # Minimum dry-bulb temperature shown on the x-axis (°C).
  # Defines the left boundary of the chart.

  t_max: 50
  # Maximum dry-bulb temperature shown on the x-axis (°C).
  # Defines the right boundary of the chart.

  pressure: 101325
  # Total atmospheric pressure (Pa).
  # This value is used in ALL psychrometric calculations
  # (humidity ratio, wet-bulb temperature, specific volume, etc.).

  y_min: 0
  # Lower bound of the y-axis (humidity ratio).
  # Forces the chart to start exactly at the physical origin (W = 0).

  y_max: 0.085
  # Upper bound of the y-axis (humidity ratio).
  # If omitted, the plotting engine will automatically compute
  # a value slightly above the saturation curve at t_max.

  output: carta.png
  # Output filename for the generated chart image.

  dpi: 200
  # Output resolution (dots per inch).
  # Higher values produce sharper images.

  style: seaborn-v0_8
  # Matplotlib style to be applied globally.
  # Controls default colors, grid appearance, fonts, and spacing.


# -----------------------------------------------------------------------------
# Isolines (psychrometric isopleths)
# -----------------------------------------------------------------------------
isos:
  # The key "isos" MUST be a list.
  # Each list item defines a family of isolines.

  - name: relative_humidity
    # Internal identifier of the isoline type.
    # Used by the plotting engine to select the correct equation.

    enabled: true
    # Enables or disables the rendering of this isoline family.

    values: [0.2, 0.4, 0.6, 0.8]
    # Relative humidity values.
    # May be provided as fractions (0–1) or percentages (20–80).
    # The loader normalizes these automatically.

    color: crimson
    # Line color for relative humidity curves.

    style: "-"
    # Line style (solid line).

  - name: wet_bulb
    # Wet-bulb temperature isolines.

    enabled: true
    # Enables wet-bulb temperature curves.

    values: [10, 15, 20, 25, 30, 35]
    # Wet-bulb temperatures (°C) at which isolines are drawn.

    color: goldenrod
    # Line color for wet-bulb isolines.

    style: "--"
    # Dashed line to visually distinguish from other isolines.

  - name: moisture_quantity
    # Constant humidity ratio (moisture content) isolines.

    enabled: true
    # Enables horizontal moisture content lines.

    values: [0.005, 0.010, 0.015, 0.020]
    # Humidity ratio values (kg water vapor / kg dry air).

    color: forestgreen
    # Line color for moisture content isolines.

    style: "-."
    # Solid line style.

  - name: enthalpy
    # Moist air enthalpy isolines.

    enabled: false
    # Explicitly disabled in this example.
    # Keeping it declared improves configuration readability.

  - name: specific_volume
    # Specific volume isolines.

    enabled: false
    # Disabled in this configuration.


# -----------------------------------------------------------------------------
# Zones (thermal comfort regions)
# -----------------------------------------------------------------------------
zones:
  - name: Conforto (Taurinos)
    # Zona "core" de conforto: mínima ativação termorregulatória,
    # desempenho preservado, cenário típico com sombra e vento fraco/moderado.

    vertices:
      # (T, RH) em fração 0–1
      # Formato "Givoni": topo inclinado e limites práticos.
      - [16, 0.70]
      - [16, 0.40]
      - [22, 0.40]
      - [25, 0.50]
      - [24, 0.70]
    follow_rh: true

    edgecolor: darkgreen
    facecolor: none
    linewidth: 2.2


  - name: Conforto permissível (Taurinos)
    # Zona aceitável/operacional: pode haver alerta leve
    # (queda pequena de consumo/produção), mas ainda sem estresse moderado.

    vertices:
      - [14, 0.80]
      - [14, 0.35]
      - [24, 0.35]
      - [28, 0.45]
      - [27, 0.70]
      - [22, 0.80]
    follow_rh: true

    edgecolor: goldenrod
    facecolor: none
    linewidth: 2.0
  - name: Comfort Zone
    vertices:
      [[20,0.2],[22,0.2],[22,0.50],[21,0.80],[20,0.80]]
#    facecolor: '#b2fab4'
    facecolor: blue
#    edgecolor: '#2e7d32'
    edgecolor: blue
    linewidth: 2

#  - name: Taurinos
#    # Name of the zone.
#    # Displayed in the chart legend.
#
#    t_range: [15, 25]
#    # Dry-bulb temperature range (°C) defining the horizontal extent.
#
#    rh_range: [0.40, 0.70]
#    # Relative humidity range (fraction 0–1).
#    # Defines the vertical extent of the zone.
#
#    follow_rh: true
#    # If true, zone boundaries follow actual relative humidity curves,
#    # rather than forming a rectangular approximation.
#
#    edgecolor: darkred
#    # Color of the zone boundary.
#
#    facecolor: none
#    # No fill color (transparent zone interior).
#
#    linewidth: 2.0
#    # Width of the zone boundary line.
#
#  - name: Girolando
#    # Second comfort zone, representing a different breed or condition.
#
#    t_range: [15, 28]
#    # Wider temperature tolerance.
#
#    rh_range: [0.40, 0.75]
#    # Wider humidity tolerance.
#
#    follow_rh: true
#    # Boundaries follow real RH curves.
#
#    edgecolor: magenta
#    # Zone boundary color.
#
#    facecolor: none
#    # Transparent interior.
#
#    linewidth: 2.0
#    # Boundary line width.
#    #
index_fields:
  - index: ITU
    cmap: inferno
    alpha: 0.4
    colorbar: true
      
indexes:
  - name: ITU
    mode: isolines
    levels: [68, 72, 76, 80]
    style: "-"
    color: black
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

