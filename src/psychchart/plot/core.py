from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from psychchart.psychrometrics import Psychrometrics
from psychchart.config import (
    ChartConfig,
    IsoSet,
    Zone,
    Point,
    IndexConfig,
    IndexZone,
    IndexField,
)

# Low-level drawing helpers (single responsibility)
from .layers import ZORDER
from .isolines import draw_isolines
from .zones import draw_zones
from .indexes import (
    draw_index_isolines,
    draw_index_zones,
    draw_index_fields,
)

# =============================================================================
# Main rendering engine
# =============================================================================
@dataclass
class PsychChart:
    """
    Psychrometric chart rendering engine.

    This class is the **central orchestration layer** of the psychrometric
    chart system. It receives fully validated configuration objects and
    delegates all numerical computation and geometry to specialized modules.

    The responsibility of this class is strictly to:
    - manage the plotting pipeline
    - control drawing order (semantic layering)
    - coordinate helpers that draw isolines, zones, points and indexes

    It intentionally follows an **imperative rendering model**, similar
    to Matplotlib itself.

    Responsibilities
    ----------------
    - Initialize figure and axes
    - Prepare the thermodynamic domain
    - Call drawing routines in correct semantic order
    - Apply axis formatting and grid

    Non-responsibilities
    --------------------
    - YAML parsing
    - Configuration validation
    - Psychrometric calculations
    - File I/O (savefig)
    - Interactivity

    Parameters
    ----------
    cfg : ChartConfig
        Global chart configuration defining:
        - temperature bounds
        - pressure
        - visual style
    isolines : dict[str, IsoSet], optional
        Dictionary of psychrometric isolines to draw
        (e.g. relative humidity, enthalpy).
    zones : list[Zone], optional
        Geometric temperature–humidity zones.
    points : list[Point], optional
        Discrete reference points (observations, design states).
    indexes : list[IndexConfig], optional
        Index isolines (e.g. THI, ITU).
    index_zones : list[IndexZone], optional
        Zones derived from index thresholds.
    index_fields : list[IndexField], optional
        Continuous index fields rendered as heatmaps.

    Notes
    -----
    - All inputs are assumed to be valid.
    - This class does **not** perform semantic checks.
    - Designed for batch rendering and scientific figures.
    """

    # ------------------------------------------------------------------
    # Core configuration
    # ------------------------------------------------------------------
    cfg: ChartConfig

    # ------------------------------------------------------------------
    # Psychrometric isolines (RH, enthalpy, etc.)
    # ------------------------------------------------------------------
    isolines: Optional[Dict[str, IsoSet]] = None

    # ------------------------------------------------------------------
    # Geometric comfort / risk zones
    # ------------------------------------------------------------------
    zones: Optional[List[Zone]] = None

    # ------------------------------------------------------------------
    # Discrete reference points
    # ------------------------------------------------------------------
    points: Optional[List[Point]] = None

    # ------------------------------------------------------------------
    # Index isolines (e.g., ITU contours)
    # ------------------------------------------------------------------
    indexes: Optional[List[IndexConfig]] = None

    # ------------------------------------------------------------------
    # Index-based zones (categorical)
    # ------------------------------------------------------------------
    index_zones: Optional[List[IndexZone]] = None

    # ------------------------------------------------------------------
    # Index continuous fields (heatmaps)
    # ------------------------------------------------------------------
    index_fields: Optional[List[IndexField]] = None

    # ------------------------------------------------------------------
    # Post-initialization normalization
    # ------------------------------------------------------------------
    def __post_init__(self):
        """
        Normalize optional containers.

        This method guarantees that all optional attributes
        are always iterable collections, eliminating the need
        for repeated ``None`` checks throughout the code.

        It also initializes internal counters used by
        index-based rendering layers.
        """
        self.isolines = self.isolines or {}
        self.zones = self.zones or []
        self.points = self.points or []
        self.indexes = self.indexes or []
        self.index_zones = self.index_zones or []
        self.index_fields = self.index_fields or []

        # Internal counter used for unique labeling of index zones
        self._index_zone_counter = 0

    # ==================================================================
    # Domain preparation
    # ==================================================================
    def _prepare_domain(self):
        """
        Prepare thermodynamic domain arrays.

        This method defines:
        - the dry-bulb temperature vector
        - the saturation humidity ratio curve

        These arrays are reused by multiple drawing routines.
        """
        # Temperature domain (°C)
        self.T = np.linspace(self.cfg.t_min, self.cfg.t_max, 300)

        # Saturation humidity ratio (kg/kg)
        self.W_sat = Psychrometrics.humidity_ratio(
            self.T, 1.0, self.cfg.pressure
        )

    # ==================================================================
    # Axes preparation
    # ==================================================================
    def _prepare_axes(self):
        """
        Initialize Matplotlib figure and axes.

        Applies the configured Matplotlib style if provided.
        """
        if self.cfg.style:
            plt.style.use(self.cfg.style)

        self.fig, self.ax = plt.subplots()

    # ==================================================================
    # Final formatting
    # ==================================================================
    def _finalize_axes(self):
        """
        Apply axis labels, limits and grid.

        This step is intentionally deferred until all drawing
        operations are complete.
        """
        self.ax.set_xlabel("Dry-bulb temperature (°C)")
        self.ax.set_ylabel("Humidity ratio (kg/kg)")
        self.ax.set_xlim(self.cfg.t_min, self.cfg.t_max)
        self.ax.grid(True)

    # ------------------------------------------------------------------
    # Plot saturation curve
    # ------------------------------------------------------------------
    def _draw_saturation_curve(self):
        """
        Draw the saturation curve (100% relative humidity).
    
        The saturation curve represents the **physical upper boundary**
        of the psychrometric chart, corresponding to air that is fully
        saturated with water vapor (RH = 1.0).
    
        From a thermodynamic perspective, this curve separates:
        - physically admissible states (below the curve), from
        - impossible states (above the curve, supersaturation).
    
        Because of its fundamental role, the saturation curve:
        - must always be drawn,
        - must appear visually on top of other elements,
        - acts as a reference boundary for isolines, zones and fields.
    
        This method assumes that:
        - ``self.T`` has already been initialized as the dry-bulb
          temperature domain (°C),
        - ``self.W_sat`` contains the corresponding saturation
          humidity ratio values (kg/kg),
        - both are prepared during the domain setup stage
          (see ``_prepare_domain``).
    
        This method is intentionally minimal and imperative.
        It does NOT:
        - compute saturation properties
        - perform axis scaling
        - clip other chart elements
        - manage legends globally
    
        All such responsibilities belong to higher-level logic.
    
        Notes
        -----
        - The saturation curve corresponds to RH = 1.0.
        - It is rendered with a thicker line and higher z-order
          to ensure visibility.
        - The label "100% RH" is provided for optional legend use.
    
        See Also
        --------
        Psychrometrics.humidity_ratio :
            Computes the saturation humidity ratio used to build ``self.W_sat``.
        """
    
        # ------------------------------------------------------------------
        # self.T     : dry-bulb temperature array (°C)
        # self.W_sat : saturation humidity ratio (kg/kg)
        #
        # zorder is set high to ensure the curve is drawn above
        # isolines, zones and index fields.
        self.ax.plot(
            self.T,
            self.W_sat,
            color="black",               # visually neutral and physically canonical
            lw=1.8,                      # thicker line to emphasize physical boundary
            label="100% RH",             # optional legend entry
            zorder=ZORDER['saturation'], # top-most layer
        )
    
    # ==================================================================
    # Main rendering pipeline
    # ==================================================================
    def draw(self) -> Axes:
        """
        Render the complete psychrometric chart.

        Rendering order (semantic layers)
        ---------------------------------
        1. Index continuous fields (background heatmaps)
        2. Index-derived zones
        3. Saturation curve
        4. Thermodynamic zones
        5. Psychrometric isolines
        6. Reference points
        7. Axis formatting

        Returns
        -------
        ax : matplotlib.axes.Axes
            Axes containing the rendered psychrometric diagram.

        Notes
        -----
        - The figure object is created internally.
        - Saving or displaying the figure is responsibility of the caller.
        """
        self._prepare_axes()
        self._prepare_domain()

        # Semantic layering (background → foreground)
        self._draw_saturation_curve()

        draw_index_fields(self.ax, self)   # fundo
        draw_index_zones(self.ax, self)    # fundo categórico
        draw_isolines(self.ax, self)       # campo físico
        draw_zones(self.ax, self)          # conforto (frente)
        self._draw_points()                # observações
        
        self._finalize_axes()

        return self.ax

    # ==================================================================
    # Reference points
    # ==================================================================
    def _draw_points(self):
        """
        Draw discrete reference points.

        Each point is defined in temperature and relative humidity
        and converted internally to humidity ratio.
        """
        for p in self.points:
            w = Psychrometrics.humidity_ratio(
                p.t, p.rh, self.cfg.pressure
            )
            self.ax.plot(p.t, w, "o", label=p.label)

