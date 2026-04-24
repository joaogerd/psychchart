"""
Runtime container for processed data layers.

This module defines the in-memory runtime representation of a canonical
``DataLayerConfig`` after file loading, thermodynamic normalization, optional
temporal ordering, and derived-field evaluation.

The runtime object reuses the existing observation infrastructure of
``psychchart.data``:

- ``Observations`` for density and trajectory semantics
- ``FunctionalObservations`` for scalar-field projection

This keeps the runtime compact, explicit, and consistent with the existing
data model of the project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from psychchart.data.functional import FunctionalObservations
from psychchart.data.observations import Observations


@dataclass(slots=True)
class ProcessedDataLayer:
    """
    Fully processed dataset-driven layer ready for rendering.

    Parameters
    ----------
    config : object
        Original validated data-layer configuration.
    frame : pandas.DataFrame
        Normalized runtime frame, including projected helper columns such as
        ``_T``, ``_RH``, and ``_W``, plus any derived fields.
    observations : Observations
        Interpreted observation collection built from projected runtime data.
    functional_observations : FunctionalObservations or None
        Extended observation collection including scalar fields, when present.
    T : ndarray
        Dry-bulb temperature vector in °C.
    RH : ndarray
        Relative humidity vector as fractions in ``[0, 1]``.
    W : ndarray
        Humidity-ratio vector in kg/kg.
    fields : dict of str to ndarray, optional
        Mapping of derived field names to numeric arrays.

    Notes
    -----
    This class contains no rendering logic.
    """

    config: object
    frame: pd.DataFrame
    observations: Observations
    functional_observations: Optional[FunctionalObservations]
    T: np.ndarray
    RH: np.ndarray
    W: np.ndarray
    fields: dict[str, np.ndarray] = field(default_factory=dict)

    def get_array(self, name: str) -> np.ndarray:
        """
        Return one runtime array by name.

        Parameters
        ----------
        name : str
            Field or runtime column name.

        Returns
        -------
        ndarray
            Runtime array associated with ``name``.

        Raises
        ------
        KeyError
            If the requested name does not exist.
        """
        if name in self.fields:
            return self.fields[name]

        if name in self.frame.columns:
            return self.frame[name].to_numpy()

        raise KeyError(f"Unknown runtime field or column: {name}")

    def ordered_frame(self, order_by: Optional[str] = None) -> pd.DataFrame:
        """
        Return the runtime frame optionally ordered by one column.

        Parameters
        ----------
        order_by : str or None, optional
            Column used for ordering.

        Returns
        -------
        pandas.DataFrame
            Ordered or original frame.
        """
        if order_by is None:
            return self.frame
        if order_by not in self.frame.columns:
            raise KeyError(f"Ordering column not found: {order_by}")
        return self.frame.sort_values(order_by).reset_index(drop=True)
