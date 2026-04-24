# `zones` e `index_zones` — regiões do gráfico

## `zones`

## O que é

Zona geométrica definida por vértices explícitos ou por intervalos de temperatura e umidade relativa.

## Para que serve

Serve para representar regiões como conforto, alerta, operação admissível ou qualquer outra área de interesse no gráfico.

## Parâmetros disponíveis

### Confirmado no código

- `name`
- `vertices`
- `t_range`
- `rh_range`
- `follow_rh`
- `edgecolor`
- `facecolor`
- `linewidth`
- `alpha`

## Valores aceitos

- `name`: texto.
- `vertices`: lista de pares numéricos.
- `t_range`: par numérico.
- `rh_range`: par numérico.
- `follow_rh`: booleano.
- `edgecolor`, `facecolor`: texto.
- `linewidth`, `alpha`: número.

## Exemplo de uso

### Zona por intervalos

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
```

### Zona por vértices

```yaml
zones:
  - name: comfort_polygon
    vertices:
      - [20.0, 0.006]
      - [24.0, 0.007]
      - [26.0, 0.009]
    edgecolor: green
    facecolor: lightgreen
```

## Observações importantes

### Confirmado no código

- `rh_range` aceita porcentagem ou fração e é normalizado para fração.
- A zona pode ser declarada por geometria explícita (`vertices`) ou por faixas semânticas (`t_range` + `rh_range`).

### Inferência controlada

- `follow_rh: true` sugere que o contorno deve seguir curvas de umidade relativa, e não um retângulo bruto.

### Não foi possível validar

- O algoritmo exato que transforma `t_range` + `rh_range` em polígono final.

## Erros comuns

- Misturar coordenadas de `vertices` com a ideia de `rh_range`: `vertices` aparenta esperar coordenadas finais do gráfico, enquanto `rh_range` ainda está em umidade relativa.

---

## `index_zones`

## O que é

Zona semântica definida por um intervalo de um índice calculado, e não por geometria direta.

## Para que serve

Serve para classificar o gráfico por faixas de índice, como conforto, alerta ou perigo.

## Parâmetros disponíveis

### Confirmado no código

- `index`
- `name`
- `range`
- `color`
- `alpha`
- `parameters`

## Valores aceitos

- `index`, `name`, `color`: texto.
- `range`: par numérico.
- `alpha`: número.
- `parameters`: objeto.

## Exemplo de uso

```yaml
index_zones:
  - index: ITU
    name: comfort
    range: [20, 72]
    color: green
    alpha: 0.25
```

## Observações importantes

### Confirmado no código

- `parameters` existe para índices parametrizados.

### Não foi possível validar

- Como a região espacial correspondente a `range` é calculada no gráfico.

## Erros comuns

- Definir `index_zones` sem que o índice correspondente exista no runtime.
