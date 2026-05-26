# `data_layers` — formato canônico para camadas baseadas em dados

## O que é

É o formato atual e unificado para descrever qualquer camada que venha de arquivo tabular e seja projetada no espaço psicrométrico.

## Para que serve

Serve para representar, em um único formato:

- pontos simples
- scatter colorido por valor
- densidade
- campo escalar agregado
- trajetória ordenada
- anotações periódicas

## Parâmetros disponíveis

## Seção `data_layers[]`

### O que é

É uma camada baseada em um arquivo.

### Para que serve

Serve para dizer qual arquivo será lido, como as colunas serão interpretadas e quais saídas visuais serão desenhadas.

### Parâmetros disponíveis

### Confirmado no código

- `data`: caminho do arquivo.
- `format`: formato do arquivo. Padrão: `parquet`.
- `projection`: mapeamento termodinâmico obrigatório.
- `temporal`: ordenação temporal opcional.
- `fields`: campos derivados opcionais.
- `render`: lista de renderizações.

### Valores aceitos

- `data`: texto.
- `format`: texto.
- `projection`: objeto.
- `temporal`: objeto opcional.
- `fields`: lista.
- `render`: lista.

### Exemplo de uso

```yaml
data_layers:
  - data: "animal_day.csv"
    format: "csv"
    projection:
      t_col: "temp"
      rh_col: "rh"
      rh_unit: auto
    temporal:
      time_col: "hour"
      sort: true
    fields:
      - type: direct_column
        name: CTA
        col: cta_acumulada
    render:
      - type: path
        order_by: hour
      - type: scatter
        value: CTA
        cmap: viridis
      - type: annotate
        every: 3
        template: "{time}h\n(CTA:{value:.0f})"
        time_field: hour
        value_field: CTA
```

### Observações importantes

### Confirmado no código

- `projection` é obrigatório.
- `render` aceita vários itens, permitindo empilhar diferentes saídas visuais sobre o mesmo arquivo.
- `temporal` é opcional, mas influencia ordenação de `path` e `annotate`.

### Erros comuns

- Omitir `projection`.
- Tentar colocar um objeto em `render` sem `type`.
- Usar tipos de `render` não declarados.

---

## Seção `projection`

### O que é

Define quais colunas do arquivo representam temperatura e umidade relativa.

### Para que serve

Serve para projetar dados tabulares no domínio psicrométrico.

### Parâmetros disponíveis

### Confirmado no código

- `t_col`
- `rh_col`
- `rh_unit`

### Valores aceitos

### Confirmado no código

- `t_col`: texto.
- `rh_col`: texto.
- `rh_unit`: `fraction`, `percent` ou `auto`.

### Exemplo de uso

```yaml
projection:
  t_col: temp
  rh_col: rh
  rh_unit: auto
```

### Observações importantes

### Confirmado no código

- `rh_unit: auto` aceita os dois formatos e deixa a normalização para o runtime.

### Não foi possível validar

- O algoritmo exato de conversão para razão de umidade não foi enviado.

### Erros comuns

- Apontar `rh_col` para uma coluna em unidade diferente do informado.

---

## Seção `temporal`

### O que é

Metadado opcional para ordenar o arquivo como sequência temporal.

### Para que serve

Serve principalmente para trajetórias e anotações periódicas.

### Parâmetros disponíveis

### Confirmado no código

- `time_col`
- `sort` (padrão: `true`)

### Valores aceitos

- `time_col`: texto.
- `sort`: booleano.

### Exemplo de uso

```yaml
temporal:
  time_col: hour
  sort: true
```

### Observações importantes

### Confirmado no código

- `path` usa `order_by` quando informado.
- Se `order_by` não for informado e existir `temporal`, o renderizador de `path` usa `temporal.time_col`.
- `annotate` também ordena pela coluna temporal quando `temporal` está presente.

### Erros comuns

- Esperar ordenação temporal sem informar `temporal` nem `order_by`.

---

## Seção `fields`

### O que é

Define campos adicionais expostos aos renderizadores.

### Para que serve

Serve para nomear colunas existentes ou pedir cálculo de campos derivados.

### Parâmetros disponíveis

### Tipo `direct_column`

- `type`: fixo em `direct_column`
- `name`: nome público do campo
- `col`: coluna de origem

### Tipo `data_index`

- `type`: fixo em `data_index`
- `name`: nome público do campo
- `index`: identificador do índice de dados
- `source_col`: coluna de origem opcional
- `parameters`: parâmetros opcionais

### Exemplo de uso

```yaml
fields:
  - type: direct_column
    name: CTA
    col: cta_acumulada

  - type: data_index
    name: ICF
    index: ICF
    source_col: behavior
    parameters: {}
```

### Observações importantes

### Confirmado no código

- `direct_column` apenas expõe uma coluna existente com um nome público.
- `data_index` descreve um campo calculado por um backend de índice de dados.

### Não foi possível validar

- Quais índices de dados estão registrados no runtime.
- Como `parameters` é consumido por cada backend.

### Erros comuns

- Usar `value` em um render apontando para um nome que não existe nem em coluna nem em `fields`.

---

## Renderizador `scatter`

### O que é

Desenha pontos do dataset no espaço psicrométrico. Pode usar uma cor fixa ou colorir os pontos por um campo numérico, como `cta`.

### Parâmetros principais

- `type`: fixo em `scatter`.
- `value`: campo usado para colorir os pontos.
- `order_by`: coluna usada para ordenar os pontos antes da amostragem.
- `every`: intervalo de amostragem dos pontos desenhados. Padrão: `1`.
- `cmap`: mapa de cores do Matplotlib.
- `size`: tamanho dos pontos.
- `alpha`: transparência.
- `edgecolor`: cor da borda.
- `edgewidth`: espessura da borda.
- `colorbar`: ativa a barra de cores.
- `zorder`: ordem de desenho.

### Controles da barra de cores

Quando `colorbar: true`, os seguintes parâmetros permitem controlar o layout da barra diretamente no YAML:

- `colorbar_label`: rótulo da barra.
- `colorbar_location`: posição da barra. Aceita `left`, `right`, `top` ou `bottom`.
- `colorbar_shrink`: fração do tamanho da barra em relação ao eixo.
- `colorbar_pad`: espaço entre o eixo principal e a barra.
- `colorbar_aspect`: proporção comprimento/largura da barra.
- `colorbar_fraction`: fração da área do eixo usada pela barra.
- `colorbar_ticks`: marcas numéricas exibidas.
- `colorbar_labelpad`: distância entre a barra e o rótulo.
- `colorbar_label_rotation`: rotação do rótulo.

### Exemplo recomendado para CTA

```yaml
- type: scatter
  value: cta
  order_by: data_hora
  every: 3
  cmap: plasma
  size: 48
  alpha: 0.95
  edgecolor: black
  edgewidth: 0.7
  colorbar: true
  colorbar_label: "CTA 19h"
  colorbar_location: right
  colorbar_fraction: 0.035
  colorbar_pad: 0.08
  colorbar_aspect: 28
  colorbar_shrink: 0.78
  colorbar_ticks: [160, 170, 180, 190, 200, 210]
  colorbar_labelpad: 18
  colorbar_label_rotation: 270
  zorder: 50
```

### Observações importantes

- `every` é aplicado após a ordenação temporal.
- A barra de cores do `scatter` é independente de outras barras do gráfico, como campos contínuos de índices.
- Quando houver mais de uma barra de cores no gráfico, aumente `colorbar_pad` para evitar sobreposição com o eixo `W`.

---

## Renderizador `path`

### O que é

Desenha uma trajetória ordenada no espaço psicrométrico.

### Parâmetros principais

- `type`: fixo em `path`.
- `order_by`: coluna usada para ordenar a trajetória.
- `every`: intervalo de amostragem dos vértices da trajetória. Padrão: `1`.
- `color`: cor da linha quando `color_by` não é usado.
- `color_by`: campo usado para colorir segmentos da trajetória.
- `cmap`: mapa de cores quando `color_by` é usado.
- `linewidth`: espessura da linha.
- `linestyle`: estilo da linha.
- `label`: rótulo de legenda.
- `zorder`: ordem de desenho.

### Exemplo

```yaml
- type: path
  order_by: data_hora
  every: 1
  color: "#b36b00"
  alpha: 0.75
  linewidth: 2.2
  linestyle: "-"
  label: "Trajetória CTA"
  zorder: 45
```

---

## Renderizador `annotate`

### O que é

Desenha textos periódicos ao longo da camada de dados.

### Parâmetros principais

- `type`: fixo em `annotate`.
- `every`: intervalo entre anotações.
- `template`: texto formatado.
- `time_field`: campo usado como `{time}`.
- `time_format`: formato `strftime` aplicado a `time_field`.
- `value_field`: campo usado como `{value}`.
- `dx`: deslocamento horizontal.
- `dy`: deslocamento vertical.
- `fontsize`: tamanho da fonte.
- `fontweight`: peso da fonte.
- `color`: cor do texto.
- `zorder`: ordem de desenho.

### Exemplo

```yaml
- type: annotate
  every: 6
  template: "{time}"
  time_field: data_hora
  time_format: "%Hh"
  value_field: cta
  dx: 0.25
  dy: 0.00035
  fontsize: 8
  fontweight: bold
  color: black
  zorder: 60
```

---

## Substituição de `temporal_overlays` por `data_layers`

`temporal_overlays` é mantido apenas como formato legado de entrada. A forma
canônica para trajetórias temporais é `data_layers`, combinando:

- `projection` para mapear temperatura e umidade relativa;
- `temporal` para declarar a coluna de tempo e ordenação;
- `fields` para expor uma métrica acumulada, como CTA;
- `render` para desenhar caminho, pontos coloridos e anotações.

Exemplo canônico:

```yaml
data_layers:
  - data: "animal_day.csv"
    format: "csv"
    projection:
      t_col: "temperature"
      rh_col: "relative_humidity"
      rh_unit: auto
    temporal:
      time_col: "hour"
      sort: true
    fields:
      - type: direct_column
        name: CTA
        col: cta_accumulated
    render:
      - type: path
        order_by: hour
        color: blue
        linewidth: 1.5
        label: "CTA trajectory"
      - type: scatter
        value: CTA
        cmap: viridis
        colorbar: true
      - type: annotate
        every: 3
        template: "{time}h\nCTA={value:.0f}"
        time_field: hour
        value_field: CTA
```

Equivalência legada:

```yaml
temporal_overlays:
  - type: CTA
    data: "animal_day.csv"
    t_col: "temperature"
    rh_col: "relative_humidity"
    time_col: "hour"
    cta_col: "cta_accumulated"
```

Quando `data_layers` não é informado, essa forma legada é convertida
internamente para a estrutura canônica. Quando `data_layers` é informado, ele
tem precedência e `temporal_overlays` não é usado para sintetizar camadas.
