psychChart examples
===================

Run examples from the repository root so relative data paths resolve correctly.

The examples listed here are part of the validated release smoke-test set.
Files under examples_old/ are historical references and are not part of the
validated set.

Core examples
-------------

psychchart examples/example_points.yaml
psychchart examples/example_scatter.yaml
psychchart examples/example_density.yaml
psychchart examples/example_scalar_field.yaml
psychchart examples/example_path.yaml
psychchart examples/example_annotate.yaml
psychchart examples/example_path_scatter_annotate.yaml
psychchart examples/example_mixed.yaml

Path and trajectory examples
----------------------------

psychchart examples/path_basic.yaml
psychchart examples/path_colored_cta.yaml
psychchart examples/path_colored_itu.yaml
psychchart examples/path_dashed_order_by.yaml
psychchart examples/path_order_by.yaml
psychchart examples/path_points.yaml
psychchart examples/path_scatter_annotate_cta.yaml
psychchart examples/thermal_trajectory_classified.yaml

Bioclimatic and index examples
------------------------------

psychchart examples/bovinos_racas.yaml
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
psychchart examples/itu_field_labels.yaml
psychchart examples/index_zone_itu_labeled.yaml

Operational decision and intervention examples
----------------------------------------------

psychchart examples/operational_overlay_minimal.yaml
psychchart examples/intervention_zones_minimal.yaml

Notes
-----

- Files under examples_old/ are kept as historical references and are not part of the validated example smoke-test set.
- CSV files under examples/data/ are intentionally small and deterministic so examples can run in CI.
- Relative paths are written for execution from the repository root.
