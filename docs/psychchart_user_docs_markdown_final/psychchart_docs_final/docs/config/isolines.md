# `isolines`

## O que é

É a seção para isolinhas psicrométricas clássicas, como:

- `relative_humidity`
- `enthalpy`
- `wet_bulb`
- `specific_volume`
- `moisture_quantity`

## Para que serve

Permite controlar níveis e estilo visual das famílias de isolinhas que estruturam a carta psicrométrica.

## Parâmetros disponíveis

- `name`
- `enabled`
- `values`
- `color`
- `linewidth`
- `linestyle`
- `alpha`
- `cmap`
- `labels`
- `label_fontsize`
- `label_fmt`

## Valores aceitos

### Obrigatórios

- `name`: texto, identificador da família

### Opcionais

- `enabled`: booleano
- `values`: lista de números
- `color`: texto
- `linewidth`: número
- `linestyle`: texto
- `alpha`: número
- `cmap`: texto
- `labels`: booleano
- `label_fontsize`: inteiro
- `label_fmt`: texto

## Exemplo de uso

```yaml
isolines:
  relative_humidity:
    values: [30, 50, 70, 90]
    color: "#444444"
    linestyle: "--"
    labels: true

  enthalpy:
    values: [20, 40, 60, 80]
    color: "#202020"
    linestyle: "-."
    linewidth: 0.6
```

## Observações importantes

### Confirmado no código

- `enabled` controla se a família é desenhada.
- a resolução de defaults mistura:
  1. valores do usuário em `IsoSet`
  2. valores do profile semântico da família
  3. defaults de segurança do renderer
- se `values` vier vazio e o profile também não fornecer valores, a família não é desenhada.
- para `relative_humidity`, `values` aceita frações ou porcentagens e normaliza para `[0, 1]`.

### Famílias confirmadas pelos handlers enviados

- `relative_humidity`
- `enthalpy`
- `wet_bulb`
- `specific_volume`
- `moisture_quantity`

### Sobre labels

- o renderer atual possui handlers específicos de label ao menos para `relative_humidity` e `enthalpy`
- outras famílias têm suporte parcial ou dependem de outra implementação enviada em paralelo

### Inferência controlada

- `cmap` existe no contrato, mas o uso efetivo depende da família e do handler

### Não foi possível validar

- o uso efetivo de `cmap` em todas as famílias
- se todas as famílias listadas no profile registry estão realmente alinhadas com o registry de handlers

## Erros comuns

- informar `relative_humidity` em porcentagem e esquecer que internamente o valor vira fração
- esperar que toda família tenha o mesmo nível de suporte a labels
- depender de `cmap` sem verificar se a família realmente o usa
