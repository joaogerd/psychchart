from typing import Optional, Any

try:
    import pandas as pd
except ImportError:
    pd = None

from psychchart.data.config import ObservationsConfig
from .base import ObservationParser

class CSVObservationParser:
    """
    CSV-based parser for psychrometric observations.

    This class implements a **minimal and explicit translation layer**
    between tabular CSV data and the internal canonical representation
    used by the psychchart library (:class:`ObservationsConfig`).

    Responsibilities
    ----------------
    - Read CSV files using pandas
    - Extract temperature and relative humidity columns
    - Optionally parse a time axis
    - Normalize relative humidity units when requested
    - Return a fully populated :class:`ObservationsConfig`

    Non-responsibilities
    --------------------
    This parser intentionally does NOT:
    - validate physical ranges (e.g., RH > 1, negative temperature)
    - perform psychrometric calculations (W, h, v, etc.)
    - resample or interpolate time series
    - apply statistical reductions
    - perform plotting or chart interaction

    This strict separation ensures that:
    - data ingestion remains simple and predictable
    - scientific logic lives elsewhere in the system
    - parsers can be swapped or extended safely

    Parameters
    ----------
    t_col : str
        Name of the column containing dry-bulb air temperature (°C).
    rh_col : str
        Name of the column containing relative humidity.
    time_col : str, optional
        Name of the column containing timestamps or dates.
        If None, no time axis is parsed.
    rh_unit : {"fraction", "percent"}, optional
        Unit of the relative humidity column:
        - "fraction" → values already in [0, 1]
        - "percent"  → values in [0, 100], converted internally
    time_format : str, optional
        Optional datetime format string passed to
        ``pandas.to_datetime``.
        If None, pandas will attempt automatic parsing.
    encoding : str, optional
        File encoding passed to ``pandas.read_csv``.

    Notes
    -----
    - This parser requires pandas. If pandas is not installed,
      an ImportError is raised at runtime.
    - The returned data is *not* copied defensively; it is assumed
      to be immutable at higher layers.
    - All numeric arrays are converted to NumPy arrays with
      dtype=float for consistency.
    """

    def __init__(
        self,
        t_col: str,
        rh_col: str,
        time_col: Optional[str] = None,
        rh_unit: str = "fraction",
        time_format: Optional[str] = None,
        encoding: Optional[str] = None,
    ):
        # Column mapping
        self.t_col = t_col
        self.rh_col = rh_col
        self.time_col = time_col

        # Units and parsing options
        self.rh_unit = rh_unit
        self.time_format = time_format
        self.encoding = encoding

    # ------------------------------------------------------------------
    # Main parsing routine
    # ------------------------------------------------------------------
    def parse(self, path: str) -> ObservationsConfig:
        """
        Parse a CSV file into an ObservationsConfig object.

        Parameters
        ----------
        path : str
            Path to the CSV file containing psychrometric observations.

        Returns
        -------
        ObservationsConfig
            Declarative container with temperature, relative humidity,
            optional time axis, and metadata describing the data source.

        Raises
        ------
        ImportError
            If pandas is not installed.
        KeyError
            If required columns are missing from the CSV file.

        Notes
        -----
        - Relative humidity normalization is applied only if explicitly
          requested via ``rh_unit="percent"``.
        - Time parsing uses ``pandas.to_datetime`` and may raise
          parsing errors for malformed timestamps.
        """

        # --------------------------------------------------------------
        # Dependency check
        # --------------------------------------------------------------
        if pd is None:
            raise ImportError(
                "pandas is required to parse CSV files. "
                "Install it with `pip install pandas`."
            )

        # --------------------------------------------------------------
        # Read CSV file
        # --------------------------------------------------------------
        df = pd.read_csv(path, encoding=self.encoding)

        # --------------------------------------------------------------
        # Extract mandatory fields
        # --------------------------------------------------------------
        T = df[self.t_col].to_numpy(dtype=float)
        RH = df[self.rh_col].to_numpy(dtype=float)

        # --------------------------------------------------------------
        # Normalize relative humidity units
        # --------------------------------------------------------------
        # Accepts either:
        # - fraction (0–1): used as-is
        # - percent (0–100): converted to fraction
        if self.rh_unit == "percent":
            RH = RH / 100.0
        elif self.rh_unit != "fraction":
            raise ValueError(
                f"Unsupported RH unit: {self.rh_unit!r}. "
                "Use 'fraction' or 'percent'."
            )

        # --------------------------------------------------------------
        # Optional time axis
        # --------------------------------------------------------------
        time = None
        if self.time_col is not None:
            time_series = df[self.time_col]

            # Explicit datetime format (recommended for performance)
            if self.time_format is not None:
                time_series = pd.to_datetime(
                    time_series,
                    format=self.time_format
                )
            else:
                # Let pandas infer the format
                time_series = pd.to_datetime(time_series)

            time = time_series.to_numpy()

        # --------------------------------------------------------------
        # Build declarative configuration object
        # --------------------------------------------------------------
        return ObservationsConfig(
            T=T,
            RH=RH,
            time=time,
            metadata={
                "source": path,          # Original data source
                "format": "csv",         # Explicit input format
                "parser": self.__class__.__name__,
                "rh_unit": self.rh_unit,
            },
        )

