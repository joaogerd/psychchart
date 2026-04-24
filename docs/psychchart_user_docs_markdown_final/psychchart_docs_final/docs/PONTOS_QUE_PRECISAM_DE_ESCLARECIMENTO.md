# Pontos que precisam de esclarecimento

## 1. `data_layers` é o formato atual, mas ainda existe bastante código legado ao redor

O material enviado confirma que o fluxo atual mais consistente é `AppConfig -> data_layers -> draw_data_layers()`. Mesmo assim, ainda há artefatos legados espalhados pelo código.

### Confirmado

- `AppConfig.to_runtime_payload()` envia `data_layers`, mas não envia `observations` nem `temporal_overlays`.
- `draw()` do `PsychChart` chama `draw_data_layers()`.

## 2. `paths` e outras estruturas antigas aparecem em runtime, mas não entram pelo payload canônico

O `PsychChart` aceita atributos como `paths` e `density_fields`, mas o payload canônico montado por `AppConfig` não os envia.

### Confirmado

- `to_runtime_payload()` envia `cfg`, `isolines`, `zones`, `points`, `indexes`, `index_zones` e `data_layers`
- não envia `paths`
- não envia `density_fields`

### Consequência prática

Para documentação de usuário, o caminho mais seguro continua sendo:

- `data_layers + render: path`
- `data_layers + render: density`

e não as APIs antigas de runtime.

## 3. O `draw()` atual não chama o renderer de `paths` top-level

Foi enviado um renderer específico para `chart.paths`, mas o `draw()` consolidado enviado não o chama.

### Confirmado

A ordem atual chama:

- `draw_density_field`
- `draw_indexes`
- `draw_index_zones`
- `draw_data_layers`
- curva de saturação
- `draw_zones`
- `draw_isolines`
- `_draw_points`

Não aparece chamada para `draw_paths(chart.paths)`.

## 4. Há inconsistências reais entre profiles de isolinhas e seus registries

Este é um dos pontos mais importantes encontrados.

### Confirmado

No material enviado:

- o registry de profiles usa `moisture`, mas os handlers trabalham com `moisture_quantity`
- o registry de profiles usa `wet_bulb.py`, mas o restante do sistema usa `wet_bulb`

### Consequência prática

Alguns defaults semânticos de isolinhas podem não estar sendo resolvidos como a intenção da docstring sugere.

## 5. Também há inconsistência de namespace/import entre implementações de isolinhas

### Confirmado

Os arquivos enviados mostram variantes como:

- `psychchart.plot.isolines.profiles`
- `psychchart.plot.isoline_profiles`

Isso sugere transição ou coexistência de versões internas.

## 6. O profile de `relative_humidity` contradiz sua própria descrição textual

### Confirmado

A descrição fala em:

- curvas tracejadas
- cinza claro

Mas os valores definidos no profile são:

- `color="#000000"`
- `linestyle="-"`

## 7. O template legado de overlay usa `{cta}`, mas o renderer canônico usa `{value}`

### Confirmado

- `TemporalOverlayConfig` documenta `annotation_template` com `{cta}`
- o renderizador canônico `annotate` só constrói `time` e `value`

### Consequência prática

No formato canônico `data_layers`, não é seguro documentar `{cta}` como placeholder padrão.

## 8. `show_legend` e `legend_loc` existem no modelo legado, mas não entram no fluxo canônico

### Confirmado

Esses campos existem em `TemporalOverlayConfig`, e existe um renderer temporal legado com legenda refinada.

### Não foi possível validar

- se isso ainda participa do caminho principal do projeto
- se o usuário final ainda deve depender desse fluxo no estado atual

## 9. `tw_grid` existe no contrato, mas o uso direto dele não ficou demonstrado no `core`

### Confirmado

No `core` enviado, o desenho da grade usa:

- `show_tw_grid`
- `tw_grid_style`

### Não foi possível validar

- uso direto de chaves internas de `tw_grid`

## 10. `grid` existe em `ChartConfig`, mas não aparece no `core` consolidado

### Confirmado

O campo existe no modelo.

### Não foi possível validar

- qualquer efeito real dele no pipeline atual enviado

## 11. `output` e `dpi` existem no contrato, mas `draw()` não salva arquivo

### Confirmado

O próprio `draw()` deixa claro que:

- não chama `savefig()`
- não chama `plt.show()`

### Consequência prática

`output` e `dpi` devem ser tratados como metadados/configuração de exportação, e não como garantia de salvamento automático no `draw()`.

## 12. `normalize` em `density` continua sem semântica fechada

### Confirmado

- o contrato aceita `normalize`
- o renderizador passa `cfg` para a construção da densidade

### Não foi possível validar

- se a normalização é por soma, frequência relativa, máximo, área ou outra convenção

## 13. Há sinais de coexistência entre versão antiga e versão nova do sistema de plot

### Confirmado

Os arquivos mostram:

- caminho canônico com `data_layers`
- renderizadores legados de observações e overlays temporais
- duplicidade de alguns arquivos enviados em momentos diferentes
- importações e registries que apontam para variantes internas

### Consequência prática

A documentação de usuário deve privilegiar:

- `AppConfig`
- `chart`
- `isolines`
- `zones`
- `points`
- `indexes`
- `index_zones`
- `data_layers`

e tratar o resto como compatibilidade ou transição.
