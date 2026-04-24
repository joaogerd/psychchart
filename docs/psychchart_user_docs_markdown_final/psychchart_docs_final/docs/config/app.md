# `AppConfig`

## O que é

É a configuração raiz do projeto. Ela junta as seções principais do gráfico e normaliza formatos legados antes da validação final.

## Para que serve

Serve para montar a estrutura completa do gráfico em um único YAML, com suporte ao formato canônico atual e a algumas entradas antigas.

## Parâmetros disponíveis

### Seções principais

- `chart`
- `isolines`
- `zones`
- `points`
- `indexes`
- `index_zones`
- `data_layers`

### Seções legadas aceitas

- `observations`
- `temporal_overlays`

## Valores aceitos

### `chart`
Bloco obrigatório com a configuração do gráfico.

### `isolines`
Dicionário de famílias de isolinhas. Também pode vir em formato legado de lista, desde que cada item tenha `name`.

### `zones`
Lista de zonas geométricas.

### `points`
Lista de pontos de referência.

### `indexes`
Lista de índices calculados no domínio do gráfico.

### `index_zones`
Lista de zonas baseadas em faixas de índice.

### `data_layers`
Lista de camadas baseadas em arquivo tabular. Este é o formato canônico atual.

### `observations`
Lista legada de datasets observacionais.

### `temporal_overlays`
Lista legada de overlays temporais.

## Exemplo de uso

```yaml
chart:
  t_min: 10
  t_max: 40
  pressure: 101325
  xlabel: "Temperatura de bulbo seco (°C)"
  ylabel: "Razão de umidade (kg/kg)"
  output: "chart.png"
  dpi: 150

isolines:
  relative_humidity:
    values: [30, 50, 70]

points:
  - t: 25
    rh: 60
    label: "Referência"

data_layers:
  - data: "animal_day.csv"
    format: "csv"
    projection:
      t_col: temp
      rh_col: rh
    render:
      - type: points
```

## Observações importantes

### Confirmado no código

- `data_layers` é o formato canônico atual.
- `observations` e `temporal_overlays` podem ser promovidos para `data_layers` quando `data_layers` não é fornecido.
- `isolines` em formato de lista legado é convertido para dicionário.
- em `indexes`, o alias legado `name` pode ser convertido para `index`.
- alguns campos legados de renderização de `indexes` são convertidos para o bloco moderno `render`.

### Conversões legadas confirmadas

#### `observations` → `data_layers`

A promoção automática:

- usa `file` como origem do dataset
- usa `format` com default `parquet`
- fixa `projection.t_col = T`
- fixa `projection.rh_col = RH`
- converte `data_indexes` em `fields` e `render`
- converte `density` em `render: density`

#### `temporal_overlays` → `data_layers`

A promoção automática:

- usa `data` como arquivo
- força `format: csv`
- cria `temporal.time_col`
- cria um campo direto chamado `CTA`
- monta `render` com `path`, `scatter` e `annotate`

## Erros comuns

- usar `observations` esperando que ele continue independente de `data_layers`
- misturar `name` e `index` em `indexes` sem saber qual forma está em uso
- esquecer que a promoção automática de `observations` assume colunas `T` e `RH`
- fornecer `isolines` como lista sem `name`

## Não foi possível validar

- se o projeto ainda possui outros loaders externos além desse fluxo
- se todas as entradas legadas continuam sendo usadas em outras partes não enviadas
