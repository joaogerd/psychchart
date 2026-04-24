# `data_layers`

## O que é

É o formato canônico atual para qualquer camada baseada em dataset tabular.

## Para que serve

Um `data_layer` descreve, em um único bloco:

- qual arquivo será lido
- quais colunas representam `T` e `RH`
- se existe ordenação temporal
- quais campos extras devem ser expostos
- como esses dados devem ser desenhados

## Estrutura geral

Um `data_layer` é organizado em cinco blocos:

1. identidade do dataset
2. projeção termodinâmica
3. ordenação temporal opcional
4. campos derivados opcionais
5. uma ou mais especificações de `render`

## Parâmetros disponíveis

### Raiz do `data_layer`

- `data`
- `format`
- `projection`
- `temporal`
- `fields`
- `render`

### `projection`

- `t_col`
- `rh_col`
- `rh_unit`

### `temporal`

- `time_col`
- `sort`

### `fields`

Tipos aceitos:

- `direct_column`
- `data_index`

#### `direct_column`

- `type`
- `name`
- `col`

#### `data_index`

- `type`
- `name`
- `index`
- `source_col`
- `parameters`

### `render`

Tipos aceitos:

- `points`
- `scatter`
- `density`
- `scalar_field`
- `path`
- `annotate`

## Valores aceitos

### Na raiz

- `data`: caminho do arquivo
- `format`: texto, como `csv` ou outro formato tabular aceito pelo runtime
- `projection`: obrigatório
- `temporal`: opcional
- `fields`: lista opcional
- `render`: lista obrigatória

### `projection.rh_unit`

Aceita:

- `fraction`
- `percent`
- `auto`

## Exemplo de uso

### Exemplo simples

```yaml
data_layers:
  - data: "observations.csv"
    format: "csv"
    projection:
      t_col: T
      rh_col: RH
      rh_unit: auto
    render:
      - type: points
```

### Exemplo com ordenação temporal e campo derivado

```yaml
data_layers:
  - data: "animal_day.csv"
    format: "csv"
    projection:
      t_col: temp
      rh_col: rh
      rh_unit: percent
    temporal:
      time_col: hour
      sort: true
    fields:
      - type: direct_column
        name: CTA
        col: cta_acumulada
    render:
      - type: path
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

## Observações importantes

### Confirmado no código

- `projection` define como o dataset vira estados psicrométricos.
- `rh_unit: auto` aceita fração ou porcentagem e deixa a normalização para o runtime.
- `temporal.sort` existe e o `path`/`annotate` podem usar a ordenação temporal.
- `fields` permite expor colunas diretas e índices derivados.
- `render` aceita múltiplos renderizadores na mesma camada.
- a ordem interna dos itens em `render` importa, porque o dispatcher percorre a lista na sequência.

### Inferência controlada

- usar uma única camada com vários `render` ajuda a manter coerência entre dados, ordem temporal e campos derivados

### Não foi possível validar

- todos os formatos de arquivo aceitos por `format`, porque a camada de leitura não foi enviada completa

## Erros comuns

- esquecer `projection`
- usar `render` como objeto único em vez de lista
- usar `path` sem `temporal` ou sem uma ordem previsível
- tentar usar `scalar_field` sem disponibilizar um campo acessível em `fields` ou no runtime
