import textwrap
import tempfile
from pathlib import Path

from psychchart.loader import load_chart_config
from psychchart.config import ChartConfig, IsoSet, Zone, Point


def test_loader_basic_yaml():
    yaml_content = textwrap.dedent("""
    chart:
      t_min: 0
      t_max: 40
      pressure: 101325

    isolines:
      relative_humidity:
        values: [30, 60, 90]   # em %

    zones:
      - name: conforto
        t_range: [20, 26]
        rh_range: [40, 60]

    points:
      - label: A
        t: 25
        rh: 50
    """)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.yaml"
        path.write_text(yaml_content, encoding="utf-8")

        cfg, isolines, zones, points = load_chart_config(path)

    # ChartConfig
    assert isinstance(cfg, ChartConfig)
    assert cfg.t_min == 0
    assert cfg.t_max == 40

    # Isolines
    assert "relative_humidity" in isolines
    iso = isolines["relative_humidity"]
    assert isinstance(iso, IsoSet)
    assert iso.values == [0.3, 0.6, 0.9]  # normalizado

    # Zones
    assert len(zones) == 1
    z = zones[0]
    assert isinstance(z, Zone)
    assert z.rh_range == [0.4, 0.6]

    # Points
    assert len(points) == 1
    p = points[0]
    assert isinstance(p, Point)
    assert p.rh == 0.5

