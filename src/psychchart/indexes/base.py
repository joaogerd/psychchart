"""
Base classes for thermal and bioclimatic comfort indexes.

This module defines abstract base classes intended to standardize
the implementation of empirical or semi-empirical thermal comfort
and heat stress indexes.

Important conceptual note
-------------------------
Thermal/bioclimatic indexes (e.g., THI, HLI, UTCI, BGHI) are **not**
psychrometric relationships themselves. Instead, they *use*
meteorological and physiological variables (temperature, humidity,
radiation, wind, etc.) to interpret **thermal comfort or heat stress**
conditions for humans or animals.

These base classes provide a consistent API to:
- enforce documentation of required inputs;
- allow interchangeable use of different indexes;
- support extensibility in scientific and operational workflows.
"""

from abc import ABC, abstractmethod


class ComfortIndex(ABC):
    """
    Abstract base class for thermal and bioclimatic comfort indexes.

    This class defines the minimal interface that all comfort or
    heat-stress indexes must implement. Each index is assumed to
    represent a *scalar diagnostic quantity* derived from one or
    more environmental or physiological variables.

    Attributes
    ----------
    name : str
        Human-readable name of the index (e.g., ``"THI"``, ``"HLI"``,
        ``"UTCI"``). Subclasses should override this attribute.

    Notes
    -----
    - This class does **not** impose any specific set of inputs.
      Each index formulation is free to define its own required
      variables (e.g., air temperature, relative humidity, wind speed).
    - Implementations should clearly document:
        * required keyword arguments,
        * units of each variable,
        * valid ranges (if applicable),
        * scientific references.
    """

    #: Human-readable name of the index
    name: str

    @abstractmethod
    def compute(self, **kwargs):
        """
        Compute the thermal comfort or heat-stress index.

        This abstract method must be implemented by all subclasses.
        The method signature uses keyword arguments to allow flexible
        and explicit specification of required inputs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments required to compute the index.
            The exact set of parameters depends on the specific
            index implementation.

        Returns
        -------
        float
            Computed value of the comfort or heat-stress index.

        Raises
        ------
        KeyError
            If a required input variable is missing.
        ValueError
            If input values are outside acceptable physical ranges.

        Notes
        -----
        Implementations should:
        - explicitly validate inputs;
        - document expected units (e.g., °C, %, m s⁻¹);
        - remain side-effect free (pure computation).

        Examples
        --------
        A minimal example of a concrete implementation::

            class THI(ComfortIndex):
                name = "Temperature-Humidity Index"

                def compute(self, T, RH):
                    # T  : air temperature [°C]
                    # RH : relative humidity [0–1]
                    return T - (0.55 - 0.55 * RH) * (T - 14.5)

        Usage example::

            thi = THI()
            value = thi.compute(T=30.0, RH=0.60)
            print(value)
        """
        raise NotImplementedError

