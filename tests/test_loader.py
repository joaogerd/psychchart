import textwrap
import tempfile
from pathlib import Path

from psychchart import load_chart_config


def test_loader_basic_yaml():
    yaml_content = textwrap.dedent("""
    profile: default_si

    chart:
      t_min: 0
      t_max: 40
      pressure: 101325

    isolines:
      relative_humidity:
        values: [0.30, 0.60, 0.90]

    zones:
      - name: conforto
        t_range: [20, 26]
        rh_range: [0.40, 0.60]

    points:
      - label: A
        t: 25
        rh: 0.50
    """)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.yaml"
        path.write_text(yaml_content, encoding="utf-8")

        data = load_chart_config(path)

    assert "cfg" in data
    assert "isolines" in data
    assert "zones" in data
    assert "points" in data
    assert data["cfg"].t_min == 0
    assert data["cfg"].t_max == 40
    assert "relative_humidity" in data["isolines"]
    assert len(data["zones"]) == 1
    assert len(data["points"]) == 1
