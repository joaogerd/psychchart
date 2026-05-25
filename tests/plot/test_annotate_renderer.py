from types import SimpleNamespace

import pandas as pd

from psychchart.plot.data_renderers.annotate import _build_annotation_context


def test_annotation_context_exposes_named_dataframe_columns():
    row = pd.Series(
        {
            "data_hora": "2025-11-08 15:00:00",
            "hora": 15,
            "cta": 181.7,
            "cta_classe": "acumulo elevado",
        }
    )
    cfg = SimpleNamespace(time_field="data_hora", value_field="cta")

    context = _build_annotation_context(row, cfg)

    assert context["hora"] == 15
    assert context["cta"] == 181.7
    assert context["cta_classe"] == "acumulo elevado"
    assert context["time"] == context["data_hora"]
    assert context["value"] == 181.7


def test_annotation_template_supports_datetime_and_numeric_formatting():
    row = pd.Series(
        {
            "data_hora": "2025-11-08 15:00:00",
            "hora": 15,
            "cta": 181.7,
        }
    )
    cfg = SimpleNamespace(time_field="data_hora", value_field="cta")

    context = _build_annotation_context(row, cfg)
    label = "{data_hora:%H:%M}\nCTA:{cta:.0f}\nH:{hora:02d}".format(**context)

    assert label == "15:00\nCTA:182\nH:15"


def test_annotation_template_keeps_legacy_time_and_value_placeholders():
    row = pd.Series(
        {
            "data_hora": "2025-11-08 10:00:00",
            "cta": 95.4,
        }
    )
    cfg = SimpleNamespace(time_field="data_hora", value_field="cta")

    context = _build_annotation_context(row, cfg)
    label = "{time:%Y-%m-%d %Hh}\n(CTA:{value:.0f})".format(**context)

    assert label == "2025-11-08 10h\n(CTA:95)"
