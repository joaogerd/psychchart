# `points`

## O que é

É a seção de pontos de referência desenhados diretamente no gráfico.

## Para que serve

Serve para marcar estados específicos, como:

- condição de referência
- medição pontual
- ponto de projeto
- valor observado importante

## Parâmetros disponíveis

- `t`
- `rh`
- `label`
- `marker`
- `color`
- `size`
- `alpha`
- `zorder`
- `show_label`

## Valores aceitos

- `t`: número
- `rh`: número em fração ou porcentagem
- `label`: texto
- `marker`: texto compatível com Matplotlib
- `color`: texto
- `size`: número
- `alpha`: número
- `zorder`: inteiro
- `show_label`: booleano

## Exemplo de uso

```yaml
points:
  - t: 25
    rh: 60
    label: "Referência"
    marker: "o"
    color: "red"
    size: 35
    alpha: 0.9
    zorder: 6
    show_label: true
```

## Observações importantes

### Confirmado no código

- `rh` aceita fração ou porcentagem e é normalizado para fração
- o `draw()` do gráfico converte o ponto de `(T, RH)` para `(T, W)` antes de desenhar
- se `show_label` for `true` e `label` existir, o texto é desenhado com `annotate`

### Inferência controlada

- pontos com `zorder` alto tendem a aparecer acima de muitas outras camadas

## Erros comuns

- esquecer que `rh: 60` vira `0.60` internamente
- achar que `label` sozinho já garante exibição quando `show_label` estiver desligado
