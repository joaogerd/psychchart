"""
Command-line interface (CLI) for psychchart.

This module provides a thin command-line wrapper that orchestrates
the full workflow of the psychchart package:

- reading a YAML configuration file
- loading and normalizing configuration objects
- generating a psychrometric chart
- saving the resulting figure to disk

The CLI is intentionally minimal and delegates all core logic
to the loader and plotting modules.
"""

import sys
import argparse

from .plot import PsychChart
from .loader import load_chart_config


# =============================================================================
# Main entry point
# =============================================================================
def main() -> None:
    """
    Entry point for the psychchart command-line interface.

    This function performs the following steps:

    1. Parse command-line arguments
    2. Load and validate the YAML configuration file
    3. Instantiate the PsychChart object
    4. Render the psychrometric diagram
    5. Save the output figure to disk

    Any exception raised during the process is caught,
    reported to stderr, and results in a non-zero exit code.
    """
    parser = argparse.ArgumentParser(
        description="Generate a psychrometric chart from a YAML configuration file."
    )
    parser.add_argument(
        "config",
        metavar="CONFIG",
        type=str,
        help="Path to the YAML configuration file."
    )

    args = parser.parse_args()

    try:
        # -------------------------------------------------------------
        # Load configuration (returns a dictionary of objects)
        # -------------------------------------------------------------
        data = load_chart_config(args.config)

        cfg      = data["cfg"]
        isolines = data["isolines"]
        zones    = data["zones"]
        points   = data["points"]

        # -------------------------------------------------------------
        # Create and draw chart
        # -------------------------------------------------------------
        chart = PsychChart(
            cfg=cfg,
            isolines=isolines,
            zones=zones,
            points=points
        )

        ax = chart.draw()

        # -------------------------------------------------------------
        # Save output
        # -------------------------------------------------------------
        ax.figure.savefig(
            cfg.output,
            dpi=cfg.dpi,
            bbox_inches="tight"
        )

        print(f"[OK] Chart successfully saved to '{cfg.output}'")

    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


# =============================================================================
# Script execution hook
# =============================================================================
if __name__ == "__main__":
    main()


# =============================================================================
# Usage examples
# =============================================================================
#
# Example 1: Basic command-line usage
#
# $ python -m psychchart.cli config/chart.yml
#
#
# Example 2: Typical YAML configuration file
#
# chart:
#   t_min: 0
#   t_max: 40
#   pressure: 101325
#   output: psychchart.png
#   dpi: 150
#
# isos:
#   - name: relative_humidity
#     values: [30, 50, 70, 90]   # percent accepted
#     style: "--"
#
#   - name: enthalpy
#     values: [30, 40, 50]
#
# zones:
#   - name: Comfort zone
#     t_range: [18, 26]
#     rh_range: [40, 70]
#     facecolor: lightgreen
#
# points:
#   - label: Station A
#     t: 32
#     rh: 65
#
#
# Example 3: Typical console output
#
# [OK] Chart successfully saved to 'psychchart.png'
#

