# Render `scalar_field`

## O que é

Agrega um valor escalar do dataset em um campo bidimensional no gráfico.

## Para que serve

Serve para transformar uma variável observada ou derivada em um campo contínuo resumido por bins.

## Parâmetros disponíveis

- `type`
- `value`
- `bins`
- `cmap`
- `alpha`
- `colorbar`
- `zorder`

## Valores aceitos

- `type`: `scalar_field`
- `value`: nome do campo/coluna
- `bins`: par de inteiros
- `cmap`: texto
- `alpha`: número
- `colorbar`: booleano
- `zorder`: inteiro

## Exemplo de uso

```yaml
fields:
  - type: direct_column
    name: CTA
    col: cta_acumulada

render:
  - type: scalar_field
    value: CTA
    bins: [50, 50]
    cmap: plasma
    alpha: 0.6
    colorbar: true
```

## Observações importantes

### Confirmado no código

- o renderer exige que `layer.functional_observations` exista
- se não existir, lança erro dizendo que o `data_layer` precisa de pelo menos um campo derivado
- o campo é gerado via `to_scalar_field(cfg.value, bins=cfg.bins)`
- a colorbar usa `field.name`

### Inferência controlada

- na prática, esse render é mais seguro quando `fields` define claramente o valor a ser usado

## Erros comuns

- usar `scalar_field` sem `fields`
- informar `value` que o runtime não consegue resolver
