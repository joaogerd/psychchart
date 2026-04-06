from psychchart import load_chart_config, PsychChart


def test_plot_smoke(tmp_path):
    yaml = """
profile: default_si

chart:
  t_min: 0
  t_max: 40
"""

    cfg = tmp_path / "plot_smoke.yaml"
    cfg.write_text(yaml, encoding="utf-8")

    data = load_chart_config(cfg)
    chart = PsychChart(**data)
    ax = chart.draw()

    assert ax is not None
