# Documentação de usuário do `psychchart`

Esta documentação foi gerada **somente** a partir dos arquivos enviados sobre configuração (`config`) e renderização de camadas de dados (`data_renders`).

## Como ler esta documentação

Ao longo dos arquivos, eu separo a confiabilidade da informação em três níveis:

- **Confirmado no código**: comportamento, parâmetro ou valor que aparece claramente nos arquivos enviados.
- **Inferência controlada**: conclusão provável a partir do nome do parâmetro, docstring ou fluxo de conversão, mas sem o trecho final de execução que comprove totalmente o efeito visual.
- **Não foi possível validar**: o parâmetro existe, mas os arquivos enviados não mostram como ele é realmente usado em tempo de execução.

## Organização

### Configuração principal

- `config/app.md`
- `config/chart.md`
- `config/data_layers.md`
- `config/indexes.md`
- `config/isolines.md`
- `config/points.md`
- `config/zones.md`
- `config/legacy_observations.md`
- `config/legacy_temporal_overlays.md`

### Renderizadores de `data_layers`

- `data_renders/points.md`
- `data_renders/scatter.md`
- `data_renders/density.md`
- `data_renders/scalar_field.md`
- `data_renders/path.md`
- `data_renders/annotate.md`

### Lacunas e inconsistências

- `PONTOS_QUE_PRECISAM_DE_ESCLARECIMENTO.md`

## Visão geral rápida

Pelo que está confirmado nos arquivos enviados, o formato **canônico e atual** para camadas baseadas em dados é `data_layers`. As seções legadas `observations` e `temporal_overlays` ainda são aceitas, mas são convertidas automaticamente para `data_layers` quando `data_layers` não é fornecido explicitamente.

Isso significa que, para documentação de uso atual, o ponto principal é:

1. definir `chart`
2. definir `data_layers`
3. dentro de cada `data_layer`, configurar:
   - origem do arquivo (`data`, `format`)
   - projeção (`projection`)
   - ordenação temporal opcional (`temporal`)
   - campos derivados opcionais (`fields`)
   - uma ou mais saídas visuais (`render`)
