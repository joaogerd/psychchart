from dataclasses import dataclass
import numpy as np


@dataclass
class ScalarFieldData:
    """
    Computed data container for a psychrometric scalar field.

    A ``ScalarFieldData`` instance stores the **numerical result**
    of a scalar-field computation over the psychrometric domain.

    A scalar field represents any physically or functionally
    meaningful quantity evaluated over a discretized
    temperature–humidity space, such as:

    - Functional Comfort Index (ICF)
    - Thermal stress indicators
    - Model-derived scalar diagnostics
    - Any custom index defined over (T, W)

    This class is a **pure data container**:
    it contains **no logic**, **no validation**, and
    **no rendering code**.

    It exists solely to package the outputs of a scalar-field
    computation in a structured, explicit, and reusable form.

    Responsibilities
    ----------------
    - Store bin edges along the dry-bulb temperature axis
    - Store bin edges along the humidity-ratio axis
    - Store the computed scalar values
    - Store the semantic name of the scalar field

    Non-responsibilities
    --------------------
    - Computing the scalar field
    - Normalizing or rescaling values
    - Performing psychrometric transformations
    - Validating physical plausibility
    - Plotting or visualization
    - Applying masking or clipping rules

    Parameters
    ----------
    T_edges : numpy.ndarray
        One-dimensional array of bin edges along the
        dry-bulb temperature axis (°C).

        Length must be ``n_T + 1``, where ``n_T`` is the
        number of bins along the temperature dimension.

    W_edges : numpy.ndarray
        One-dimensional array of bin edges along the
        humidity-ratio axis (kg_vapor / kg_dry_air).

        Length must be ``n_W + 1``, where ``n_W`` is the
        number of bins along the humidity-ratio dimension.

    values : numpy.ndarray
        Two-dimensional array of shape ``(n_W, n_T)``
        containing the computed scalar values.

        The physical meaning of ``values`` depends entirely
        on the generating function (e.g., ICF, HLI, custom index).

        This container makes **no assumptions** about:
        - value ranges
        - normalization
        - monotonicity
        - boundedness

    name : str
        Human-readable identifier of the scalar field.

        Examples:
        - "ICF"
        - "HLI"
        - "CustomStressIndex"

        This field is informational and intended for:
        - labeling colorbars
        - legends
        - metadata export
        - debugging

    Notes
    -----
    - This class is typically produced by functions such as
      ``compute_scalar_field`` or ``to_scalar_field``.
    - It is typically consumed by rendering functions such as
      ``draw_scalar_field``.
    - The binning domain must be consistent with the
      psychrometric chart configuration (temperature limits,
      pressure assumptions, etc.).
    - No implicit physical interpretation is embedded here;
      interpretation belongs to the index definition layer.

    Design considerations
    ---------------------
    - Separating scalar-field data from rendering logic
      enforces architectural clarity.
    - Using bin edges ensures compatibility with
      ``matplotlib.pcolormesh`` and similar APIs.
    - The explicit ``name`` attribute prevents ambiguity
      when multiple scalar fields are computed in the same
      analysis pipeline.
    - This container can be safely serialized, cached,
      or reused across rendering contexts.

    Examples
    --------
    Typical creation after computing an index field:

    >>> T_edges, W_edges, Z = compute_icf_field(obs, cfg)
    >>> data = ScalarFieldData(
    ...     T_edges=T_edges,
    ...     W_edges=W_edges,
    ...     values=Z,
    ...     name="ICF",
    ... )

    Rendering the scalar field:

    >>> draw_scalar_field(ax, data, field_cfg)

    Accessing raw values:

    >>> data.name
    'ICF'
    >>> data.values.min(), data.values.max()
    """

    # ------------------------------------------------------------------
    # Bin edges along dry-bulb temperature axis (°C)
    # ------------------------------------------------------------------
    T_edges: np.ndarray

    # ------------------------------------------------------------------
    # Bin edges along humidity-ratio axis (kg_vapor / kg_dry_air)
    # ------------------------------------------------------------------
    W_edges: np.ndarray

    # ------------------------------------------------------------------
    # Scalar field values
    # Shape: (n_W, n_T)
    # ------------------------------------------------------------------
    values: np.ndarray

    # ------------------------------------------------------------------
    # Human-readable scalar field name (e.g., "ICF")
    # ------------------------------------------------------------------
    name: str

