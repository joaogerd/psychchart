# `zones` e `index_zones`

## O que é

Há dois tipos de zonas nos arquivos enviados:

- `zones`: zonas geométricas
- `index_zones`: zonas semânticas baseadas em faixas de índice

## Para que serve

### `zones`

Usadas para representar regiões como:

- conforto
- risco
- envelopes operacionais
- regiões definidas manualmente

### `index_zones`

Usadas para colorir áreas do gráfico conforme intervalos de um índice, como `ITU` ou `TE`.

---

## `zones`

### Parâmetros disponíveis

- `name`
- `vertices`
- `t_range`
- `rh_range`
- `follow_rh`
- `edgecolor`
- `facecolor`
- `linewidth`
- `alpha`

### Valores aceitos

- `vertices`: lista de pares numéricos
- `t_range`: par numérico
- `rh_range`: par numérico em fração ou porcentagem
- `follow_rh`: booleano
- `edgecolor`, `facecolor`: texto
- `linewidth`, `alpha`: número

### Exemplo de uso

```yaml
zones:
  - name: "comfort_band"
    t_range: [18, 26]
    rh_range: [40, 70]
    follow_rh: true
    edgecolor: "green"
    facecolor: "lightgreen"
    alpha: 0.3
```

### Observações importantes

#### Confirmado no código

- `rh_range` é normalizado para fração
- o renderer geométrico aceita:
  - polígono explícito por `vertices`
  - zona por `t_range + rh_range`
  - zona com bordas seguindo curvas de umidade relativa quando `follow_rh = true`

#### Inferência controlada

- `follow_rh: true` é a forma mais coerente para zonas que você quer alinhar à física psicrométrica, e não a um retângulo bruto no plano

---

## `index_zones`

### Parâmetros disponíveis

- `index`
- `name`
- `range`
- `color`
- `alpha`
- `parameters`

### Valores aceitos

- `index`: texto
- `name`: texto
- `range`: par numérico
- `color`: texto
- `alpha`: número
- `parameters`: dicionário

### Exemplo de uso

```yaml
index_zones:
  - index: ITU
    name: "danger"
    range: [78, 84]
    color: "orange"
    alpha: 0.25
```

### Observações importantes

#### Confirmado no código

- o renderer de `index_zones` cria uma máscara booleana da faixa e desenha uma região preenchida com `contourf`
- o nome da zona também aparece como texto no canto superior esquerdo do gráfico, em coordenadas do eixo

#### Não foi possível validar

- a estratégia completa de clipping físico dessas zonas em todos os cenários
