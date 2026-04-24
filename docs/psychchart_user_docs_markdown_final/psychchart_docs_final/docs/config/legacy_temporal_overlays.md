# `temporal_overlays` (legado)

## O que é

É um formato legado para trajetórias temporais em espaço psicrométrico.

## Para que serve

Permitia descrever:

- caminho temporal
- pontos
- anotações periódicas
- parte do comportamento de legenda

Hoje, o fluxo mais seguro é usar `data_layers` com `temporal`, `fields` e `render`.

## Parâmetros disponíveis

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

## Exemplo de uso

```yaml
temporal_overlays:
  - type: CTA
    data: "animal_day.csv"
    t_col: temp
    rh_col: rh
    time_col: hour
    cta_col: cta
    annotate_every: 3
    annotation_template: "{time}h\nCTA={cta:.0f}"
    show_path: true
    path_color: blue
    point_size: 42
```

## Conversão automática para `data_layers`

### Confirmado no código

Quando `data_layers` não é fornecido, cada overlay legado vira:

- `data = overlay.data`
- `format = csv`
- `projection` com `t_col`, `rh_col` e `rh_unit = auto`
- `temporal.time_col = overlay.time_col`
- `temporal.sort = true`
- um `field` direto chamado `CTA`, vindo de `cta_col`

#### Renderizadores gerados

- `path` se `show_path` estiver ligado
- `scatter` colorido por `CTA`
- `annotate` se `annotate_every` não for `null`

## Observações importantes

### Confirmado no código

- o `scatter` legado convertido usa `value: CTA` e `colorbar: false`
- o `annotate` legado convertido usa:
  - `time_field = time_col`
  - `value_field = CTA`

### Inconsistência importante

O contrato legado documenta templates como:

```yaml
annotation_template: "{time}h\n(CTA:{cta:.0f})"
```

Mas o renderizador canônico `annotate` disponibiliza placeholders `time` e `value`.

Ou seja, depois da promoção para `data_layers`, o template mais seguro é:

```yaml
template: "{time}h\nCTA={value:.0f}"
```

### Não foi possível validar

- `show_legend` e `legend_loc` no fluxo canônico promovido, porque eles não entram na camada `data_layers`
- o uso efetivo de `type` na promoção para `data_layers`

## Erros comuns

- usar `{cta}` em `template` após migração para `data_layers`
- esperar que os controles de legenda legados tenham efeito no fluxo canônico
