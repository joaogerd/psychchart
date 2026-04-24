# Documentação de usuário do `psychchart`

Esta documentação foi montada **somente** com base nos arquivos enviados nesta conversa, incluindo:

- modelos de configuração
- renderizadores de `data_layers`
- partes do pipeline de plot (`core`, `indexes`, `zones`, `density`, `temporal`, `layers`)
- profiles semânticos de `indexes` e `isolines`

## Como interpretar a confiabilidade da informação

Ao longo dos arquivos, cada assunto é tratado com três níveis de segurança:

- **Confirmado no código**: aparece claramente nos modelos, nos renderizadores ou no pipeline enviado.
- **Inferência controlada**: é uma conclusão razoável a partir do fluxo do código, mas sem validação completa de todas as camadas.
- **Não foi possível validar**: existe no contrato ou na docstring, mas o material enviado não mostra o efeito final com segurança.

## Estrutura desta documentação

### Configuração

- `config/app.md`
- `config/chart.md`
- `config/data_layers.md`
- `config/indexes.md`
- `config/index_profiles.md`
- `config/isolines.md`
- `config/isoline_profiles.md`
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

### Pipeline de plot

- `plot/rendering_pipeline.md`

### Lacunas e inconsistências

- `PONTOS_QUE_PRECISAM_DE_ESCLARECIMENTO.md`

## Leitura rápida

Pelo que está **confirmado**, o formato **canônico atual** para camadas baseadas em dados é `data_layers`.

As seções legadas `observations` e `temporal_overlays` ainda podem ser aceitas como entrada, mas são convertidas para `data_layers` quando `data_layers` não é fornecido explicitamente.

Na prática, o fluxo atual mais seguro para o usuário é:

1. definir `chart`
2. definir `isolines`, `zones`, `points`, `indexes` e `index_zones` quando necessário
3. usar `data_layers` para tudo que vem de arquivo tabular
4. dentro de cada `data_layer`, configurar:
   - `data` e `format`
   - `projection`
   - `temporal` quando houver ordem temporal
   - `fields` quando precisar expor colunas ou índices derivados
   - `render` com um ou mais tipos de renderização

Também ficou **confirmado** no `core` que a ordem de desenho favorece:

- fundos contínuos primeiro
- depois `data_layers`
- depois curva de saturação
- depois zonas, isolinhas e pontos
- por último a formatação do eixo
