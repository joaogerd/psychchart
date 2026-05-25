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
    time_col: data_hora
    cta_col: cta
    annotate_every: 3
    annotation_template: "{data_hora:%Hh}\nCTA:{cta:.0f}"
    show_path: true
    path_color: blue
    path_alpha: 0.6
    path_linewidth: 1.2
    point_size: 42.0
    point_edgecolor: black
    point_edgewidth: 0.8
```

## Formatação dos rótulos

O campo `annotation_template` usa a sintaxe padrão de `str.format` do Python.

Na renderização canônica, o contexto do template contém:

- `time`: valor da coluna definida por `time_col`;
- `value`: valor do campo acumulado convertido para `CTA`;
- todas as colunas do dataframe processado, acessíveis pelo próprio nome.

Isso permite rótulos compactos, por exemplo:

```yaml
annotation_template: "{data_hora:%Hh}"
```

ou rótulos com CTA arredondada:

```yaml
annotation_template: "{data_hora:%Hh}\nCTA:{cta:.0f}"
```

Também continua válido usar os nomes legados:

```yaml
annotation_template: "{time:%Y-%m-%d %Hh}\n(CTA:{value:.0f})"
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
- O renderizador de anotações expõe `time`, `value` e todas as colunas do dataframe processado ao `annotation_template`.

### Confirmado no código, mas com ressalva

- `value` aponta para o campo canônico `CTA` criado durante a conversão.
- A coluna original indicada em `cta_col` também pode ser usada no template quando permanecer presente no dataframe carregado.

### Não foi possível validar

- O efeito real de `show_legend` e `legend_loc`: esses campos existem no modelo legado, mas não aparecem no conversor nem nos renderizadores enviados.
- O efeito real de `type`: ele existe no modelo legado, mas não é usado no trecho de conversão enviado.

## Erros comuns

- Usar um nome de campo que não existe no CSV ou no dataframe processado.
- Usar formato numérico, como `{cta:.0f}`, em uma coluna textual.
- Usar formato de data, como `{data_hora:%Hh}`, em uma coluna que não pode ser convertida para data/hora.
- Esperar que `format` seja detectado automaticamente: na conversão enviada, ele é fixado em `csv`.
