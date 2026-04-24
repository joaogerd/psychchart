from __future__ import annotations

from dataclasses import dataclass
import matplotlib.pyplot as plt
from psychchart.psychrometrics import Psychrometrics
import numpy as np



@dataclass
class ObservationLayer:
    """
    Visual representation of a DataIndex evaluated over observational data.

    This class acts as a pure rendering adapter between:

        FunctionalObservations  →  matplotlib axes

    It assumes that all data have already been:

    - Validated
    - Unit-normalized (°C, RH fraction)
    - Indexed (DataIndexes computed)
    - Structurally consistent

    Parameters
    ----------
    functional_obs : FunctionalObservations
        Container holding:

        - Thermodynamic coordinates (T in °C, RH in fraction)
        - One or more scalar index fields
        - Conversion utilities (e.g., to_points, to_scalar_field)

    config : DataIndexConfig
        Rendering configuration defining:

        - Which index to visualize
        - Whether to render scatter and/or scalar field
        - Colormap
        - Transparency
        - Binning strategy
        - Colorbar behavior

    Conceptual Model
    ----------------
    Observational layers are discrete projections of measured
    states onto the psychrometric domain.

    Unlike domain index fields:

        f(T, RH) → scalar

    Observational layers operate as:

        g(record_i) → scalar

    and are plotted at measured coordinates only.

    Rendering Modes
    ---------------
    - Scatter mode:
        Individual observation points colored by index value.

    - Scalar field mode:
        Binned 2D aggregation projected as a mesh over the domain.

    Architectural Guarantees
    -------------------------
    - No scientific computation occurs during rendering.
    - No mutation of observational data occurs.
    - Rendering order is deterministic.
    - Domain geometry remains untouched.
    - Axis formatting is handled elsewhere.

    Notes
    -----
    - Colorbars are created only if explicitly enabled.
    - Overlapping layers stack in call order.
    - This class does not manage legends or titles.
    """
    functional_obs: object
    config: object
    def _debug_array_stats(self, name: str, arr: np.ndarray) -> None:
        """
        Print detailed statistics of a numeric array for debugging purposes.
    
        Parameters
        ----------
        name : str
            Logical name of the array being inspected.
        arr : array-like
            Numerical array to inspect.
        """
        arr = np.asarray(arr)
    
        print(f"\n[DEBUG] {name}")
        print(f"  size       : {arr.size}")
        print(f"  dtype      : {arr.dtype}")
    
        if arr.size == 0:
            print("  [WARNING] Empty array")
            return
    
        print(f"  min        : {np.nanmin(arr):.6f}")
        print(f"  max        : {np.nanmax(arr):.6f}")
        print(f"  mean       : {np.nanmean(arr):.6f}")
        print(f"  std        : {np.nanstd(arr):.6f}")
        print(f"  nan count  : {np.isnan(arr).sum()}")
        print(f"  inf count  : {np.isinf(arr).sum()}")
        print(f"  unique     : {len(np.unique(arr))}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def draw(self, ax, chart):
        """
        Render the observational layer on the provided axes.

        This method delegates rendering to either:

        - Scatter visualization
        - Scalar field visualization
        - Or both

        depending on configuration flags.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Target axes.

        chart : PsychrometricChart
            Parent chart instance (read-only context).

        Notes
        -----
        - This method performs no data transformation.
        - It does not alter the psychrometric domain.
        - It does not apply axis formatting.
        - Rendering behavior is entirely driven by ``config``.
        """


        index_name = self.config.index

        if self.config.scalar_field:
            self._draw_scalar_field(ax, index_name)

        if self.config.scatter:
            self._draw_scatter(ax, index_name)

    # ------------------------------------------------------------------
    #
    # ------------------------------------------------------------------
    def _compute_obs_index_field(self, index_name):
    
        points = self.functional_obs.to_points()
    
        TT = np.array([p.t for p in points], dtype=float)
        RH = np.array([p.rh for p in points], dtype=float)
    
        WW = Psychrometrics.humidity_ratio(TT, RH)
        ZZ = np.asarray(self.functional_obs.fields[index_name], dtype=float)
    
        # --------------------------------------------------
        # Debug checks
        # --------------------------------------------------
        self._debug_array_stats("TT (Temperature °C)", TT)
        self._debug_array_stats("RH (Relative Humidity frac)", RH)
        self._debug_array_stats("WW (Humidity ratio kg/kg)", WW)
        self._debug_array_stats(f"ZZ ({index_name})", ZZ)
        vals, counts = np.unique(TT, return_counts=True)
        print("  most frequent T:", vals[np.argmax(counts)])
        print("  max frequency :", counts.max())

        return TT, WW, ZZ



    # ------------------------------------------------------------------
    # Scatter rendering
    # ------------------------------------------------------------------
    def _draw_scatter(self, ax, index_name):
        """
        Render observational points as a colored scatter plot.

        Each point represents an individual measured thermodynamic
        state (T, RH) colored by the selected DataIndex value.

        The colormap and visual properties are defined in ``config``.

        Notes
        -----
        - Coordinates must already be normalized.
        - Index values must already exist.
        - No aggregation occurs.
        - Colorbar creation is optional.
        """

        TT, WW, Z = self._compute_obs_index_field(index_name)
        
        scatter = ax.scatter(
            TT,
            WW,
            c=Z,
            cmap=self.config.cmap,
            s=getattr(self.config, "size", 20),
            alpha=self.config.alpha,
            edgecolor="black",
        )

        if self.config.colorbar:
            plt.colorbar(scatter, ax=ax, label=index_name)

    # ------------------------------------------------------------------
    # Scalar field rendering
    # ------------------------------------------------------------------
    def _draw_scalar_field(self, ax, index_name):
        """
        Render a binned scalar field derived from observational data.

        This visualization represents aggregated index values over
        the psychrometric plane using a 2D binning strategy.

        The resulting field is projected via ``pcolormesh``.

        Notes
        -----
        - Binning is performed upstream via FunctionalObservations.
        - This method does not compute statistics.
        - It only visualizes the provided field.
        - Shading is set to 'auto' for compatibility.
        - Colorbar creation is optional.
        """

        field = self.functional_obs.to_scalar_field(
            index_name,
            bins=self.config.bins,
        )
        print(field.T_edges)
        print(field.W_edges)
        print(field.values)
        mesh = ax.pcolormesh(
            field.T_edges,
            field.W_edges,
            field.values,
            cmap=self.config.cmap,
            shading="auto",
            alpha=self.config.alpha,
        )

        if self.config.colorbar:
            plt.colorbar(mesh, ax=ax, label=index_name)
