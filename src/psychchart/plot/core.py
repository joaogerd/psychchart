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
    PathConfig,
    DensityFieldConfig,
    DataLayerConfig,
    OperationalOverlayConfig,
    OperationalProfileConfig,    
)

from psychchart.data.layer_builder import build_data_layer
# Low-level drawing helpers (single responsibility)
from .layers import ZORDER
from .data_layers import draw_data_layers
from .legend import draw_chart_legend
from .isolines import draw_isolines
from .zones import draw_zones
from .indexes import (
    draw_indexes,
    draw_index_zones,
)

#from .operational_zones import draw_operational_zones

# =============================================================================
# Main rendering engine
# =============================================================================
@dataclass
class PsychChart:
    """
    Psychrometric chart rendering engine.

    This class is the **central orchestration layer** of the psychrometric
    chart system. It coordinates all rendering steps and delegates
    numerical computation, geometry construction, and domain-specific
    logic to specialized helper modules.

    The design philosophy intentionally mirrors Matplotlib itself:
    - imperative
    - explicit
    - stateless between draw calls

    This class DOES NOT perform calculations.
    It only **organizes and executes the drawing pipeline**.

    Responsibilities
    ----------------
    - Initialize Matplotlib figure and axes
    - Prepare the thermodynamic domain (T, W, saturation curve)
    - Control semantic drawing order (layering)
    - Dispatch rendering to specialized helpers:
        * isolines
        * zones
        * points
        * index isolines
        * index zones
        * index fields
        * density fields
        * psychrometric paths
    - Apply axis formatting, labels, limits, and grid

    Non-responsibilities
    --------------------
    - YAML / JSON parsing
    - Configuration validation
    - Psychrometric calculations
    - Statistical analysis
    - File I/O (savefig)
    - Interactive callbacks

    This strict separation ensures:
    - scientific transparency,
    - predictable rendering,
    - easy extensibility,
    - reproducibility of figures.

    Parameters
    ----------
    cfg : ChartConfig
        Global chart configuration defining:
        - dry-bulb temperature limits
        - reference pressure
        - figure size and style
        - axis labels and ticks

    isolines : dict[str, IsoSet], optional
        Classical psychrometric isolines such as:
        - relative humidity
        - enthalpy
        - wet-bulb temperature
        - specific volume

    zones : list[Zone], optional
        Geometric zones defined in temperature–humidity space.
        These typically represent comfort, risk, or design regions.

    points : list[Point], optional
        Discrete reference points plotted on the chart
        (e.g., measurements, design conditions).

    indexes : list[IndexConfig], optional
        Index isolines derived from bioclimatic or thermal indices
        (e.g., ITU, THI, HLI).

    index_zones : list[IndexZone], optional
        Categorical zones derived from index thresholds
        (e.g., stress classes).

    index_fields : list[IndexField], optional
        Continuous index fields rendered as background heatmaps.

    paths : list[PathConfig], optional
        Ordered psychrometric trajectories, typically derived
        from time-series observations.

    density_fields : list[DensityField], optional
        Density or frequency fields representing the distribution
        of observed psychrometric states.

    Notes
    -----
    - All inputs are assumed to be **validated and coherent**.
    - This class performs **no semantic checks**.
    - Designed for batch rendering of scientific-quality figures.
    - The chart can be redrawn multiple times without side effects.
    """

    # ------------------------------------------------------------------
    # Core chart configuration
    # ------------------------------------------------------------------
    cfg: ChartConfig

    # ------------------------------------------------------------------
    # Classical psychrometric isolines
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
    # Index-based categorical zones
    # ------------------------------------------------------------------
    index_zones: Optional[List[IndexZone]] = None

    # ------------------------------------------------------------------
    # Psychrometric paths (temporal trajectories)
    # ------------------------------------------------------------------
    paths: Optional[List[PathConfig]] = None

    # ------------------------------------------------------------------
    # Density / frequency fields
    # ------------------------------------------------------------------
    density_fields: Optional[List[DensityFieldConfig]] = None

    # ------------------------------------------------------------------
    # datasets (data-driven overlays)
    # ------------------------------------------------------------------
    data_layers: Optional[List[DataLayerConfig]] = None
    
    operational_profiles: Optional[List[OperationalProfileConfig]] = None
    operational_overlays: Optional[List[OperationalOverlayConfig]] = None
    
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
        self.paths = self.paths or []
        self.density_fields = self.density_fields or []
        self.density_fields = self.density_fields or []
        self.psych = Psychrometrics()
        
        # -------------------------------------------------------------
        # Process datasets (declarative → executable)
        # -------------------------------------------------------------

        self.data_layers = [
            build_data_layer(layer_cfg, pressure=self.cfg.pressure)
            for layer_cfg in self.data_layers
        ]

        # ---------------------------------------------------------
        # App-level declarative sections live on the chart instance,
        # not inside ChartConfig.
        # ---------------------------------------------------------
        self.operational_profiles = self.operational_profiles or {}
        self.operational_overlays = self.operational_overlays or {}
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
            self.T, np.ones_like(self.T), self.cfg.pressure
        )

        self._tw_grid_cache = None
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

        self.fig, self.ax = plt.subplots(
            figsize=self.cfg.figsize if self.cfg.figsize else (14, 7)
        )


 
    # ==================================================================
    # Axes styling helpers
    # ==================================================================
    def _style_axes(self):
        """
        Apply standard visual styling to the psychrometric chart axes.

        This method enforces the **canonical psychchart axis layout**:
        - The **y-axis** (humidity ratio) is displayed on the **right side**
          of the chart.
        - The **left** and **top** spines are hidden to reduce visual clutter.
        - Tick visibility and direction are explicitly controlled to ensure
          consistency across backends and Matplotlib styles.

        The method operates **in-place** on the Matplotlib ``Axes`` object
        associated with the current chart instance.

        Notes
        -----
        - This function does **not** set axis limits, labels, or tick values.
          Those responsibilities belong to higher-level configuration logic
          (:class:`ChartConfig`).
        - Styling choices are aligned with typical psychrometric chart
          conventions, where the humidity axis is placed on the right.

        Examples
        --------
        Typical usage inside the rendering pipeline::

            chart = PsychChart(cfg)
            chart._style_axes()
            chart.render()

        If you are manually working with an Axes object for debugging::

            fig, ax = plt.subplots()
            chart.ax = ax
            chart._style_axes()
            plt.show()
        """

        # Reference to the Matplotlib Axes associated with this chart
        ax = self.ax

        # --------------------------------------------------------------
        # Y-axis positioning (right side)
        # --------------------------------------------------------------
        # Place the y-axis ticks on the right
        ax.yaxis.tick_right()

        # Ensure the y-axis label is also placed on the right
        ax.yaxis.set_label_position("right")

        # --------------------------------------------------------------
        # Spine visibility
        # --------------------------------------------------------------
        # Hide left spine (no left y-axis in psychrometric charts)
        ax.spines["left"].set_visible(False)

        # Hide top spine for a cleaner, open-frame appearance
        ax.spines["top"].set_visible(False)

        # --------------------------------------------------------------
        # Tick configuration
        # --------------------------------------------------------------
        # Y-axis: disable left ticks, enable right ticks (both major/minor)
        ax.tick_params(
            axis="y",
            which="both",
            left=False,
            right=True,
        )

        # X-axis: disable top ticks, enable bottom ticks (both major/minor)
        ax.tick_params(
            axis="x",
            which="both",
            top=False,
            bottom=True,
        )
        
    # ==================================================================
    # Final formatting
    # ==================================================================
    def _finalize_axes(self):
        """
        Apply final axis formatting and presentation settings.

        This method performs the **last-stage visual configuration**
        of the psychrometric chart axes. It is strictly limited to
        *presentation concerns* and must be executed **after all
        geometric and data-driven drawing operations**.

        The responsibilities of this method include:
        - applying axis labels and title,
        - enforcing axis limits from configuration,
        - drawing the fundamental T–W grid (if enabled),
        - applying canonical axis styling (spines and ticks),
        - extending the saturation curve to visually close the domain.

        Design rationale
        ----------------
        This method is intentionally placed at the *end* of the rendering
        pipeline so that:
        - automatically inferred limits (from plotted elements) are known,
        - user overrides defined in :class:`ChartConfig` are applied last,
        - no visual adjustment interferes with geometric construction.

        Strict constraints
        ------------------
        - This method must **not** perform any numerical computation.
        - All values must be sourced exclusively from ``self.cfg``.
        - No new chart elements (isolines, zones, fields) may be created here.

        Notes
        -----
        - Axis labels are always applied (defaults are defined in
          :class:`ChartConfig`).
        - Axis limits are enforced explicitly to guarantee reproducibility.
        - Optional elements (title, y-limits) are applied only when set.

        Examples
        --------
        Typical usage at the end of the rendering pipeline::

            chart._draw_saturation_curve()
            chart._draw_isolines()
            chart._draw_zones()
            chart._finalize_axes()

        When testing formatting in isolation::

            fig, ax = plt.subplots()
            chart.ax = ax
            chart._finalize_axes()
            plt.show()
        """

        # Local alias for readability
        cfg = self.cfg

        # ------------------------------------------------------------------
        # Title (presentation-only, optional)
        # ------------------------------------------------------------------
        # Applied only if explicitly defined in the configuration
        if cfg.title is not None:
            self.ax.set_title(cfg.title)

        # ------------------------------------------------------------------
        # Axis labels (always applied)
        # ------------------------------------------------------------------
        # Defaults are defined in ChartConfig
        self.ax.set_xlabel(cfg.xlabel)
        self.ax.set_ylabel(cfg.ylabel)

        # ------------------------------------------------------------------
        # Axis limits
        # ------------------------------------------------------------------
        # Temperature domain is always explicit and controlled by config
        self.ax.set_xlim(cfg.t_min, cfg.t_max)

        # Humidity ratio limits are optional:
        # - if both are None, limits are inferred from plotted data
        # - if one or both are provided, they are enforced explicitly
        if cfg.y_min is not None or cfg.y_max is not None:
            self.ax.set_ylim(cfg.y_min, cfg.y_max)

        # ------------------------------------------------------------------
        # Fundamental T × W grid
        # ------------------------------------------------------------------
        # Drawn here (and not earlier) so it aligns with finalized ticks
        self._draw_tw_grid()

        # ------------------------------------------------------------------
        # Axis spine and tick layout (presentation-only)
        # ------------------------------------------------------------------
        # Applies canonical psychchart styling (right y-axis, hidden spines)
        self._style_axes()

        # ------------------------------------------------------------------
        # Saturation-curve visual extensions
        # ------------------------------------------------------------------
        # Extends the saturation curve to the chart frame, visually
        # closing the admissible thermodynamic domain
        self._draw_saturation_extensions()


    # ==================================================================
    # build T × W grid
    # ==================================================================
    def _build_tw_grid(self, n_w: int = 100):
        """
        Build a physically admissible T × W grid limited by saturation.
    
        This method constructs a **curvilinear computational grid** in the
        (T, W) psychrometric space, where:
        - T is the dry-bulb air temperature (°C),
        - W is the humidity ratio (kg/kg).
    
        For each temperature value ``T[i]``, the humidity ratio spans
        from 0 up to the corresponding saturation value ``W_sat[i]``.
        This guarantees that:
        - all generated states are physically admissible,
        - no supersaturated conditions (W > W_sat) are produced.
    
        The resulting grid is primarily used by:
        - continuous scalar fields (e.g., index maps),
        - comfort or stress index evaluations,
        - density or probability fields defined over the chart domain.
    
        Parameters
        ----------
        n_w : int, optional
            Number of humidity-ratio points per temperature column.
            Higher values increase vertical resolution in W.
            Default is 100.
    
        Returns
        -------
        T_grid : ndarray of shape (n_T, n_w)
            Two-dimensional dry-bulb temperature grid (°C).
            Each row contains a constant temperature value.
    
        W_grid : ndarray of shape (n_T, n_w)
            Two-dimensional humidity-ratio grid (kg/kg), linearly spaced
            from 0 up to the saturation curve for each temperature.
    
        Notes
        -----
        - Assumes that ``self.T`` (1D temperature array) and ``self.W_sat``
          (saturation humidity ratio for each T) have already been
          initialized by ``_prepare_domain``.
        - The grid is **not Cartesian** in physical space, since the upper
          boundary (saturation) varies with temperature.
        - This representation closely follows the physical structure of
          a psychrometric chart and avoids non-physical regions.
    
        Examples
        --------
        Typical usage inside the chart rendering pipeline:
    
        >>> chart._prepare_domain()
        >>> T_grid, W_grid = chart._build_tw_grid(n_w=150)
        >>> T_grid.shape
        (n_T, 150)
        >>> W_grid.max() <= chart.W_sat.max()
        True
        """
    
        # ------------------------------------------------------------------
        # Retrieve precomputed domain variables
        # ------------------------------------------------------------------
        T = self.T           # 1D array of dry-bulb temperatures (°C)
        W_sat = self.W_sat   # 1D array of saturation humidity ratios (kg/kg)
    
        n_T = T.size         # Number of temperature points
    
        # ------------------------------------------------------------------
        # Allocate output grids
        # ------------------------------------------------------------------
        # T_grid : each row has constant temperature T[i]
        # W_grid : humidity ratio varies from 0 to W_sat[i]
        T_grid = np.empty((n_T, n_w))
        W_grid = np.empty((n_T, n_w))
    
        # ------------------------------------------------------------------
        # Build the curvilinear grid column by column
        # ------------------------------------------------------------------
        for i in range(n_T):
            # Replicate temperature value along the W direction
            T_grid[i, :] = T[i]
    
            # Linearly sample humidity ratio up to saturation
            W_grid[i, :] = np.linspace(0.0, W_sat[i], n_w)
    
        return T_grid, W_grid
    # ------------------------------------------------------------------
    # Plot saturation curve
    # ------------------------------------------------------------------
    def _draw_saturation_curve(self):
        """
        Draw the saturation curve (100% relative humidity).

        The saturation curve defines the **physical upper boundary**
        of the psychrometric chart and corresponds to air at
        **100% relative humidity (RH = 1.0)**.

        From a thermodynamic standpoint, this curve separates:
        - **physically admissible states** (below the curve), from
        - **physically impossible states** (above the curve, i.e.,
          supersaturated air).

        Because of its fundamental role, the saturation curve:
        - is **always drawn** (never optional),
        - appears **above all other graphical elements**,
        - serves as a reference boundary for isolines, zones,
          density fields, and index overlays.

        This method assumes that the thermodynamic domain has
        already been prepared.

        Assumptions
        -----------
        - ``self.T`` is a 1D NumPy array of dry-bulb temperatures (°C).
        - ``self.W_sat`` is a 1D NumPy array of saturation humidity
          ratios (kg/kg), aligned with ``self.T``.
        - Both arrays are initialized during the domain setup phase
          (see ``_prepare_domain``).

        Responsibilities explicitly excluded
        ------------------------------------
        This method intentionally does **not**:
        - compute saturation properties,
        - adjust axis limits or scaling,
        - clip other chart elements,
        - manage legends globally.

        Those responsibilities are handled by higher-level
        orchestration logic.

        Notes
        -----
        - The saturation curve corresponds strictly to RH = 1.0.
        - Line style (color and linewidth) is inherited from the
          **visible right-axis spine** to ensure visual coherence
          with the chart frame.
        - A high ``zorder`` guarantees that the curve remains visible
          above all other plotted layers.
        - The label ``"100% RH"`` is provided for optional legend use.

        See Also
        --------
        Psychrometrics.humidity_ratio :
            Computes the saturation humidity ratio used to build
            ``self.W_sat``.

        Examples
        --------
        Typical usage inside the rendering pipeline::

            chart._prepare_domain()
            chart._draw_saturation_curve()
            chart._draw_saturation_extensions()

        Manual debugging example::

            fig, ax = plt.subplots()
            chart.ax = ax
            chart.T = np.linspace(0, 50, 200)
            chart.W_sat = Psychrometrics.humidity_ratio(
                chart.T, RH=1.0, P=101325
            )
            chart._draw_saturation_curve()
            plt.show()
        """

        ax = self.ax

        # --------------------------------------------------------------
        # Inherit visual style from the visible (right) axis spine
        # --------------------------------------------------------------
        spine = ax.spines["right"]
        color = spine.get_edgecolor()
        lw = spine.get_linewidth()

        # --------------------------------------------------------------
        # Plot saturation curve
        # --------------------------------------------------------------
        # self.T     : dry-bulb temperature array (°C)
        # self.W_sat : saturation humidity ratio (kg/kg)
        #
        # A high zorder ensures this curve is rendered above
        # isolines, zones, grids, and index fields.
        ax.plot(
            self.T,
            self.W_sat,
            label="100% RH",               # optional legend entry
            zorder=ZORDER["saturation"],   # top-most graphical layer
            color=color,
            lw=lw,
        )

    # ==================================================================
    # Saturation-curve visual extensions
    # ==================================================================
    def _draw_saturation_extensions(self):
        """
        Draw visual extensions of the saturation curve to the chart borders.

        This helper draws **geometric extensions** of the saturation curve
        so that it visually connects with the chart frame, ensuring a clean
        and continuous boundary of the psychrometric domain.

        Two extensions may be drawn:

        1. **Vertical extension at T = t_min**
           A vertical line from W = 0 up to the first saturation value
           (W_sat at the minimum temperature).

        2. **Horizontal extension at the top of the chart**
           If (and only if) the saturation curve intersects the *upper*
           y-limit of the chart, a horizontal line is drawn from the
           intersection point up to ``t_max``.

        All extensions:
        - Inherit color and linewidth from the **visible axis spine**
          (right y-axis), ensuring visual consistency.
        - Are drawn *outside* the clipping region so they remain visible
          even when touching the frame.

        Notes
        -----
        - This method assumes that:
          - ``self.T`` contains the dry-bulb temperature array.
          - ``self.W_sat`` contains the saturation humidity ratio values
            aligned with ``self.T``.
          - Axis limits have already been finalized.
        - No saturation curve itself is drawn here — only its *extensions*.

        Examples
        --------
        Typical usage inside the rendering pipeline::

            chart._draw_saturation_curve()
            chart._draw_saturation_extensions()

        When debugging visually::

            fig, ax = plt.subplots()
            chart.ax = ax
            chart._draw_saturation_extensions()
            plt.show()
        """

        cfg = self.cfg
        ax = self.ax

        # --------------------------------------------------------------
        # Use the visible axis spine as visual reference (right y-axis)
        # --------------------------------------------------------------
        spine = ax.spines["right"]

        # Style inherits color and linewidth from the axis spine
        style = {
            "color": spine.get_edgecolor(),
            "lw": spine.get_linewidth(),
            "zorder": ZORDER["saturation"],
            # IMPORTANT: allow drawing beyond axes clipping
            "clip_on": False,
        }

        # --------------------------------------------------------------
        # 1) Vertical extension at T = t_min
        # --------------------------------------------------------------
        # Saturation humidity ratio at the minimum temperature
        W_left = float(self.W_sat[0])

        # Draw vertical line from W=0 to W=W_sat(T_min)
        ax.plot(
            [cfg.t_min, cfg.t_min],
            [0.0, W_left],
            **style,
        )

        # --------------------------------------------------------------
        # 2) Horizontal extension at the top of the chart (conditional)
        # --------------------------------------------------------------
        # We want the temperature T where:
        #     W_sat(T) = y_top
        # i.e., the saturation curve exits through the top boundary.
        W = self.W_sat
        T = self.T

        # Current upper y-limit of the axis (must already be finalized)
        y_top = ax.get_ylim()[1]

        # If the chart top is above the maximum saturation value,
        # the saturation curve never reaches the top boundary.
        if y_top > float(W.max()):
            return

        # Find first index where saturation exceeds or equals y_top
        i = int(np.searchsorted(W, y_top))

        if i <= 0:
            # Edge case: intersection occurs at the first sample
            T_exit = float(T[0])
        else:
            # Linear interpolation between surrounding points:
            # (T[i-1], W[i-1]) and (T[i], W[i])
            T0, W0 = float(T[i - 1]), float(W[i - 1])
            T1, W1 = float(T[i]), float(W[i])

            # Avoid division by zero (degenerate but safe guard)
            if W1 == W0:
                T_exit = T1
            else:
                frac = (y_top - W0) / (W1 - W0)
                T_exit = T0 + frac * (T1 - T0)

        # If the intersection is effectively at t_max,
        # the horizontal extension would be zero-length.
        if T_exit >= cfg.t_max - 1e-9:
            return

        # Draw horizontal line exactly at the top of the axes:
        # - x is in data coordinates
        # - y is fixed at the top boundary of the axes (y=1)
        ax.plot(
            [T_exit, cfg.t_max],
            [1.0, 1.0],
            transform=ax.get_xaxis_transform(),
            **style,
        )

    def _draw_tw_grid(self):
        """
        Draw the fundamental T × W grid aligned with axis ticks.
    
        This method renders the **base psychrometric grid** defined by the
        current axis ticks:
        - vertical lines follow dry-bulb temperature ticks (T),
        - horizontal lines follow humidity-ratio ticks (W).
    
        All grid lines are **physically clipped at the saturation curve**,
        ensuring that no grid element appears in the supersaturated region
        of the chart.
    
        The T × W grid serves as the geometric reference frame for:
        - isolines,
        - comfort zones,
        - index fields,
        - observational points.
    
        Grid visibility and styling are fully controlled via
        ``ChartConfig``.
    
        Notes
        -----
        - The grid strictly follows the axis ticks defined by Matplotlib.
        - Vertical lines are clipped analytically using the saturation
          humidity ratio at each temperature.
        - Horizontal lines are clipped numerically using the precomputed
          saturation curve ``self.W_sat``.
        """
    
        cfg = self.cfg
    
        # --------------------------------------------------------------
        # Early exit if grid is disabled by configuration
        # --------------------------------------------------------------
        if not cfg.show_tw_grid:
            return
    
        ax = self.ax
    
        # --------------------------------------------------------------
        # Grid style (user-configurable)
        # --------------------------------------------------------------
        # Default style only defines semantic z-order.
        # Additional style attributes (color, linewidth, linestyle, alpha)
        # may be provided by the user via cfg.tw_grid_style.
        style = {
            "zorder": ZORDER["grid"],
        }
        style.update(cfg.tw_grid_style or {})
    
        # --------------------------------------------------------------
        # Retrieve axis ticks (authoritative grid definition)
        # --------------------------------------------------------------
        x_ticks = ax.get_xticks()  # dry-bulb temperature ticks (°C)
        y_ticks = ax.get_yticks()  # humidity-ratio ticks (kg/kg)
    
        # --------------------------------------------------------------
        # Vertical grid lines: constant dry-bulb temperature (T = const)
        # --------------------------------------------------------------
        for T0 in x_ticks:
            # Ignore ticks outside the configured domain
            if T0 < cfg.t_min or T0 > cfg.t_max:
                continue
    
            # Saturation humidity ratio at this temperature
            # RH = 1.0 enforces clipping at saturation
            W_max = Psychrometrics.humidity_ratio(
                T0, 1.0, cfg.pressure
            )
    
            # Draw vertical line from W = 0 up to saturation
            ax.plot(
                [T0, T0],
                [0.0, W_max],
                **style,
            )
    
        # --------------------------------------------------------------
        # Horizontal grid lines: constant humidity ratio (W = const)
        # --------------------------------------------------------------
        for W0 in y_ticks:
            # Skip non-physical or trivial humidity levels
            if W0 <= 0:
                continue
    
            # Determine temperatures where this W is physically admissible
            # (i.e., below the saturation curve)
            mask = self.W_sat >= W0
            if not np.any(mask):
                continue
    
            T_valid = self.T[mask]
    
            # Draw horizontal line only where W <= W_sat(T)
            ax.plot(
                T_valid,
                np.full_like(T_valid, W0),
                **style,
            )
    

    # ==================================================================
    # Reference points
    # ==================================================================
    def _draw_points(self):
        """
        Render discrete reference points on the psychrometric chart.
    
        Each point is defined by dry-bulb temperature and relative humidity.
        The corresponding humidity ratio is computed internally using the
        chart pressure and the psychrometric model.
    
        Notes
        -----
        - This method performs *coordinate conversion only*.
        - No validation or inference is performed here.
        - Visual attributes are taken directly from each ``Point`` instance.
        """
        for p in self.points:
            # --------------------------------------------------------------
            # Convert thermodynamic state to chart coordinates
            # --------------------------------------------------------------
            w = Psychrometrics.humidity_ratio(
                T=p.t,
                RH=p.rh,
                P=self.cfg.pressure,
            )
    
            # --------------------------------------------------------------
            # Draw marker
            # --------------------------------------------------------------
            self.ax.scatter(
                p.t,
                w,
                marker=p.marker,
                color=p.color,
                s=p.size,
                alpha=p.alpha,
                zorder=p.zorder,
            )
    
            # --------------------------------------------------------------
            # Draw label (optional)
            # --------------------------------------------------------------
            if p.show_label and p.label:
                self.ax.annotate(
                    p.label,
                    (p.t, w),
                    textcoords="offset points",
                    xytext=(5, 5),
                    color=p.color,
                    fontsize="small",
                    zorder=p.zorder,
                )
                                
    # ==================================================================
    # Main rendering pipeline
    # ==================================================================
    def draw(self) -> Axes:
        """
        Render the complete psychrometric chart.

        This method executes the full rendering pipeline following a strictly
        defined semantic layer order. Each stage corresponds to a conceptual
        rendering category, ensuring deterministic behavior, reproducibility,
        and clear separation between:

        - Domain-based computations
        - Data-driven overlays
        - Physical constraints
        - Presentation formatting

        Rendering Pipeline (Ordered Layers)
        -----------------------------------

        Background Layers (continuous fields)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        1. Density fields
           Statistical or interpolated scalar fields derived from
           observational datasets.

        2. Domain index fields
           Continuous index values evaluated over the thermodynamic
           psychrometric domain (e.g., ITU(T, RH)).

        3. Domain index zones
           Categorical regions derived from domain index thresholds.

        Observational Overlays
        ~~~~~~~~~~~~~~~~~~~~~~
        4. Observational overlays
           Scatter layers, trajectories, or data-index projections
           based on measured T,RH records.

        Physical Boundaries
        ~~~~~~~~~~~~~~~~~~~
        5. Saturation curve
           Physical upper boundary (100% relative humidity).

        Foreground Analytical Layers
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        6. Thermodynamic zones
           Predefined psychrometric comfort or stress regions.

        7. Psychrometric isolines
           Lines of constant physical properties
           (enthalpy, wet-bulb temperature, specific volume, etc.).

        8. Reference points
           Explicit user-defined state markers.

        Final Presentation
        ~~~~~~~~~~~~~~~~~~
        9. Axis formatting
           Labels, limits, title, and visual refinements.

        Returns
        -------
        ax : matplotlib.axes.Axes
            Axes instance containing the fully rendered diagram.

        Notes
        -----
        - The matplotlib Figure object is created internally.
        - This method does not call ``plt.show()`` or ``savefig()``.
          Displaying or exporting the figure is the responsibility
          of the caller.
        - No scientific computation is performed in this method.
          All physical calculations occur prior to rendering.
        - The rendering order is intentionally deterministic to
          guarantee layer composability and visual stability.

        Architectural Guarantees
        -------------------------
        - Domain computations are independent of observational data.
        - Observational overlays never modify the psychrometric domain.
        - Presentation formatting is applied strictly after all geometry.
        - No state mutation occurs outside rendering concerns.

        Examples
        --------
        Basic usage:

        >>> chart = PsychrometricChart(cfg)
        >>> ax = chart.draw()

        Saving the result:

        >>> ax.figure.savefig("diagram.png", dpi=300)

        Advanced usage (adding custom overlays before draw):

        >>> chart.add_zone(my_zone)
        >>> chart.add_index(my_index)
        >>> ax = chart.draw()
        """

        self._prepare_axes()
        self._prepare_domain()
    
        # ------------------------------------------------------------------
        # Background layers
        # ------------------------------------------------------------------
        #draw_density_field(self.ax, self)
        draw_indexes(self, self.ax)
        draw_index_zones(self, self.ax)

        # ------------------------------------------------------------------
        # Canonical data-driven layers
        # ------------------------------------------------------------------
        auto_legend_handles = draw_data_layers(self, self.ax)
        draw_chart_legend(self.ax, self.cfg, auto_legend_handles)
        
        # ------------------------------------------------------------------
        # Physical boundaries
        # ------------------------------------------------------------------
        self._draw_saturation_curve()

        # ------------------------------------------------------------------
        # Foreground layers
        # ------------------------------------------------------------------
        draw_zones(self.ax, self)
        draw_isolines(self.ax, self)
        self._draw_points()

        operational_overlays = getattr(self.cfg, "operational_overlays", None)
        if operational_overlays:
            for overlay_cfg in operational_overlays:
                draw_operational_zones(self.ax, self, overlay_cfg)

        # ------------------------------------------------------------------
        # Final formatting
        # ------------------------------------------------------------------
        self._finalize_axes()
        
        return self.ax


