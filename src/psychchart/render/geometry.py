from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional
import numpy as np


# -----------------------------------------------------------------------------
# Basic geometric primitive
# -----------------------------------------------------------------------------
Point2D = Tuple[float, float]  # (x, y)


# -----------------------------------------------------------------------------
# Style container
# -----------------------------------------------------------------------------
@dataclass
class Style:
    """
    Renderer-agnostic styling configuration.

    This class stores visual properties that can be interpreted
    by different rendering backends (e.g., Matplotlib, SVG, WebGL).

    It does NOT perform rendering itself.

    Parameters
    ----------
    stroke : str or None, optional
        Line color. Example: "black", "#FF0000".

    stroke_width : float or None, optional
        Line width in rendering units.

    stroke_dasharray : str or None, optional
        Dash pattern definition (e.g., "5,2" for dashed lines).
        Interpretation depends on backend.

    fill : str or None, optional
        Fill color for closed shapes (e.g., polygons).

    opacity : float or None, optional
        Opacity value between 0 and 1.

    zorder : int or None, optional
        Rendering order priority.

    extra : dict, optional
        Arbitrary backend-specific styling parameters.

    Notes
    -----
    • Designed to be backend-independent.
    • Backends may ignore unsupported attributes.
    • The `extra` dictionary allows future extensibility.

    Examples
    --------
    >>> style = Style(
    ...     stroke="black",
    ...     stroke_width=1.5,
    ...     fill="#FFDDDD",
    ...     opacity=0.8,
    ...     zorder=10,
    ... )

    >>> style.extra["marker"] = "o"
    """

    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    stroke_dasharray: Optional[str] = None
    fill: Optional[str] = None
    opacity: Optional[float] = None
    zorder: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Path layer
# -----------------------------------------------------------------------------
@dataclass
class PathLayer:
    """
    Collection of one or more polylines.

    Each path is a sequence of (x, y) coordinates representing
    a continuous line segment.

    Parameters
    ----------
    name : str
        Layer identifier.

    paths : list of list of (float, float)
        Each inner list represents a polyline.

    style : Style, optional
        Styling configuration.

    visible : bool, optional
        Whether this layer should be rendered.

    meta : dict, optional
        Arbitrary metadata associated with the layer.

    Notes
    -----
    • Suitable for isolines, axes, gridlines, boundaries.
    • Paths are assumed ordered.
    • No automatic geometry validation is performed.

    Examples
    --------
    >>> path = [(0, 0), (1, 1), (2, 0)]
    >>> layer = PathLayer(
    ...     name="ExampleLine",
    ...     paths=[path],
    ... )
    """

    name: str
    paths: List[List[Point2D]]
    style: Style = field(default_factory=Style)
    visible: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Polygon layer
# -----------------------------------------------------------------------------
@dataclass
class PolygonLayer:
    """
    Collection of filled polygonal regions.

    Parameters
    ----------
    name : str
        Layer identifier.

    polygons : list of list of (float, float)
        Each inner list represents a closed polygon.

    style : Style, optional
        Styling configuration.

    visible : bool, optional
        Whether this layer should be rendered.

    meta : dict, optional
        Arbitrary metadata associated with the layer.

    Notes
    -----
    • Polygons are assumed to be closed (first and last point may
      or may not be repeated; renderer may close automatically).
    • Suitable for comfort zones, threshold areas, domain masks.

    Examples
    --------
    >>> poly = [(0, 0), (2, 0), (2, 2), (0, 2)]
    >>> layer = PolygonLayer(
    ...     name="ComfortZone",
    ...     polygons=[poly],
    ... )
    """

    name: str
    polygons: List[List[Point2D]]
    style: Style = field(default_factory=Style)
    visible: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Points layer
# -----------------------------------------------------------------------------
@dataclass
class PointsLayer:
    """
    Collection of discrete 2D points.

    Parameters
    ----------
    name : str
        Layer identifier.

    points : list of (float, float)
        Coordinates of individual points.

    labels : list of str or None, optional
        Optional label for each point.
        Must match length of `points` if provided.

    style : Style, optional
        Styling configuration.

    visible : bool, optional
        Whether this layer should be rendered.

    meta : dict, optional
        Arbitrary metadata associated with the layer.

    Notes
    -----
    • Suitable for observational data points.
    • Label handling depends on backend.
    • No automatic length validation for labels.

    Examples
    --------
    >>> layer = PointsLayer(
    ...     name="Stations",
    ...     points=[(25.0, 0.012), (30.0, 0.018)],
    ...     labels=["A940", "A001"],
    ... )
    """

    name: str
    points: List[Point2D]
    labels: Optional[List[str]] = None
    style: Style = field(default_factory=Style)
    visible: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Scalar field layer
# -----------------------------------------------------------------------------
@dataclass
class ScalarFieldLayer:
    """
    Scalar field defined over a structured 2D grid.

    This layer represents continuous scalar diagnostics
    evaluated over the psychrometric domain.

    Typical use cases:
        - ICF continuous field
        - THI / HLI domain evaluation
        - Density or probability fields
        - Heatmaps over T-W space

    Parameters
    ----------
    name : str
        Field identifier.

    X : np.ndarray
        2D array of X-coordinates (e.g., temperature).

    Y : np.ndarray
        2D array of Y-coordinates (e.g., humidity ratio).

    Z : np.ndarray
        2D array of scalar values evaluated at (X, Y).

    levels : int or None, optional
        Number of contour levels (if using contour rendering).

    cmap : str, optional
        Colormap name.

    alpha : float, optional
        Transparency level between 0 and 1.

    Notes
    -----
    • Requires X.shape == Y.shape == Z.shape.
    • Rendering backend decides between contourf, pcolormesh, etc.
    • This class does NOT compute scalar values.

    Examples
    --------
    >>> T = np.linspace(10, 40, 100)
    >>> W = np.linspace(0.002, 0.025, 100)
    >>> X, Y = np.meshgrid(T, W)
    >>> Z = 0.5 * X + 100 * Y

    >>> field = ScalarFieldLayer(
    ...     name="ExampleField",
    ...     X=X,
    ...     Y=Y,
    ...     Z=Z,
    ...     levels=20,
    ...     cmap="viridis",
    ...     alpha=0.9,
    ... )
    """

    name: str
    X: np.ndarray
    Y: np.ndarray
    Z: np.ndarray
    levels: Optional[int] = None
    cmap: str = "viridis"
    alpha: float = 1.0

