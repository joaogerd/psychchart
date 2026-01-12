def test_index_field_smoke(tmp_path):
    """
    Smoke test for rendering a psychrometric chart with an index field.

    This test verifies that a psychrometric chart can be successfully
    rendered when a **continuous index field** is defined in the
    YAML configuration.

    The purpose of this test is to ensure that:
    - the ``index_fields`` section is correctly parsed
    - an :class:`IndexField` object is instantiated
    - index field computation completes without errors
    - the rendering pipeline supports background index fields

    This is a *smoke test*, not a scientific or visual validation.
    It does NOT:
    - verify correctness of index values
    - check color scaling or colormap behavior
    - assert the presence or correctness of the colorbar
    - inspect the generated figure output

    If this test passes, it indicates that the integration between:
    - YAML loader
    - IndexField configuration
    - index computation pipeline
    - PsychChart rendering logic

    is operational at a basic execution level.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory provided by pytest, used to create
        an isolated YAML configuration file for the test.

    Notes
    -----
    - The test uses the ``ITU`` index as a minimal reference case.
    - A colormap is explicitly specified to exercise that code path.
    - No output file is written; rendering occurs in memory only.
    - This test is suitable for continuous integration environments.
    """

    # --------------------------------------------------------------
    # Local imports to keep the test explicit and self-contained
    # --------------------------------------------------------------
    from psychchart import load_chart_config, PsychChart

    # --------------------------------------------------------------
    # Minimal YAML configuration including an index field definition
    # --------------------------------------------------------------
    yaml = """
chart:
  t_min: 20
  t_max: 40

index_fields:
  - index: ITU
    cmap: inferno
"""

    # --------------------------------------------------------------
    # Write YAML configuration to a temporary file
    # --------------------------------------------------------------
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(yaml)

    # --------------------------------------------------------------
    # Load configuration into Python objects
    # --------------------------------------------------------------
    data = load_chart_config(cfg)

    # --------------------------------------------------------------
    # Instantiate and render the psychrometric chart
    # --------------------------------------------------------------
    chart = PsychChart(**data)
    chart.draw()

