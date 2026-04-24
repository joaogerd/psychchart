# `render: { type: density }`

## O que é

Campo 2D de densidade derivado da distribuição dos pontos do dataset.

## Para que serve

Serve para resumir concentração de observações em vez de desenhar todos os pontos individualmente.

## Parâmetros disponíveis

### Confirmado no código

- `type`: deve ser `density`.
- `bins`: resolução do histograma 2D. Padrão: `(60, 60)`.
- `cmap`: colormap. Padrão: `viridis`.
- `vmin`, `vmax`: limites opcionais de normalização.
- `alpha`: transparência. Padrão: `0.6`.
- `colorbar`: mostra barra de cor. Padrão: `true`.
- `normalize`: existe no contrato. Padrão: `true`.
- `zorder`: ordem de desenho. Padrão: `20`.

## Valores aceitos

- `bins`: par de inteiros.
- `cmap`: texto.
- `vmin`, `vmax`: números opcionais.
- `alpha`: número.
- `colorbar`, `normalize`: booleanos.
- `zorder`: inteiro.

## Exemplo de uso

```yaml
render:
  - type: density
    bins: [60, 60]
    cmap: viridis
    vmin: 0.0
    vmax: 1.0
    alpha: 0.6
    colorbar: true
    normalize: true
    zorder: 20
```

## Observações importantes

### Confirmado no código

- O renderer chama `layer.observations.to_density_field(cfg, chart.cfg)`.
- Bins vazios são mascarados antes do desenho.
- Regiões sem suporte observacional ficam transparentes, em vez de receber a cor mínima do colormap.
- Quando `colorbar: true`, o rótulo da barra é `Density`.

### Não foi possível validar

- O efeito matemático exato de `normalize`, porque a implementação de `to_density_field` não foi enviada.

## Erros comuns

- Interpretar regiões transparentes como “valor mínimo de densidade”. No código enviado, transparência aqui significa bin vazio mascarado.
