from abc import ABC, abstractmethod
from typing import Union
import numpy as np

# ----------------------------------------------------------------------
# Public type alias for scalar or vector inputs
# ----------------------------------------------------------------------
ArrayLike = Union[float, np.ndarray]


class ComfortIndex(ABC):
    """
    Abstract base class for thermal and bioclimatic comfort indexes.

    This class defines the **minimal and canonical interface**
    that all thermal comfort or heat-stress indexes must follow
    in the psychchart ecosystem.

    Conceptual model
    ----------------
    A comfort index is treated as a **pure diagnostic function**
    that maps environmental conditions to a scalar indicator of
    thermal comfort or heat stress.

    Design contract
    ---------------
    All subclasses MUST obey the following rules:

    1. Stateless
       - Index classes must not store internal state.
       - All required information must be passed explicitly
         during evaluation.

    2. Canonical input space
       - Evaluation is always performed in:
         - dry-bulb temperature (T, °C)
         - relative humidity (RH, fraction 0–1)

    3. Explicit parameters
       - Any additional environmental or physiological variables
         (e.g., wind speed, solar radiation) must be passed
         explicitly via ``**params``.

    4. Vectorized behavior
       - Implementations must support both scalar inputs and
         NumPy arrays transparently.

    This strict contract ensures that:
    - indexes are interchangeable,
    - plotting logic remains generic,
    - scientific assumptions are explicit,
    - and future extensions (e.g., new indexes) remain safe.

    Responsibilities
    ----------------
    - Define the evaluation interface for comfort indexes
    - Enforce consistency across different index implementations

    Non-responsibilities
    --------------------
    - Psychrometric conversions (T–RH → W, h, etc.)
    - Input validation or unit conversion
    - Plotting or visualization
    - Configuration or parameter storage

    Attributes
    ----------
    name : str
        Human-readable identifier of the index
        (e.g., ``"ITU"``, ``"THI"``, ``"HLI"``, ``"UTCI"``).

        This attribute is used for:
        - labeling plots,
        - legend entries,
        - dispatching logic.

    Notes
    -----
    - Subclasses should normally implement ``evaluate`` as a
      ``@staticmethod`` to reinforce statelessness.
    - This base class intentionally avoids enforcing a specific
      unit system beyond what is documented.
    """

    #: Human-readable name of the index (must be overridden by subclasses)
    name: str

    # ------------------------------------------------------------------
    # Canonical evaluation interface
    # ------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def evaluate(
        T: ArrayLike,
        RH: ArrayLike,
        **params,
    ) -> ArrayLike:
        """
        Evaluate the comfort index.

        This method defines the **canonical computation interface**
        shared by all comfort and bioclimatic indexes.

        Implementations must accept both scalars and NumPy arrays
        and return values with matching shape.

        Parameters
        ----------
        T : float or numpy.ndarray
            Dry-bulb air temperature [°C].

        RH : float or numpy.ndarray
            Relative humidity as a fraction in the range [0, 1].

        **params : dict
            Index-specific auxiliary parameters.

            Examples include:
            - ``WS`` : wind speed [m s⁻¹]
            - ``SR`` : solar radiation [W m⁻²]
            - ``MR`` : metabolic rate
            - ``CLO`` : clothing insulation

            The meaning and units of these parameters are defined
            by each concrete index implementation.

        Returns
        -------
        float or numpy.ndarray
            Computed index value(s), with shape compatible
            with the input ``T`` and ``RH``.

        Raises
        ------
        NotImplementedError
            If the subclass does not implement this method.

        Examples
        --------
        Scalar usage:

        >>> ITUIndex.evaluate(T=30.0, RH=0.65)
        78.4

        Vectorized usage:

        >>> T = np.array([25.0, 30.0, 35.0])
        >>> RH = np.array([0.5, 0.6, 0.7])
        >>> ITUIndex.evaluate(T, RH)
        array([72.1, 78.4, 84.9])

        With auxiliary parameters:

        >>> HLIIndex.evaluate(
        ...     T, RH,
        ...     WS=2.0,
        ...     SR=600.0
        ... )
        """
        raise NotImplementedError

