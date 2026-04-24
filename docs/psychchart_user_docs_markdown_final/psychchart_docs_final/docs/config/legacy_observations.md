# `observations` (legado)

## O que é

É um formato legado para datasets observacionais.

## Para que serve

Permitia configurar:

- um arquivo observacional
- uma densidade resumida
- um ou mais índices dirigidos por dados

Hoje, o fluxo mais seguro é usar `data_layers`.

## Parâmetros disponíveis

- `file`
- `format`
- `data_indexes`
- `density`

### Em `data_indexes`

- `index`
- `scatter`
- `scalar_field`
- `bins`
- `cmap`
- `alpha`
- `colorbar`

### Em `density`

- `bins`
- `cmap`
- `vmin`
- `vmax`
- `alpha`
- `colorbar`
- `normalize`

## Exemplo de uso

```yaml
observations:
  - file: "animals.parquet"
    format: "parquet"
    data_indexes:
      - index: CTA
        scatter: true
        scalar_field: true
        bins: [50, 50]
        cmap: plasma
        colorbar: true
    density:
      bins: [80, 80]
      cmap: viridis
      alpha: 0.5
```

## Conversão automática para `data_layers`

### Confirmado no código

Quando `data_layers` não é fornecido, cada item de `observations` é convertido para uma camada canônica com:

- `data = file`
- `format = format` ou `parquet`
- `projection.t_col = T`
- `projection.rh_col = RH`
- `projection.rh_unit = auto`

#### Para cada `data_index`

- se `index == ICF`, vira `field` do tipo `data_index` com `source_col = behavior`
- caso contrário, vira `field` do tipo `direct_column` com o mesmo nome da coluna

#### Renderização gerada

- `scatter: true` cria um `render` do tipo `scatter`
- `scalar_field: true` cria um `render` do tipo `scalar_field`
- `density` cria um `render` do tipo `density`

## Observações importantes

### Confirmado no código

- `scatter` e `scalar_field` são independentes
- `colorbar` default de `DataIndexConfig` é `true`
- `density.normalize` existe no contrato e é encaminhado na promoção automática

### Não foi possível validar

- a semântica exata da normalização em `density.normalize`
- se ainda existe algum fluxo principal do projeto que consome `observations` sem passar por `data_layers`

## Erros comuns

- usar nomes de coluna diferentes de `T` e `RH` e esperar que a promoção automática descubra isso
- continuar investindo em `observations` como formato principal
