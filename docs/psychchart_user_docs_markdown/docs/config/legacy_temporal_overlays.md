# `temporal_overlays` — formato legado para trajetórias temporais

## O que é

É o formato legado para trajetórias temporais. Ainda é aceito, mas pode ser convertido automaticamente para `data_layers`.

## Para que serve

Serve para descrever uma sequência temporal com caminho, pontos e anotações.

## Parâmetros disponíveis

### Confirmado no código

- `type`
- `data`
- `t_col`
- `rh_col`
- `time_col`
- `cta_col`
- `annotate_every`
- `annotation_template`
- `show_path`
- `path_color`
- `path_alpha`
- `path_linewidth`
- `path_zorder`
- `point_size`
- `point_edgecolor`
- `point_edgewidth`
- `point_zorder`
- `annotation_dx`
- `annotation_dy`
- `annotation_fontsize`
- `annotation_fontweight`
- `annotation_color`
- `annotation_zorder`
- `show_legend`
- `legend_loc`

## Valores aceitos

- colunas e identificadores: texto.
- estilos visuais: texto ou número conforme o campo.
- `annotate_every`: inteiro opcional.
- `show_path`, `show_legend`: booleano.

## Exemplo de uso

```yaml
temporal_overlays:
  - type: CTA
    data: data/trajectory.csv
    t_col: temperature
    rh_col: relative_humidity
    time_col: hour
    cta_col: cta
    annotate_every: 3
    annotation_template: "{time}h\n(CTA:{value:.0f})"
    show_path: true
    path_color: blue
    path_alpha: 0.6
    path_linewidth: 1.2
    point_size: 42.0
    point_edgecolor: black
    point_edgewidth: 0.8
```

## Observações importantes

### Confirmado no código

- Quando `data_layers` não é fornecido, `temporal_overlays` é convertido para `data_layers`.
- Na conversão automática:
  - o arquivo vira um `data_layer`
  - `time_col` entra em `temporal`
  - `cta_col` vira um campo `direct_column` chamado `CTA`
  - `show_path` controla se o bloco `path` será criado
  - sempre é criado um `scatter` com `value: CTA`
  - quando `annotate_every` não é `None`, é criado um `annotate`
- O `format` é fixado como `csv` na conversão automática.

### Confirmado no código, mas com ressalva

- O renderizador canônico de anotações trabalha com placeholders `time` e `value`.
- A conversão automática para `data_layers` usa `value_field: CTA`.

### Não foi possível validar

- O efeito real de `show_legend` e `legend_loc`: esses campos existem no modelo legado, mas não aparecem no conversor nem nos renderizadores enviados.
- O efeito real de `type`: ele existe no modelo legado, mas não é usado no trecho de conversão enviado.

## Erros comuns

- Usar `annotation_template` com `{cta}` em vez de `{value}` quando a trajetória for convertida para o formato canônico de anotações.
- Esperar que `format` seja detectado automaticamente: na conversão enviada, ele é fixado em `csv`.
