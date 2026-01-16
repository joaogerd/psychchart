from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence


@dataclass
class ObservationsConfig:
    """
    Declarative configuration for psychrometric observations.
    
    This class represents a **collection of psychrometric states**
    defined in terms of dry-bulb temperature (T) and relative humidity (RH).
    These states may originate from:
    - field measurements,
    - numerical simulations,
    - design scenarios,
    - diagnostic outputs.
    
    The class is intentionally **lightweight and declarative**.
    It serves exclusively as a *data container* and does not implement
    any interpretation, computation, or visualization logic.
    
    ObservationsConfig is an **input model**, not a plotting entity.
    It must be interpreted by higher-level components before it can be
    rendered in a psychrometric chart.
    
    Typical workflow
    ----------------
    ObservationsConfig → Observations → chart entities → PsychChart
    
    Responsibilities
    ----------------
    - Store raw psychrometric variables (T, RH)
    - Optionally associate a time axis
    - Optionally carry a semantic label
    - Carry arbitrary metadata
    
    Non-responsibilities
    --------------------
    - File parsing (CSV, EPW, NetCDF, etc.)
    - Validation of value ranges or array lengths
    - Psychrometric computations (W, h, v, etc.)
    - Plotting, styling, or axis management
    - Temporal interpolation or aggregation
    
    All interpretation, validation, aggregation, and rendering logic
    must be implemented by higher-level components.
    
    Parameters
    ----------
    T : sequence of float
        Dry-bulb air temperature values in degrees Celsius (°C).
    
        Expected invariant:
            - All values refer to the same pressure level.
            - Length defines the number of observations (N).
    
    RH : sequence of float
        Relative humidity values expressed as fractions in the
        closed interval [0, 1].
    
        Expected invariant:
            - ``len(RH) == len(T)``
    
    time : sequence of Any, optional
        Optional time coordinate associated with each observation.
    
        Typical types include:
        - ``datetime`` objects,
        - ISO-formatted strings,
        - numeric time steps.
    
        If provided, its length should match ``T`` and ``RH``.
    
    label : str, optional
        Human-readable label identifying this observation set.
    
        Used for:
        - legends,
        - grouping multiple datasets,
        - annotations,
        - reporting.
    
    metadata : dict, optional
        Free-form metadata dictionary.
    
        Typical entries include:
        - station or sensor identifier,
        - geographic location,
        - data source,
        - timezone,
        - experiment or scenario name,
        - quality-control flags.
    
        Defaults to an empty dictionary.
    
    Notes
    -----
    - This class performs **no validation** by design.
      Validation may be implemented upstream or in optional helpers.
    - Observations are assumed to be defined in (T, RH) space and
      converted internally to (T, W) only during plotting or analysis.
    - Using generic ``Sequence`` types allows easy integration with:
        * lists
        * tuples
        * NumPy arrays
        * pandas Series
    
    Design considerations
    ---------------------
    - Keeping this class declarative avoids coupling data containers
      with computation or rendering logic.
    - The absence of validation makes the class flexible and suitable
      for configuration-driven workflows (YAML / JSON).
    - Metadata is intentionally unstructured to support diverse
      scientific and operational contexts.
    
    Examples
    --------
    Example 1: Single design condition
    
    >>> obs_cfg = ObservationsConfig(
    ...     T=[25.0],
    ...     RH=[0.60],
    ...     label="Design condition",
    ... )
    
    Example 2: Time series of measurements
    
    >>> from datetime import datetime, timedelta
    >>> times = [
    ...     datetime(2025, 1, 1, 0) + timedelta(hours=i)
    ...     for i in range(3)
    ... ]
    >>> obs_cfg = ObservationsConfig(
    ...     T=[24.5, 25.0, 26.2],
    ...     RH=[0.55, 0.58, 0.62],
    ...     time=times,
    ...     label="Hourly measurements",
    ...     metadata={"station": "AWS-001"},
    ... )
    
    >>> from psychchart.data.observations import Observations
    >>> obs = Observations(obs_cfg)
    
    >>> points = obs.to_points()
    >>> path = obs.to_path(label="Daily cycle")
    
    The plotting layer is responsible for converting (T, RH)
    to humidity ratio and rendering the resulting chart entities.
    """


    # ------------------------------------------------------------------
    # Core psychrometric variables (arrays of equal length N)
    # ------------------------------------------------------------------
    T: Sequence[float]                 # dry-bulb temperature [°C]
    RH: Sequence[float]                # relative humidity [0–1]

    # ------------------------------------------------------------------
    # Optional temporal coordinate
    # ------------------------------------------------------------------
    time: Optional[Sequence[Any]] = None

    # ------------------------------------------------------------------
    # Optional semantic label
    # ------------------------------------------------------------------
    label: Optional[str] = None

    # ------------------------------------------------------------------
    # Arbitrary metadata container
    # ------------------------------------------------------------------
    metadata: Dict[str, Any] = field(default_factory=dict)

