# `render: { type: scatter }`

## O que é

Renderização de pontos com suporte a cor fixa ou coloração por valor.

## Para que serve

Serve para mostrar amostras individuais e, opcionalmente, codificar uma variável por cor.

## Parâmetros disponíveis

### Confirmado no código

- `type`: deve ser `scatter`.
- `value`: nome do campo/coluna usado para colorir os pontos.
- `cmap`: colormap quando `value` é usado.
- `color`: cor fixa quando `value` não é usado.
- `size`: tamanho dos marcadores. Padrão: `20.0`.
- `alpha`: transparência. Padrão: `0.8`.
- `edgecolor`: cor da borda. Padrão: `black`.
- `edgewidth`: largura da borda. Padrão: `0.3`.
- `colorbar`: mostra barra de cor. Padrão: `false`.
- `zorder`: ordem de desenho. Padrão: `45`.

## Valores aceitos

- `value`, `cmap`, `color`, `edgecolor`: texto opcional.
- `size`, `alpha`, `edgewidth`: número.
- `colorbar`: booleano.
- `zorder`: inteiro.

## Exemplo de uso

### Cor fixa

```yaml
render:
  - type: scatter
    color: darkblue
    size: 20
    alpha: 0.8
    edgecolor: black
    edgewidth: 0.3
```

### Cor por variável

```yaml
render:
  - type: scatter
    value: CTA
    cmap: viridis
    size: 24
    alpha: 0.9
    edgecolor: black
    edgewidth: 0.4
    colorbar: true
```

## Observações importantes

### Confirmado no código

- Se `value` for `None`, o renderer usa `color` fixo.
- Se `value` existir, o renderer busca os dados com `layer.get_array(value)`.
- Quando `colorbar: true`, o rótulo da barra de cor é exatamente o conteúdo de `value`.

### Não foi possível validar

- Quais nomes são válidos em `value`, porque isso depende do que existe na camada processada.

## Erros comuns

- Usar `colorbar: true` sem `value` e esperar uma barra de cor quantitativa.
- Informar `value` que não existe no dataset nem em `fields`.
