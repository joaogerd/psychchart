from dataclasses import dataclass
import numpy as np


@dataclass
class DensityFieldData:
    """
    Computed data container for a psychrometric density field.

    A ``DensityFieldData`` instance stores the **numerical result**
    of a density or frequency computation over the psychrometric
    domain, typically derived from observational datasets.

    This class is a **pure data container**:
    it contains **no logic**, **no validation**, and
    **no rendering code**.

    It exists solely to package the outputs of a density computation
    (e.g., a 2D histogram or probability density field) in a
    structured, explicit, and reusable form.

    Responsibilities
    ----------------
    - Store bin edges along the dry-bulb temperature axis
    - Store bin edges along the humidity-ratio axis
    - Store the computed density or frequency values

    Non-responsibilities
    --------------------
    - Computing histograms or density fields
    - Normalizing or rescaling values
    - Performing psychrometric conversions
    - Plotting or visualization
    - Applying physical masking or saturation clipping

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
        containing the computed density or frequency values.

        The physical meaning of ``values`` depends on how
        the density field was computed:
        - raw counts per bin
        - normalized probability density
        - relative frequency

    Notes
    -----
    - This class is typically produced by a function such as
      ``to_density_field`` or ``compute_density_field`` and
      consumed by a rendering function such as
      ``draw_density_field``.
    - No assumptions are made about normalization or scaling;
      this must be documented and handled externally.
    - The binning domain is assumed to be consistent with the
      psychrometric chart configuration (temperature limits,
      pressure, etc.).

    Design considerations
    ---------------------
    - Separating *data* from *configuration* avoids ambiguity
      and makes the visualization pipeline explicit.
    - Using bin edges (instead of bin centers) ensures full
      compatibility with ``matplotlib.pcolormesh`` and
      ``matplotlib.imshow``.
    - This container can be serialized, cached, or reused
      safely across rendering calls.

    Examples
    --------
    Typical creation after computing a 2D histogram:

    >>> T_edges, W_edges, H = compute_density(obs, cfg)
    >>> data = DensityFieldData(
    ...     T_edges=T_edges,
    ...     W_edges=W_edges,
    ...     values=H,
    ... )

    Rendering the density field:

    >>> draw_density_field(ax, data, density_cfg)

    Accessing raw density values:

    >>> H = data.values
    >>> H.max(), H.mean()
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
    # Density or frequency values
    # Shape: (n_W, n_T)
    # ------------------------------------------------------------------
    values: np.ndarray

