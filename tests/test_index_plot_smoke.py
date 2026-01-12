def test_plot_with_index_smoke(tmp_path):
    """
    Smoke test for rendering a psychrometric chart with index configuration.

    This test verifies that a psychrometric chart can be successfully
    constructed and rendered when an **index configuration** is provided
    via a YAML file.

    The purpose of this test is strictly to ensure that:
    - the YAML configuration is correctly parsed
    - index-related configuration does not raise runtime errors
    - the rendering pipeline completes without exceptions

    This is a *smoke test*, not a numerical or visual validation.
    It does NOT:
    - verify correctness of index computations
    - check contour placement or labeling
    - inspect the rendered figure content
    - assert graphical output properties

    If this test passes, it indicates that the integration between:
    - YAML loader
    - IndexConfig parsing
    - PsychChart orchestration
    - index drawing routines

    is functionally intact at a basic execution level.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory provided by pytest, used to create
        an isolated YAML configuration file for the test.

    Notes
    -----
    - The test relies on the presence of an index named ``"ITU"``.
    - The index is rendered in ``isolines`` mode with two contour levels.
    - No figure is saved to disk; rendering is performed in-memory.

    This test is intentionally lightweight and fast, making it suitable
    for continuous integration environments.
    """

    # --------------------------------------------------------------
    # Import here to keep the test self-contained and explicit
    # --------------------------------------------------------------
    from psychchart import load_chart_config, PsychChart

    # --------------------------------------------------------------
    # Minimal YAML configuration including an index definition
    # --------------------------------------------------------------
    yaml = """
chart:
  t_min: 20
  t_max: 40

indexes:
  - name: ITU
    mode: isolines
    levels: [72, 78]
"""

    # --------------------------------------------------------------
    # Write configuration to a temporary file
    # --------------------------------------------------------------
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(yaml)

    # --------------------------------------------------------------
    # Load configuration into Python structures
    # --------------------------------------------------------------
    data = load_chart_config(cfg_file)

    # --------------------------------------------------------------
    # Instantiate and render the psychrometric chart
    # --------------------------------------------------------------
    chart = PsychChart(**data)
    chart.draw()

