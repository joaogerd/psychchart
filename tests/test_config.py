from psychchart.config import AppConfig, IsoSet, Point, Zone, IndexConfig
from psychchart.config.utils import normalize_rh


def test_normalize_rh_percent():
    assert normalize_rh(65) == 0.65


def test_isoset_normalizes_relative_humidity():
    iso = IsoSet(name="relative_humidity", values=[30, 50, 70])
    assert iso.values == [0.3, 0.5, 0.7]


def test_point_normalizes_rh():
    pt = Point(t=25, rh=60)
    assert pt.rh == 0.6


def test_zone_normalizes_rh_range():
    zone = Zone(name="comfort", t_range=(20, 30), rh_range=(40, 70))
    assert zone.rh_range == (0.4, 0.7)


def test_indexconfig_accepts_legacy_name():
    idx = IndexConfig(name="ITU")
    assert idx.index == "ITU"


def test_appconfig_accepts_legacy_isolines_list():
    raw = {
        "chart": {
            "t_min": 0,
            "t_max": 50,
            "pressure": 101325,
            "xlabel": "T",
            "ylabel": "W",
            "output": "out.png",
            "dpi": 100,
        },
        "isolines": [
            {"name": "relative_humidity", "values": [30, 50, 70]}
        ],
    }
    cfg = AppConfig.model_validate(raw)
    assert "relative_humidity" in cfg.isolines
    assert cfg.isolines["relative_humidity"].values == [0.3, 0.5, 0.7]


def test_appconfig_accepts_legacy_index_name():
    raw = {
        "chart": {
            "t_min": 0,
            "t_max": 50,
            "pressure": 101325,
            "xlabel": "T",
            "ylabel": "W",
            "output": "out.png",
            "dpi": 100,
        },
        "indexes": [
            {"name": "ITU"}
        ],
    }
    cfg = AppConfig.model_validate(raw)
    assert cfg.indexes[0].index == "ITU"
