# `render: { type: path }`

## O que é

Linha ordenada ligando pontos do dataset.

## Para que serve

Serve para mostrar trajetória, evolução temporal ou sequência ordenada de estados.

## Parâmetros disponíveis

### Confirmado no código

- `type`: deve ser `path`.
- `order_by`: coluna usada para ordenar a trajetória.
- `color`: cor da linha. Padrão: `blue`.
- `alpha`: transparência. Padrão: `0.6`.
- `linewidth`: espessura da linha. Padrão: `1.2`.
- `zorder`: ordem de desenho. Padrão: `20`.

## Valores aceitos

- `order_by`, `color`: texto opcional.
- `alpha`, `linewidth`: número.
- `zorder`: inteiro.

## Exemplo de uso

### Ordenação explícita

```yaml
render:
  - type: path
    order_by: hour
    color: blue
    alpha: 0.6
    linewidth: 1.2
```

### Ordenação herdada de `temporal`

```yaml
temporal:
  time_col: hour
  sort: true

render:
  - type: path
    color: red
```

## Observações importantes

### Confirmado no código

- Se `order_by` for informado, ele é usado.
- Se `order_by` não for informado e existir `temporal`, o renderer usa `temporal.time_col`.
- O desenho usa `solid_capstyle="round"` e `solid_joinstyle="round"`.

### Não foi possível validar

- Como o runtime se comporta quando não existe `order_by` e também não existe `temporal`. O renderer chama `ordered_frame(order_by)` e isso depende da implementação de `ProcessedDataLayer`, que não foi enviada.

## Erros comuns

- Esperar uma trajetória temporal correta sem informar como os dados devem ser ordenados.
