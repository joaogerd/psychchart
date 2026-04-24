# Profiles semânticos de isolinhas

## O que é

São perfis com defaults visuais e semânticos para famílias de isolinhas clássicas.

## Para que serve

Os profiles ajudam a definir automaticamente:

- níveis padrão
- cor
- espessura
- estilo de linha
- `alpha`
- labels
- `label_fmt`
- `zorder`
- `clip_to_saturation`

## Profiles confirmados nos arquivos enviados

- `relative_humidity`
- `enthalpy`
- `specific_volume`
- `wet_bulb`
- `moisture` / `moisture_quantity` (há inconsistência de nome; veja observações)

## Exemplo de uso indireto

```yaml
isolines:
  enthalpy: {}
```

Se o renderer conseguir resolver o profile corretamente, ele pode preencher defaults sem que você informe tudo manualmente.

## Observações importantes

### Confirmado no código

- o resolver de defaults usa primeiro o profile e depois aplica sobrescritas do usuário
- `relative_humidity` profile define níveis padrão de `0.1` até `0.9`
- `enthalpy` profile define níveis `[0, 20, 40, 60, 80, 100, 120]`
- `specific_volume` profile define níveis `[0.75, 0.80, 0.85, 0.90, 0.95]`
- `wet_bulb` profile define níveis `[0, 5, 10, 15, 20, 25, 30, 35]`

### Inconsistências importantes

Os arquivos enviados mostram divergências entre profiles e registries. Isso significa que nem todo default semântico pode estar sendo aplicado como a intenção da docstring sugere.

Casos encontrados:

- o registry de profiles usa a chave `moisture`, mas o handler trabalha com `moisture_quantity`
- o registry de profiles usa a chave `wet_bulb.py`, enquanto os handlers e configs usam `wet_bulb`
- a descrição textual do profile de `relative_humidity` fala em linha cinza tracejada, mas os valores definidos são:
  - `color = "#000000"`
  - `linestyle = "-"`
  - `alpha = 0.5`

## Erros comuns

- achar que a docstring do profile já garante o comportamento real
- confiar em defaults de profile sem verificar se a chave do registry bate com a família usada no YAML
