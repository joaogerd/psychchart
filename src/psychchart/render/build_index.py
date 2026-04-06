from dataclasses import dataclass
import numpy as np
from typing import Dict, Any


@dataclass
class ScalarFieldLayer:
    """
    Container for a 2D scalar field defined over psychrometric coordinates.

    This class represents a scalar field Z evaluated over a structured
    grid (X, Y), typically used for rendering isolines, filled contours,
    or heatmaps on a psychrometric diagram.

    The field is assumed to be defined over a rectangular meshgrid
    compatible with Matplotlib contouring functions.

    Parameters
    ----------
    name : str
        Identifier of the scalar field (e.g., "ICF", "THI", "HLI").
        This name is used for labeling, legend entries, and colorbar titles.

    X : np.ndarray
        2D array of X-coordinates (typically dry-bulb temperature in °C).

        Must have the same shape as `Y` and `Z`.

    Y : np.ndarray
        2D array of Y-coordinates (typically humidity ratio W in kg/kg).

        Must have the same shape as `X` and `Z`.

    Z : np.ndarray
        2D array containing scalar field values evaluated at each
        (X, Y) grid point.

        This array represents the index values (e.g., ICF intensity)
        and is typically used for contour or pcolormesh rendering.

    meta : dict
        Arbitrary metadata dictionary associated with the scalar field.

        This may contain:
        - units
        - thresholds
        - colormap configuration
        - source information
        - normalization details
        - rendering hints

    Notes
    -----
    • This class does NOT compute the scalar field.
      It only stores already-evaluated data.

    • Shape consistency is required:
      X.shape == Y.shape == Z.shape

    • This object is typically produced by:
        - DomainIndex evaluations
        - ScalarFieldData generation
        - FunctionalObservations.to_scalar_field()

    • It is designed to be consumed by rendering layers.

    Examples
    --------
    Example 1 — Creating a scalar field from meshgrid:

    >>> import numpy as np
    >>> T = np.linspace(10, 40, 50)
    >>> W = np.linspace(0.002, 0.025, 50)
    >>> X, Y = np.meshgrid(T, W)
    >>> Z = 0.8 * X + 200 * Y  # artificial index
    >>>
    >>> layer = ScalarFieldLayer(
    ...     name="ExampleIndex",
    ...     X=X,
    ...     Y=Y,
    ...     Z=Z,
    ...     meta={"units": "dimensionless"}
    ... )

    Example 2 — Using with matplotlib:

    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> cs = ax.contourf(layer.X, layer.Y, layer.Z, levels=20)
    >>> plt.colorbar(cs, ax=ax, label=layer.meta.get("units"))
    >>> plt.show()

    Example 3 — Validation check before rendering:

    >>> assert layer.X.shape == layer.Z.shape

    See Also
    --------
    ScalarFieldData :
        Utility class that builds scalar fields from observations.

    FunctionalObservations :
        Observation container capable of generating scalar fields.

    DomainIndex :
        Index evaluated over the psychrometric domain.
    """

    name: str
    X: np.ndarray
    Y: np.ndarray
    Z: np.ndarray
    meta: Dict[str, Any]

