from typing import Any
from psychchart.data.config import ObservationsConfig

class ObservationParser:
    """
    Abstract interface for psychrometric observation parsers.

    This class defines the **minimal contract** for objects capable
    of parsing external data sources and translating them into
    :class:`ObservationsConfig` instances.

    An observation parser is responsible for:
    - reading a data source (file, object, stream, etc.),
    - extracting psychrometric variables (T, RH),
    - optionally extracting time information and metadata,
    - returning a fully populated ``ObservationsConfig``.

    This base class does NOT:
    - implement any parsing logic,
    - assume a specific file format,
    - perform validation or cleaning,
    - perform psychrometric computations.

    Concrete subclasses must implement the :meth:`parse` method.

    Design philosophy
    -----------------
    - Explicit interface instead of implicit duck-typing
    - One parser per data source / format
    - Parsing isolated from plotting and computation
    - Easy extensibility without modifying core code

    Typical use cases
    -----------------
    - CSV files with T and RH columns
    - EPW weather files
    - NetCDF / HDF datasets
    - Pandas DataFrames
    - In-memory simulation outputs

    Notes
    -----
    - This class intentionally does not use ``abc.ABC`` to keep
      dependencies minimal and allow flexible inheritance.
    - Parsers should be *stateless* whenever possible.
    """

    def parse(self, source: Any) -> ObservationsConfig:
        """
        Parse an external data source into psychrometric observations.

        This method must be implemented by subclasses and should
        return an instance of :class:`ObservationsConfig`.

        Parameters
        ----------
        source : Any
            Data source to be parsed.

            The type and meaning of ``source`` depend on the concrete
            parser implementation. Examples include:
            - file paths (str or Path)
            - file-like objects
            - pandas DataFrames
            - dictionaries or custom objects

        Returns
        -------
        ObservationsConfig
            Declarative configuration containing parsed observations.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by a subclass.

        Examples
        --------
        Example: implementing a CSV-based parser

        >>> class CSVObservationParser(ObservationParser):
        ...     def parse(self, source):
        ...         import pandas as pd
        ...         df = pd.read_csv(source)
        ...         return ObservationsConfig(
        ...             T=df["T"].values,
        ...             RH=df["RH"].values / 100.0,
        ...             time=df.get("time"),
        ...             metadata={"source": source},
        ...         )

        Example: using a parser

        >>> parser = CSVObservationParser()
        >>> cfg = parser.parse("observations.csv")
        >>> obs = Observations(cfg)

        The returned ``ObservationsConfig`` can then be passed
        to the interpretation and plotting layers.
        """
        raise NotImplementedError(
            "Subclasses must implement the parse() method."
        )

