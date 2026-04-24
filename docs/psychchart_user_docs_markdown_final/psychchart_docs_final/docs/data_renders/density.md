# Render `density`

## O que é

Cria um campo de densidade bidimensional a partir do dataset.

## Para que serve

Serve para resumir a concentração de observações no gráfico, evitando plotar apenas pontos individuais.

## Parâmetros disponíveis

- `type`
- `bins`
- `cmap`
- `vmin`
- `vmax`
- `alpha`
- `colorbar`
- `normalize`
- `zorder`

## Valores aceitos

- `type`: `density`
- `bins`: par de inteiros
- `cmap`: texto
- `vmin`, `vmax`: número
- `alpha`: número
- `colorbar`: booleano
- `normalize`: booleano
- `zorder`: inteiro

## Exemplo de uso

```yaml
render:
  - type: density
    bins: [80, 80]
    cmap: viridis
    alpha: 0.5
    colorbar: true
    normalize: true
```

## Observações importantes

### Confirmado no código

- o renderer chama `layer.observations.to_density_field(cfg, chart.cfg)`
- valores menores ou iguais a zero são mascarados antes do `pcolormesh`
- bins vazios ficam transparentes, e não pintados com a cor mínima
- `vmin` e `vmax` são passados ao `pcolormesh`
- a colorbar, quando ativada, recebe o rótulo fixo `"Density"`

### Não foi possível validar

- a semântica exata de `normalize`
- a estratégia completa usada por `to_density_field()` para construir o campo

## Erros comuns

- interpretar `normalize` como algo já documentado em detalhe no código enviado
- achar que bins vazios sempre aparecem; aqui eles são mascarados
