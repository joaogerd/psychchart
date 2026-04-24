# `render: { type: points }`

## O que é

Renderização de pontos simples do dataset, sem colorir por variável.

## Para que serve

Serve para desenhar a nuvem de pontos projetada no gráfico usando uma única cor fixa.

## Parâmetros disponíveis

### Confirmado no código

- `type`: deve ser `points`.
- `color`: cor dos marcadores. Padrão: `black`.
- `size`: tamanho dos marcadores. Padrão: `20.0`.
- `alpha`: transparência. Padrão: `0.8`.
- `zorder`: ordem de desenho. Padrão: `40`.

## Valores aceitos

- `type`: `points`.
- `color`: texto.
- `size`, `alpha`: número.
- `zorder`: inteiro.

## Exemplo de uso

```yaml
render:
  - type: points
    color: black
    size: 18
    alpha: 0.7
    zorder: 40
```

## Observações importantes

### Confirmado no código

- O renderer usa apenas `layer.T` e `layer.W` como coordenadas.
- Não existe colorbar neste tipo.
- Não existe borda configurável neste tipo.

## Erros comuns

- Tentar usar `value`, `cmap` ou `colorbar` aqui. Esses campos pertencem a `scatter`.
