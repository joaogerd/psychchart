from typing import Iterable, List, Optional, Sequence, Any, Dict

import numpy as np

from psychchart.config import Point, PathConfig
from psychchart.psychrometrics import Psychrometrics
from psychchart.data.density import DensityFieldData
from .config import ObservationsConfig


class Observations:
    """
    Interpreted psychrometric observations.

    This class provides a **thin interpretation layer** on top of
    :class:`ObservationsConfig`.

    While ``ObservationsConfig`` is purely declarative, this class
    introduces *minimal operational logic* required to:
    - ensure structural consistency,
    - perform filtering and grouping operations,
    - translate raw observations into chart entities.

    The class follows the same design philosophy as ``PsychChart``:
    - imperative (explicit method calls),
    - minimal responsibilities,
    - no hidden side effects.

    Responsibilities
    ----------------
    - Convert raw sequences into NumPy arrays for safe vector operations
    - Enforce minimal structural validation (array lengths)
    - Provide filtering by mask, time, and calendar attributes
    - Group observations along simple temporal dimensions
    - Translate observations into :class:`Point` entities

    Non-responsibilities
    --------------------
    - Psychrometric computations (W, h, etc.)
    - Plotting logic
    - Styling or visual configuration
    - Advanced statistical analysis
    - File I/O or parsing
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, cfg: ObservationsConfig):
        """
        Initialize interpreted observations from configuration.

        Parameters
        ----------
        cfg : ObservationsConfig
            Declarative observation configuration.
        """
        self.cfg = cfg

        # Convert raw sequences to NumPy arrays to ensure:
        # - consistent slicing
        # - vectorized operations
        # - predictable dtype behavior
        self.T = np.asarray(cfg.T, dtype=float)
        self.RH = np.asarray(cfg.RH, dtype=float)

        # Optional temporal coordinate
        self.time = (
            np.asarray(cfg.time)
            if cfg.time is not None
            else None
        )

        # Perform minimal structural validation
        self._validate_shapes()

    # ------------------------------------------------------------------
    # Validation (structural only)
    # ------------------------------------------------------------------
    def _validate_shapes(self):
        """
        Validate structural consistency of observation arrays.

        Ensures:
        - T and RH have identical lengths
        - time (if present) matches the same length

        No physical validation is performed.
        """
        n = len(self.T)

        if len(self.RH) != n:
            raise ValueError("T and RH must have the same length.")

        if self.time is not None and len(self.time) != n:
            raise ValueError("time must have the same length as T and RH.")

    # ------------------------------------------------------------------
    # Generic filtering
    # ------------------------------------------------------------------
    def filter(self, mask: Sequence[bool]) -> "Observations":
        """
        Return a filtered subset of observations.

        Parameters
        ----------
        mask : sequence of bool
            Boolean mask indicating which observations to keep.

        Returns
        -------
        Observations
            New instance containing only masked observations.

        Examples
        --------
        >>> obs_hot = obs.filter(obs.T > 30.0)
        """
        mask = np.asarray(mask, dtype=bool)

        return Observations(
            ObservationsConfig(
                T=self.T[mask],
                RH=self.RH[mask],
                time=self.time[mask] if self.time is not None else None,
                label=self.cfg.label,
                metadata=self.cfg.metadata,
            )
        )

    # ------------------------------------------------------------------
    # Time-based filtering
    # ------------------------------------------------------------------
    def filter_time(self, mask: Sequence[bool]) -> "Observations":
        """
        Filter observations using a boolean mask over the time axis.

        Parameters
        ----------
        mask : sequence of bool
            Boolean mask aligned with the time dimension.

        Returns
        -------
        Observations
            Filtered observations.

        Raises
        ------
        ValueError
            If no time axis is defined.
        """
        if self.time is None:
            raise ValueError("No time axis defined for these observations.")

        mask = np.asarray(mask, dtype=bool)

        return Observations(
            ObservationsConfig(
                T=self.T[mask],
                RH=self.RH[mask],
                time=self.time[mask],
                label=self.cfg.label,
                metadata=self.cfg.metadata,
            )
        )

    def filter_month(self, months: Iterable[int]) -> "Observations":
        """
        Filter observations by calendar month.

        Parameters
        ----------
        months : iterable of int
            Months to retain (1–12).

        Returns
        -------
        Observations
            Observations restricted to selected months.

        Examples
        --------
        >>> summer = obs.filter_month([12, 1, 2])
        """
        if self.time is None:
            raise ValueError("No time axis defined.")

        months = set(months)

        # Extract month from numpy.datetime64
        month_labels = np.array(
            [
                t.astype("datetime64[M]").astype(int) % 12 + 1
                for t in self.time
            ]
        )

        mask = np.array([m in months for m in month_labels])

        return self.filter_time(mask)

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------
    def groupby(self, key: str) -> Dict[Any, "Observations"]:
        """
        Group observations by a temporal key.

        Supported keys:
        - "month" → calendar month (1–12)
        - "hour"  → hour of day (0–23)

        Parameters
        ----------
        key : str
            Temporal grouping key.

        Returns
        -------
        dict
            Mapping ``group_value → Observations``.

        Raises
        ------
        ValueError
            If no time axis is defined or key is unsupported.

        Examples
        --------
        >>> groups = obs.groupby("month")
        >>> jan = groups[1]

        >>> hourly = obs.groupby("hour")
        >>> noon = hourly[12]
        """
        if self.time is None:
            raise ValueError("No time axis defined.")

        groups: Dict[Any, Observations] = {}

        if key == "month":
            labels = np.array(
                [
                    t.astype("datetime64[M]").astype(int) % 12 + 1
                    for t in self.time
                ]
            )

        elif key == "hour":
            labels = np.array(
                [
                    t.astype("datetime64[h]").astype(int) % 24
                    for t in self.time
                ]
            )

        else:
            raise ValueError(f"Unsupported groupby key: {key}")

        for value in np.unique(labels):
            mask = labels == value
            groups[value] = self.filter_time(mask)

        return groups

    # ------------------------------------------------------------------
    # Translation to chart entities
    # ------------------------------------------------------------------
    def to_points(
        self,
        reducer: Optional[str] = None,
        label: Optional[str] = None,
    ) -> List[Point]:
        """
        Translate observations into chart ``Point`` entities.

        Parameters
        ----------
        reducer : {"mean", "median"} or None
            Reduction strategy.
        label : str, optional
            Label assigned to resulting points.

        Returns
        -------
        list of Point
        """
        lbl = label or self.cfg.label or ""

        if reducer is None:
            return [
                Point(label=lbl, t=float(t), rh=float(rh))
                for t, rh in zip(self.T, self.RH)
            ]

        if reducer == "mean":
            return [
                Point(
                    label=lbl,
                    t=float(np.mean(self.T)),
                    rh=float(np.mean(self.RH)),
                )
            ]

        if reducer == "median":
            return [
                Point(
                    label=lbl,
                    t=float(np.median(self.T)),
                    rh=float(np.median(self.RH)),
                )
            ]

        raise ValueError(f"Unknown reducer: {reducer}")
    
    # ------------------------------------------------------------------
    # Translate observations into a psychrometric path.
    # ------------------------------------------------------------------
    def to_path(self, label: Optional[str] = None) -> PathConfig:
        """
        Convert observations into a psychrometric path (trajectory).
    
        This method translates the full sequence of observations into
        a :class:`PathConfig` object, preserving the original ordering
        of the data.
    
        The resulting path represents a **continuous trajectory**
        in psychrometric space (T–RH), typically associated with:
        - temporal evolution (e.g., hourly or daily cycles),
        - process tracking,
        - environmental or experimental transitions.
    
        No reduction, interpolation, or validation is performed.
        The path follows the exact sequence stored in this object.
    
        Parameters
        ----------
        label : str, optional
            Label assigned to the resulting path.
            If not provided, the method falls back to:
            - ``ObservationsConfig.label``, or
            - an empty string if no label is available.
    
        Returns
        -------
        PathConfig
            Declarative configuration describing the psychrometric
            trajectory.
    
        Notes
        -----
        - The ordering of points is preserved exactly as stored.
        - This method does NOT:
            * sort by time,
            * resample data,
            * check for missing values,
            * compute psychrometric quantities.
        - Any visual customization (color, colormap, linewidth, etc.)
          should be applied *after* calling this method.
    
        Design considerations
        ---------------------
        - This method mirrors the design of :meth:`to_points`, providing
          a symmetric API:
            * ``to_points`` → discrete representation
            * ``to_path``   → continuous representation
        - Separating paths from points avoids semantic overload and
          enables richer visual narratives.
    
        Examples
        --------
        Create a path from hourly observations:
    
        >>> obs = Observations(obs_cfg)
        >>> path = obs.to_path(label="Hourly evolution")
    
        Customize path appearance:
    
        >>> path = obs.to_path(label="Daily cycle")
        >>> path.color = "tab:red"
        >>> path.linewidth = 2.0
    
        Integrate path into a psychrometric chart:
    
        >>> chart = PsychChart(
        ...     cfg=cfg,
        ...     paths=[path],
        ... )
        >>> chart.draw()
        """
        # Resolve label precedence:
        # explicit label > config label > empty string
        lbl = label or self.cfg.label or ""
    
        # Build declarative path configuration
        return PathConfig(
            label=lbl,
            T=self.T,
            RH=self.RH,
        )

    # ------------------------------------------------------------------
    # Indexed psychrometric path
    # ------------------------------------------------------------------
    def to_indexed_path(
        self,
        index,
        label: Optional[str] = None,
        *,
        cmap: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        linewidth: float = 1.5,
        linestyle: str = "-",
        alpha: float = 1.0,
    ) -> PathConfig:
        """
        Translate observations into a psychrometric path colored by an index.

        This method converts the full sequence of observations into a
        :class:`PathConfig` describing a **trajectory in psychrometric space**
        (T–RH), enriched with scalar values obtained from a bioclimatic or
        thermal index.

        The index is evaluated *pointwise* along the observation sequence
        and attached to the path, enabling:
        - color-mapped trajectories,
        - visualization of index evolution,
        - combined thermodynamic + comfort/stress analysis.

        All computation is performed here; the resulting PathConfig is
        purely declarative and contains no plotting logic.

        Parameters
        ----------
        index : object
            Index engine instance providing an ``evaluate(T, RH)`` method.

            The expected signature is::

                index.evaluate(T, RH) -> array-like

            where:
            - ``T``  : dry-bulb temperature (°C)
            - ``RH`` : relative humidity (fraction, 0–1)

            Typical examples include ITUIndex, THIIndex, HLIIndex, or
            user-defined custom indices.
        label : str, optional
            Label assigned to the resulting path.

            Resolution order:
            1. Explicit ``label`` argument
            2. ``ObservationsConfig.label``
            3. ``index.name`` (if present)
        cmap : str, optional
            Matplotlib colormap name used to map index values to colors
            along the path.
        vmin, vmax : float, optional
            Lower and upper bounds for color normalization.
            If None, Matplotlib will infer limits from the data.
        linewidth : float, optional
            Width of the path line (default: 1.5).
        linestyle : str, optional
            Line style of the path (default: "-").
        alpha : float, optional
            Transparency of the path (0–1).

        Returns
        -------
        PathConfig
            Declarative description of a colored psychrometric path,
            including:
            - ordered T and RH values,
            - index values along the trajectory,
            - visualization parameters.

        Raises
        ------
        ValueError
            If the index evaluation does not return an array with the
            same length as the observations.

        Notes
        -----
        - Index computation is intentionally performed here, not in the
          rendering layer, to preserve separation of concerns.
        - The ordering of observations is preserved exactly.
        - No resampling, smoothing, clipping, or physical validation
          is performed.
        - The returned PathConfig contains **no matplotlib code**.

        Design considerations
        ---------------------
        - This method extends :meth:`to_path` by adding a scalar dimension
          (the index) to the trajectory.
        - Keeping index evaluation outside plotting logic makes paths
          reusable across charts and layouts.
        - Styling is captured declaratively and interpreted later by
          ``draw_paths``.

        Examples
        --------
        Create an indexed path using ITU:

        >>> from psychchart.indexes import ITU
        >>> path = obs.to_indexed_path(
        ...     ITU,
        ...     label="ITU evolution",
        ...     cmap="inferno",
        ...     vmin=60,
        ...     vmax=90,
        ...     linewidth=2.0,
        ... )

        Create an indexed path with automatic color scaling:

        >>> path = obs.to_indexed_path(
        ...     ITU,
        ...     cmap="viridis",
        ... )

        Integrate into a psychrometric chart:

        >>> chart = PsychChart(cfg=cfg, paths=[path])
        >>> chart.draw()
        """

        # --------------------------------------------------------------
        # Resolve label precedence
        # --------------------------------------------------------------
        if label is not None:
            lbl = label
        elif self.cfg.label is not None:
            lbl = self.cfg.label
        else:
            # Fallback: use index name if available
            lbl = getattr(index, "name", "")

        # --------------------------------------------------------------
        # Evaluate index along the observation sequence
        # --------------------------------------------------------------
        # Expected to return one value per (T, RH) pair
        values = index.evaluate(self.T, self.RH)
        values = np.asarray(values, dtype=float)

        # Structural consistency check
        if values.shape[0] != self.T.shape[0]:
            raise ValueError(
                "Index evaluation must return an array with the same "
                "length as the observations."
            )

        # --------------------------------------------------------------
        # Build declarative PathConfig
        # --------------------------------------------------------------
        return PathConfig(
            label=lbl,
            T=self.T,
            RH=self.RH,
            values=values,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            linewidth=linewidth,
            linestyle=linestyle,
            alpha=alpha,
        )


    # ------------------------------------------------------------------
    # Convenience grouping methods
    # ------------------------------------------------------------------
    def groupby_month(self) -> dict[int, "Observations"]:
        """
        Group observations by calendar month.

        This is a semantic convenience wrapper around::

            self.groupby("month")

        It improves readability and discoverability of the API,
        especially in exploratory and scientific workflows.

        Returns
        -------
        dict[int, Observations]
            Mapping ``month → Observations``, where month is an
            integer in the range 1–12.

        Raises
        ------
        ValueError
            If no time axis is defined.

        Examples
        --------
        Group observations by month:

        >>> monthly = obs.groupby_month()
        >>> january = monthly[1]

        Compute monthly mean points:

        >>> points = [
        ...     g.to_points(reducer="mean", label=f"Month {m}")[0]
        ...     for m, g in monthly.items()
        ... ]

        Notes
        -----
        - Month extraction is based on ``numpy.datetime64``.
        - No sorting is enforced; keys appear in ascending order
          only if present in the data.
        """
        return self.groupby("month")
    

    def to_density_field(self, cfg, chart_cfg) -> DensityFieldData:
        """
        Compute a psychrometric density field from observations.
    
        This method transforms a collection of observed psychrometric
        states into a **2D density field** over the psychrometric domain,
        suitable for visualization as a heatmap.
    
        The density is computed in **(T, W) space**, where:
        - ``T`` is the dry-bulb temperature (°C),
        - ``W`` is the humidity ratio (kg_vapor / kg_dry_air).
    
        Using (T, W) instead of (T, RH) ensures:
        - correct thermodynamic geometry,
        - linear axes for rendering,
        - compatibility with standard psychrometric charts.
    
        Parameters
        ----------
        cfg : DensityFieldConfig
            Configuration object defining:
            - histogram resolution (number of bins),
            - normalization behavior (counts vs probability density).
        chart_cfg : ChartConfig
            Global chart configuration, providing atmospheric pressure
            and domain limits.
    
        Returns
        -------
        DensityFieldData
            Container holding:
            - bin edges in temperature (T_edges),
            - bin edges in humidity ratio (W_edges),
            - computed density or frequency values.
    
        Notes
        -----
        - Density computation is performed using ``numpy.histogram2d``.
        - When ``cfg.normalize=True``, the returned values represent a
          probability density (integrates to 1 over the domain).
          Then the returned histogram is the sample density, defined 
          such that the sum over bins of the product bin_value * bin_area is 1.
        - When ``cfg.normalize=False``, the returned values represent
          raw observation counts per bin.
        - No clipping to the saturation curve is performed here; this
          must be handled explicitly in the rendering layer.
        - No smoothing or KDE is applied.
    
        Design considerations
        ---------------------
        - This method performs **numerical computation only**.
        - No plotting or Matplotlib objects are created.
        - The output is suitable for direct use with
          ``matplotlib.pcolormesh``.
        - The transpose of the histogram is intentional and required
          for correct axis alignment in Matplotlib.
    
        Examples
        --------
        Compute a normalized density field from observations:
    
        >>> density_cfg = DensityFieldConfig(
        ...     bins=(60, 60),
        ...     normalize=True,
        ... )
        >>> density_data = obs.to_density_field(density_cfg, chart.cfg)
    
        Render the density field:
    
        >>> draw_density_field(ax, density_data, density_cfg)
    
        Combine density with trajectories:
    
        >>> chart.density_field = density_cfg
        >>> chart.paths = [obs.to_path(label="Trajectory")]
        >>> chart.draw()
        """
    
        # --------------------------------------------------------------
        # Convert observations to psychrometric coordinates (T, W)
        # --------------------------------------------------------------
        # T is already available as dry-bulb temperature (°C)
        T = self.T
    
        # Convert relative humidity to humidity ratio using chart pressure
        W = Psychrometrics.humidity_ratio(
            T,
            self.RH,
            chart_cfg.pressure,
        )
    
        # --------------------------------------------------------------
        # Compute 2D histogram in (T, W) space
        # --------------------------------------------------------------
        # numpy.histogram2d returns:
        #   H        → histogram values (shape: n_T, n_W)
        #   T_edges  → bin edges along temperature
        #   W_edges  → bin edges along humidity ratio
        #
        # Note: density=True normalizes such that the integral is 1.
        H, T_edges, W_edges = np.histogram2d(
            T,
            W,
            bins=cfg.bins,
            density=cfg.normalize,
        )
    
        # --------------------------------------------------------------
        # Package results into declarative data container
        # --------------------------------------------------------------
        return DensityFieldData(
            T_edges=T_edges,
            W_edges=W_edges,
            values=H.T,   # transpose for correct pcolormesh orientation
        )
    

