# Annotation label templates

`annotate` render blocks can format labels from the full processed data-layer row.

This is useful for temporal overlays, where the label often needs more than the default `time` and `value` placeholders. For example, a CTA trajectory may need to show only the hour, the accumulated load, or a compact two-line label.

## Available placeholders

For each annotated point, the template context includes:

- `time`: value from `time_field`, when configured;
- `value`: value from `value_field`, when configured;
- every column available in the processed data layer, using the column name directly.

Because all dataframe columns are exposed, templates may use fields such as `data_hora`, `hora`, `cta`, `cta_classe`, `temperatura`, or any other column present in the input file.

Datetime-like strings are parsed before formatting, so Python datetime format codes can be used.

## Examples

Show only the hour from a datetime column:

```yaml
render:
  - type: annotate
    every: 3
    time_field: data_hora
    value_field: cta
    template: "{data_hora:%Hh}"
```

Show hour and rounded CTA:

```yaml
render:
  - type: annotate
    every: 3
    time_field: data_hora
    value_field: cta
    template: "{data_hora:%Hh}\nCTA:{cta:.0f}"
```

Keep the legacy placeholders:

```yaml
render:
  - type: annotate
    every: 3
    time_field: data_hora
    value_field: cta
    template: "{time:%Y-%m-%d %Hh}\n(CTA:{value:.0f})"
```

## Notes

The template uses Python's standard `str.format` syntax. This means numeric formatting such as `{cta:.0f}` and datetime formatting such as `{data_hora:%H:%M}` are supported when the values are compatible.
