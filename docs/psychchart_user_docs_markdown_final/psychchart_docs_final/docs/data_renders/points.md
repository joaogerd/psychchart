# Render `points`

## O que é

É o renderizador mais simples de `data_layers`: desenha os pontos do dataset já projetados em `(T, W)`.

## Para que serve

Serve para mostrar a nuvem bruta de estados observados sem cor por valor.

## Parâmetros disponíveis

- `type`
- `color`
- `size`
- `alpha`
- `zorder`

## Valores aceitos

- `type`: `points`
- `color`: texto
- `size`: número
- `alpha`: número
- `zorder`: inteiro

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

- usa `ax.scatter(layer.T, layer.W, ...)`
- não usa colorbar
- não usa borda de marcador
- não depende de `fields`

## Erros comuns

- esperar coloração por valor; nesse caso use `scatter`
