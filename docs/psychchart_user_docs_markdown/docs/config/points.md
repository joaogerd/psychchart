# `points` — pontos de referência no gráfico

## O que é

É a seção para pontos individuais com temperatura, umidade relativa e rótulo opcional.

## Para que serve

Serve para destacar estados específicos no gráfico, como referências, medições pontuais ou marcos visuais.

## Parâmetros disponíveis

### Confirmado no código

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

- `t`: número.
- `rh`: número.
- `label`, `marker`, `color`: texto opcional.
- `size`, `alpha`: número.
- `zorder`: inteiro.
- `show_label`: booleano.

## Exemplo de uso

```yaml
points:
  - t: 25.0
    rh: 65
    label: "Referência"
    marker: o
    color: red
    size: 30
    alpha: 0.9
    zorder: 10
    show_label: true
```

## Observações importantes

### Confirmado no código

- `rh` aceita fração (`0.65`) ou porcentagem (`65`) e é normalizada internamente para fração.
- `show_label` apenas controla a intenção declarada de mostrar rótulo.

### Não foi possível validar

- A lógica final de posicionamento e exibição do rótulo, porque o renderer desses pontos de configuração não foi enviado.

## Erros comuns

- Informar `rh` fora do intervalo físico.
- Escrever `rh: 1.2` achando que significa `120%` ou fração inválida: pela regra do projeto, isso é interpretado como `1.2%`.
