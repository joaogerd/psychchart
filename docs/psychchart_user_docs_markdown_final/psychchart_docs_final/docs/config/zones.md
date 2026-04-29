# `zones` e `index_zones`

O psychChart possui dois mecanismos complementares para desenhar regiões no gráfico psicrométrico.

`zones` representa zonas geométricas declaradas diretamente pelo usuário em temperatura e umidade relativa. Esse mecanismo é adequado para envelopes experimentais, regiões manuais, áreas de projeto ou polígonos definidos por vértices.

`index_zones` representa zonas derivadas de intervalos de um índice calculado, como `ITU`, `HLI`, `BGHI` ou qualquer outro índice registrado. Nesse caso, a geometria da região não é fornecida manualmente. O psychChart avalia o índice no domínio psicrométrico válido e pinta os pontos em que o valor calculado cai dentro do intervalo configurado.

## `zones`

Use `zones` quando a região já é conhecida geometricamente.

Parâmetros aceitos:

- `name`
- `vertices`
- `t_range`
- `rh_range`
- `follow_rh`
- `edgecolor`
- `facecolor`
- `linewidth`
- `alpha`
- `show_label`
- `label`
- `label_t`
- `label_rh`
- `label_color`
- `label_fontsize`
- `label_rotation`
- `label_bbox`

Exemplo:

```yaml
zones:
  - name: "comfort_band"
    t_range: [18, 26]
    rh_range: [40, 70]
    follow_rh: true
    edgecolor: "green"
    facecolor: "lightgreen"
    linewidth: 1.5
    alpha: 0.3
    show_label: true
    label: "Comfort"
    label_t: 22
    label_rh: 55
```

Observações:

- `rh_range` e `label_rh` aceitam fração ou porcentagem.
- `follow_rh: true` faz as bordas seguirem curvas de umidade relativa.
- `vertices` devem ser fornecidos em coordenadas de temperatura e umidade relativa.

## `index_zones`

Use `index_zones` quando a região deve ser definida por uma faixa numérica de um índice calculado. Esse é o mecanismo recomendado para pintar uma área de ITU, por exemplo uma faixa entre 68 e 72.

Parâmetros aceitos:

- `index`
- `name`
- `range`
- `color`
- `facecolor`
- `edgecolor`
- `linewidth`
- `alpha`
- `show_label`
- `label`
- `label_position`
- `label_t`
- `label_rh`
- `label_color`
- `label_fontsize`
- `label_fontweight`
- `label_rotation`
- `label_bbox`
- `parameters`

`color` é mantido como alias legado para a cor de preenchimento. Em novas configurações, prefira `facecolor`.

`label_position` aceita dois valores: `auto` e `manual`. Com `auto`, o psychChart estima uma posição interna representativa da região pintada. Com `manual`, use também `label_t` e `label_rh`.

Exemplo com rótulo automático:

```yaml
index_zones:
  - index: ITU
    name: "ITU comfort zone"
    range: [68, 72]
    facecolor: "#A8E67A"
    edgecolor: "#5B8F3A"
    alpha: 0.38
    linewidth: 1.1
    show_label: true
    label: "ITU"
    label_position: auto
    label_color: "#2F3A2F"
    label_fontsize: 12
    label_fontweight: "bold"
    label_rotation: 72
```

Exemplo com rótulo manual:

```yaml
index_zones:
  - index: ITU
    name: "ITU comfort zone"
    range: [68, 72]
    facecolor: "#A8E67A"
    edgecolor: "#5B8F3A"
    alpha: 0.38
    linewidth: 1.1
    show_label: true
    label: "ITU"
    label_position: manual
    label_t: 25.5
    label_rh: 55
    label_color: "#2F3A2F"
    label_fontsize: 12
    label_fontweight: "bold"
    label_rotation: 72
```

Exemplo completo mínimo:

```yaml
chart:
  t_min: 10
  t_max: 45
  y_min: 0.0
  y_max: 0.035
  pressure: 101325
  output: "index_zone_itu_labeled.png"

indexes:
  - index: ITU
    render:
      isolines:
        levels: [68, 72, 78, 84]
        color: "#111111"
        linewidth: 0.9
        label: true
        label_fmt: "ITU {value:.0f}"

index_zones:
  - index: ITU
    name: "ITU comfort zone"
    range: [68, 72]
    facecolor: "#A8E67A"
    edgecolor: "#5B8F3A"
    alpha: 0.38
    linewidth: 1.1
    show_label: true
    label: "ITU"
    label_position: auto
    label_rotation: 72
```

## Escolha correta

Use `zones` para áreas geométricas ou experimentais.

Use `index_zones` para áreas calculadas por índice. Para ITU, HLI ou outros índices, essa é a forma correta, porque a área final é calculada a partir do campo do índice e não a partir de uma aproximação retangular.
