# Render `path`

## O que é

Desenha uma trajetória ordenada ao longo dos registros do dataset.

## Para que serve

Serve para séries temporais ou sequências ordenadas de estados.

## Parâmetros disponíveis

- `type`
- `order_by`
- `color`
- `alpha`
- `linewidth`
- `zorder`

## Valores aceitos

- `type`: `path`
- `order_by`: nome de coluna
- `color`: texto
- `alpha`: número
- `linewidth`: número
- `zorder`: inteiro

## Exemplo de uso

```yaml
temporal:
  time_col: hour
  sort: true

render:
  - type: path
    color: blue
    alpha: 0.6
    linewidth: 1.2
```

### Com ordenação explícita

```yaml
render:
  - type: path
    order_by: hour
    color: black
    linewidth: 1.5
```

## Observações importantes

### Confirmado no código

- se `order_by` não for informado, o renderer tenta usar `layer.config.temporal.time_col`
- o desenho usa `layer.ordered_frame(order_by)`
- a linha é desenhada com `ax.plot` em `_T` e `_W`
- o renderer usa `solid_capstyle="round"` e `solid_joinstyle="round"`

### Inferência controlada

- quando a ordem importa, é mais seguro definir `temporal.time_col` ou `order_by`

## Erros comuns

- usar `path` sem qualquer ordenação temporal ou lógica
- assumir que a ordem original do arquivo sempre será a desejada
