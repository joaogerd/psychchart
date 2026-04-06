from dataclasses import dataclass
import numpy as np
from psychchart.data.observations import Observations
from psychchart.psychrometrics import Psychrometrics
from psychchart.data.scalar import ScalarFieldData

class FunctionalObservations(Observations):
    """
    Psychrometric observations extended with functional scalar fields.

    This class augments :class:`Observations` by associating one or more
    experimental or derived scalar variables with each psychrometric state
    (T, RH).

    Typical scalar fields include:
    - Functional Comfort Index (ICF)
    - Behavioral intensity metrics
    - Experimental physiological markers
    - Custom user-defined indices

    The class preserves the minimal and explicit design philosophy of
    ``Observations``:
    - no plotting logic,
    - no hidden computation,
    - no implicit transformations.

    Responsibilities
    ----------------
    - Store additional scalar arrays aligned with observations
    - Enforce structural consistency between scalar fields and T/RH
    - Provide conversion of scalar data into 2D scalar fields
      over psychrometric space

    Non-responsibilities
    --------------------
    - Computing scalar indices (e.g., ICF calculation)
    - Performing smoothing or interpolation
    - Rendering heatmaps
    - Validating physical meaning of scalar values
    - Applying clipping or masking rules

    Design considerations
    ---------------------
    - Scalar fields are strictly observation-aligned.
    - No implicit recomputation is performed.
    - Conversion to scalar field operates in (T, W) space
      to preserve thermodynamic geometry.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, cfg, **fields):
        """
        Initialize functional observations.

        Parameters
        ----------
        cfg : ObservationsConfig
            Declarative observation configuration.
        **fields : array-like
            Named scalar fields aligned with observations.

            Each key-value pair defines:
            - key   → field name (e.g., "ICF")
            - value → sequence of scalar values

            All scalar arrays must have the same length as T and RH.

        Raises
        ------
        ValueError
            If any scalar field does not match observation length.
        """
        super().__init__(cfg)

        # Convert all scalar fields to float NumPy arrays
        self.fields = {
            name: np.asarray(values, dtype=float)
            for name, values in fields.items()
        }

        # Structural validation: scalar length must match observations
        for name, values in self.fields.items():
            if len(values) != len(self.T):
                raise ValueError(
                    f"Field '{name}' must match observation length."
                )

    # ------------------------------------------------------------------
    # Scalar field projection
    # ------------------------------------------------------------------
    def to_scalar_field(self, field_name, bins=(30, 30)) -> ScalarFieldData:
        """
        Compute a scalar field over psychrometric space.

        This method projects an observation-aligned scalar variable
        (e.g., ICF) onto a 2D grid in (T, W) space.

        The scalar field is computed as the **mean value per bin**
        of the selected scalar variable.

        Parameters
        ----------
        field_name : str
            Name of the scalar field to project.
        bins : tuple[int, int], optional
            Number of bins along:
            - temperature axis
            - humidity-ratio axis

            Default: (30, 30)

        Returns
        -------
        ScalarFieldData
            Declarative container holding:
            - bin edges along T
            - bin edges along W
            - mean scalar value per bin

        Raises
        ------
        KeyError
            If the requested field does not exist.

        Notes
        -----
        - Projection is performed in (T, W) space, not (T, RH).
        - W is computed using psychrometric transformation.
        - The scalar value in each bin represents the arithmetic mean
          of values falling within that bin.
        - Empty bins are assigned NaN.
        - No normalization, smoothing, or clipping is applied.

        Design considerations
        ---------------------
        - This method performs numerical aggregation only.
        - No Matplotlib objects are created.
        - The transpose of the histogram is intentional and required
          for compatibility with ``matplotlib.pcolormesh``.
        - Using mean aggregation preserves interpretability of indices
          such as ICF.

        Examples
        --------
        Compute ICF scalar field:

        >>> obs = FunctionalObservations(cfg, ICF=icf_values)
        >>> field = obs.to_scalar_field("ICF", bins=(50, 50))

        Render scalar field:

        >>> draw_scalar_field(ax, field, scalar_cfg)

        Access raw values:

        >>> field.values.min(), field.values.max()
        """

        # --------------------------------------------------------------
        # Validate field existence
        # --------------------------------------------------------------
        if field_name not in self.fields:
            raise KeyError(f"Unknown field '{field_name}'")

        values = self.fields[field_name]

        # --------------------------------------------------------------
        # Convert RH → W using psychrometric formulation
        # --------------------------------------------------------------
        # W ensures thermodynamically consistent geometry
        W = Psychrometrics.humidity_ratio(self.T, self.RH)

        # --------------------------------------------------------------
        # Weighted histogram for scalar aggregation
        # --------------------------------------------------------------
        # H stores the sum of scalar values per bin
        H, T_edges, W_edges = np.histogram2d(
            self.T,
            W,
            bins=bins,
            weights=values
        )

        # counts stores number of observations per bin
        counts, _, _ = np.histogram2d(
            self.T,
            W,
            bins=bins
        )

        # --------------------------------------------------------------
        # Compute mean scalar value per bin
        # --------------------------------------------------------------
        with np.errstate(divide="ignore", invalid="ignore"):
            mean_field = H / counts
            mean_field[counts == 0] = np.nan

        # --------------------------------------------------------------
        # Package results
        # --------------------------------------------------------------
        return ScalarFieldData(
            T_edges=T_edges,
            W_edges=W_edges,
            values=mean_field.T,  # transpose for correct axis orientation
            name=field_name,
        )

