# `zones` e `index_zones` — regiões do gráfico

O psychChart possui dois mecanismos para representar áreas no diagrama psicrométrico.

`zones` representa zonas geométricas, definidas diretamente por vértices ou por intervalos de temperatura e umidade relativa.

`index_zones` representa zonas calculadas a partir de uma faixa de índice. Esse é o mecanismo correto para pintar uma área baseada em ITU, HLI ou outro índice registrado.

---

## `zones`

## O que é

Zona geométrica definida por vértices explícitos ou por intervalos de temperatura e umidade relativa.

## Para que serve

Serve para representar regiões como conforto, alerta, operação admissível, envelope experimental ou qualquer outra área definida diretamente no espaço psicrométrico.

## Parâmetros disponíveis

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

## Exemplo de uso

```yaml
zones:
  - name: comfort_band
    t_range: [18, 26]
    rh_range: [40, 70]
    follow_rh: true
    edgecolor: green
    facecolor: lightgreen
    linewidth: 1.5
    alpha: 0.3
    show_label: true
    label: "Comfort"
    label_t: 22
    label_rh: 55
```

## Observações importantes

- `rh_range` e `label_rh` aceitam porcentagem ou fração e são normalizados internamente.
- `follow_rh: true` faz o contorno seguir curvas de umidade relativa.
- Use `zones` quando a geometria da região já é conhecida antes do cálculo de qualquer índice.

---

## `index_zones`

## O que é

Zona semântica definida por um intervalo de um índice calculado, e não por geometria direta.

## Para que serve

Serve para pintar regiões do gráfico onde um índice fica dentro de uma faixa numérica, por exemplo:

```text
68 <= ITU <= 72
```

Nesse caso, o psychChart avalia o índice em todo o domínio físico válido do gráfico e preenche a região onde o valor calculado satisfaz o intervalo definido.

## Parâmetros disponíveis

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

## Valores aceitos

- `index`, `name`, `color`, `facecolor`, `edgecolor`, `label`, `label_color`, `label_fontweight`: texto.
- `range`: par numérico com limite inferior menor que limite superior.
- `alpha`, `linewidth`, `label_fontsize`, `label_rotation`, `label_t`, `label_rh`: número.
- `show_label`: booleano.
- `label_position`: `auto` ou `manual`.
- `parameters`, `label_bbox`: objeto.

## Exemplo com rótulo interno automático

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

## Exemplo com rótulo interno manual

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

## Erros comuns

- Usar `zones` para representar uma faixa de ITU. Para isso, use `index_zones`.
- Usar `label_position: manual` sem informar `label_t` e `label_rh`.
- Definir `range` com limite inferior maior ou igual ao limite superior.
- Definir `index_zones` com um índice que não existe no registry.
