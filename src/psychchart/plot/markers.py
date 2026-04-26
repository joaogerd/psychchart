"""
Custom Matplotlib markers.

This module provides reusable custom marker factories for Matplotlib plots.
"""

from __future__ import annotations

from matplotlib.path import Path


def make_corner_cross_marker(
    outer: float = 1.0,
    inner: float = 0.45,
    side_inner: float = 0.35,
    side_outer: float = 2.0,
) -> Path:
    """
    Create a custom Matplotlib marker composed of four corner brackets,
    two horizontal side lines, and one vertical central line.

    The returned object can be passed directly to the ``marker`` argument
    of Matplotlib functions such as ``Axes.scatter``.
    """
    _validate_marker_dimensions(
        outer=outer,
        inner=inner,
        side_inner=side_inner,
        side_outer=side_outer,
    )

    vertices = [
        (-outer, outer), (-inner, outer),
        (-outer, outer), (-outer, inner),
        (inner, outer), (outer, outer),
        (outer, outer), (outer, inner),
        (-outer, -outer), (-inner, -outer),
        (-outer, -outer), (-outer, -inner),
        (inner, -outer), (outer, -outer),
        (outer, -outer), (outer, -inner),
        (-side_outer, 0.0), (-side_inner, 0.0),
        (side_inner, 0.0), (side_outer, 0.0),
        (0.0, -side_outer), (0.0, -side_inner),
        (0.0, side_inner), (0.0, side_outer),
    ]

    codes = _build_line_segment_codes(segment_count=len(vertices) // 2)
    return Path(vertices, codes)


def resolve_marker(marker: str):
    """Resolve named custom markers while preserving Matplotlib built-ins."""
    if marker == "corner_cross":
        return make_corner_cross_marker()
    return marker


def _build_line_segment_codes(segment_count: int) -> list[int]:
    """Build Matplotlib Path codes for independent line segments."""
    if segment_count <= 0:
        raise ValueError("'segment_count' must be greater than zero.")

    codes: list[int] = []
    for _ in range(segment_count):
        codes.extend([Path.MOVETO, Path.LINETO])
    return codes


def _validate_marker_dimensions(
    *,
    outer: float,
    inner: float,
    side_inner: float,
    side_outer: float,
) -> None:
    """Validate marker dimensions."""
    if outer <= 0:
        raise ValueError("'outer' must be greater than zero.")
    if inner <= 0:
        raise ValueError("'inner' must be greater than zero.")
    if side_inner < 0:
        raise ValueError("'side_inner' must be greater than or equal to zero.")
    if side_outer <= 0:
        raise ValueError("'side_outer' must be greater than zero.")
    if inner >= outer:
        raise ValueError("'inner' must be smaller than 'outer'.")
    if side_inner >= side_outer:
        raise ValueError("'side_inner' must be smaller than 'side_outer'.")
