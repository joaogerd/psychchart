# Pontos que precisam de esclarecimento

Esta seção reúne inconsistências, lacunas ou comportamentos que **não** puderam ser fechados com segurança apenas com os arquivos enviados.

## 1. Renderer de índices não foi enviado

Os arquivos de configuração de `indexes` existem e são claros, mas o renderer correspondente não foi enviado. Por isso, não foi possível confirmar:

- como `cmap`, `vmin`, `vmax` e `levels` atuam visualmente
- como `label_fmt` é aplicado nas isolinhas de índice
- como `field` e `isolines` convivem na prática

## 2. Grade auxiliar de `chart` não pôde ser validada em execução

Os campos abaixo existem em `ChartConfig`, mas o comportamento real de desenho não aparece nos arquivos enviados:

- `show_tw_grid`
- `tw_grid`
- `tw_grid_style`
- `style`
- `grid`

## 3. `normalize` em `density` existe, mas a implementação não foi enviada

O parâmetro `normalize` está presente tanto no contrato legado quanto no contrato canônico de densidade, porém a função que calcula a densidade (`to_density_field`) não foi enviada. Então não foi possível confirmar:

- se a normalização é por soma, máximo, área, frequência relativa ou outra regra
- em que ponto do pipeline ela ocorre

## 4. Inconsistência entre template legado de overlay e template canônico de anotação

Há uma inconsistência importante:

- no modelo legado de `temporal_overlays`, a documentação sugere templates como `{time}h\n(CTA:{cta:.0f})`
- no renderizador canônico `annotate`, os placeholders realmente disponíveis são `time` e `value`

Isso significa que um usuário pode escrever `{cta}` e esperar que funcione, mas o renderer enviado não mostra suporte a essa chave.

## 5. `show_legend` e `legend_loc` aparecem no modelo legado, mas não no fluxo enviado

Os campos existem em `TemporalOverlayConfig`, porém nos arquivos enviados:

- não aparecem na conversão para `data_layers`
- não aparecem nos renderizadores enviados

Então não foi possível confirmar se hoje eles têm efeito prático.

## 6. `type` do overlay legado existe, mas não teve uso confirmado

`TemporalOverlayConfig` exige `type`, mas o conversor legado enviado não usa esse campo para montar `data_layers`. Pode haver uso em outra parte do projeto, mas isso não apareceu no material enviado.

## 7. `paths.py` define `PathConfig`, mas não há seção top-level correspondente em `AppConfig`

Foi enviado um arquivo com um modelo `PathConfig` para trajetórias declarativas. Porém, nos arquivos de configuração raiz enviados, não existe uma seção top-level como `paths:` dentro de `AppConfig`.

Então não foi possível validar:

- se esse modelo ainda é usado
- se é usado por outro loader
- se foi substituído na prática por `data_layers + render: path`

## 8. Exemplo inconsistente em `ObservationsConfig`

A docstring de `ObservationsConfig` mostra um exemplo com:

- `data="observations.csv"`
- `t_col="T"`
- `rh_col="RH"`

Mas os campos reais do modelo são:

- `file`
- `format`
- `data_indexes`
- `density`

Ou seja, o exemplo da docstring não bate com o modelo validado mostrado no código.

## 9. Conversão automática de `observations` assume colunas `T` e `RH`

Na promoção automática de `observations` para `data_layers`, o código fixa:

- `t_col: T`
- `rh_col: RH`

Não foi possível validar se isso é uma convenção geral obrigatória do projeto ou apenas uma suposição de compatibilidade do conversor legado.

## 10. Há um ramo redundante em `AppConfig.normalize_legacy_shapes`

Depois do bloco `if raw_data_layers is None:`, aparece um `elif raw_data_layers is None:`. Esse segundo ramo é redundante/inatingível no trecho enviado. Isso não afeta diretamente a documentação de usuário, mas é um sinal de que essa parte merece revisão no código.
