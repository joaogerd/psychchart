# Render `scatter`

## O que é

Desenha pontos coloridos ou pontos de cor fixa.

## Para que serve

Serve para:

- mostrar observações com uma cor única
- colorir observações por uma coluna ou campo exposto no layer
- exibir colorbar quando houver mapeamento por valor

## Parâmetros disponíveis

- `type`
- `value`
- `cmap`
- `color`
- `size`
- `alpha`
- `edgecolor`
- `edgewidth`
- `colorbar`
- `zorder`

## Valores aceitos

- `type`: `scatter`
- `value`: nome de coluna ou campo acessível no layer
- `cmap`: texto
- `color`: texto
- `size`: número
- `alpha`: número
- `edgecolor`: texto
- `edgewidth`: número
- `colorbar`: booleano
- `zorder`: inteiro

## Exemplo de uso

### Cor fixa

```yaml
render:
  - type: scatter
    color: steelblue
    size: 24
    alpha: 0.8
    edgecolor: black
    edgewidth: 0.3
```

### Cor por valor

```yaml
fields:
  - type: direct_column
    name: CTA
    col: cta_acumulada

render:
  - type: scatter
    value: CTA
    cmap: viridis
    size: 28
    alpha: 0.9
    edgecolor: black
    edgewidth: 0.5
    colorbar: true
```

## Observações importantes

### Confirmado no código

- se `value` for `null`, usa `color` fixo
- se `value` existir, usa `layer.get_array(cfg.value)` para colorir
- a colorbar só é criada quando `colorbar = true`
- o rótulo da colorbar é o próprio nome de `value`

### Inferência controlada

- `value` pode apontar para campo derivado ou coluna acessível pelo runtime do layer

## Erros comuns

- usar `value` sem expor o campo/coluna corretamente
- definir `cmap` e esquecer `value`
- esperar colorbar com `value: null`
