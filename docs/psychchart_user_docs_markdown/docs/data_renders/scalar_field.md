# `render: { type: scalar_field }`

## O que é

Campo escalar agregado a partir de uma camada processada.

## Para que serve

Serve para transformar uma variável escalar da camada em um campo 2D agregado sobre o domínio do gráfico.

## Parâmetros disponíveis

### Confirmado no código

- `type`: deve ser `scalar_field`.
- `value`: nome do campo/variável a ser agregado.
- `bins`: resolução da agregação. Padrão: `(40, 40)`.
- `cmap`: colormap. Padrão: `viridis`.
- `alpha`: transparência. Padrão: `0.6`.
- `colorbar`: mostra barra de cor. Padrão: `true`.
- `zorder`: ordem de desenho. Padrão: `25`.

## Valores aceitos

- `value`: texto.
- `bins`: par de inteiros.
- `cmap`: texto.
- `alpha`: número.
- `colorbar`: booleano.
- `zorder`: inteiro.

## Exemplo de uso

```yaml
fields:
  - type: direct_column
    name: CTA
    col: cta_acumulada

render:
  - type: scalar_field
    value: CTA
    bins: [40, 40]
    cmap: plasma
    alpha: 0.6
    colorbar: true
```

## Observações importantes

### Confirmado no código

- O renderer falha com erro se `layer.functional_observations` for `None`.
- O campo é construído com `to_scalar_field(value, bins=...)`.
- Quando `colorbar: true`, o rótulo da barra de cor é `field.name`.

### Não foi possível validar

- Se uma simples coluna direta sem processamento sempre gera `functional_observations` suficiente para esse renderer funcionar. O código enviado não permite confirmar isso com segurança.

## Erros comuns

- Declarar `scalar_field` sem ter preparado os dados necessários para `functional_observations`.
- Informar `value` que não existe na camada processada.
