# `app` — configuração raiz

## O que é

É a configuração principal validada do projeto. Ela reúne as seções de gráfico, isolinhas, zonas, pontos, índices e camadas de dados.

## Para que serve

Serve como documento único de entrada da aplicação. É também o ponto onde formatos antigos são normalizados para o formato atual.

## Parâmetros disponíveis

### Confirmado no código

- `chart`: configuração do gráfico.
- `isolines`: famílias de isolinhas.
- `zones`: zonas geométricas.
- `points`: pontos de referência.
- `indexes`: índices calculados.
- `index_zones`: zonas definidas por intervalo de índice.
- `data_layers`: formato canônico atual para camadas baseadas em dados.
- `observations`: formato legado.
- `temporal_overlays`: formato legado.

## Valores aceitos

### Confirmado no código

- `chart`: objeto.
- `isolines`: dicionário.
- `zones`: lista.
- `points`: lista.
- `indexes`: lista.
- `index_zones`: lista.
- `data_layers`: lista.
- `observations`: lista.
- `temporal_overlays`: lista.

## Exemplo de uso

```yaml
chart:
  t_min: 0
  t_max: 40
  pressure: 101325
  xlabel: "Temperatura"
  ylabel: "Razão de umidade"
  output: "chart.png"
  dpi: 150

data_layers:
  - data: "animal_day.csv"
    format: "csv"
    projection:
      t_col: "temp"
      rh_col: "rh"
      rh_unit: auto
    render:
      - type: points
```

## Observações importantes

### Confirmado no código

- `data_layers` é o formato canônico exposto para o runtime.
- Se `data_layers` **não** for fornecido, o sistema tenta sintetizá-lo a partir de `observations` e `temporal_overlays`.
- `isolines` pode entrar em formato de lista legado e é convertido para dicionário, usando `name` como chave.
- Em `indexes`, o campo legado `name` é promovido para `index`.
- Campos legados de renderização de índice podem ser convertidos para `render.field` ou `render.isolines`.

### Inferência controlada

- Para uso novo, faz mais sentido escrever YAML diretamente em `data_layers` e tratar `observations` e `temporal_overlays` apenas como compatibilidade.

## Erros comuns

- Usar `isolines` com tipo diferente de dicionário ou lista.
- Colocar entradas de `indexes`, `observations` ou `temporal_overlays` que não sejam objetos/mapeamentos.
- Esperar que `observations` e `temporal_overlays` continuem aparecendo no payload canônico: a saída consolidada passa a ser `data_layers`.
