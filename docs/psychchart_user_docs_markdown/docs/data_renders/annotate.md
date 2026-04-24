# `render: { type: annotate }`

## O que é

Anotações textuais periódicas ao longo de uma camada ordenada.

## Para que serve

Serve para rotular pontos específicos da sequência, como tempo, valor acumulado ou outro campo relevante.

## Parâmetros disponíveis

### Confirmado no código

- `type`: deve ser `annotate`.
- `every`: intervalo de anotação em número de pontos. Padrão: `3`.
- `template`: texto-base da anotação. Padrão: `"{time}"`.
- `time_field`: campo/coluna usado para preencher `time`.
- `value_field`: campo/coluna usado para preencher `value`.
- `dx`: deslocamento horizontal. Padrão: `0.35`.
- `dy`: deslocamento vertical. Padrão: `0.0005`.
- `fontsize`: tamanho da fonte. Padrão: `8.0`.
- `fontweight`: peso da fonte. Padrão: `bold`.
- `color`: cor do texto. Padrão: `black`.
- `zorder`: ordem de desenho. Padrão: `30`.

## Valores aceitos

- `every`: inteiro.
- `template`, `time_field`, `value_field`, `fontweight`, `color`: texto.
- `dx`, `dy`, `fontsize`: número.
- `zorder`: inteiro.

## Exemplo de uso

```yaml
render:
  - type: annotate
    every: 3
    template: "{time}h\n(CTA:{value:.0f})"
    time_field: hour
    value_field: CTA
    dx: 0.35
    dy: 0.0005
    fontsize: 8
    fontweight: bold
    color: black
```

## Observações importantes

### Confirmado no código

- Se `every <= 0`, nada é desenhado.
- O renderer preenche o template com exatamente duas chaves de contexto: `time` e `value`.
- Se houver `temporal` na camada, a ordenação usada para anotar segue `temporal.time_col`.
- Os textos são posicionados em `row["_T"] + dx` e `row["_W"] + dy`.

### Confirmado no código, mas importante

- O template **não** é preenchido automaticamente com qualquer nome de coluna. O renderer cria somente `time` e `value`.

## Erros comuns

- Usar placeholders como `{cta}` ou `{CTA}` achando que funcionarão automaticamente.
- Esperar anotação em todos os pontos com `every: 3`.
- Usar `every: 0` ou valor negativo sem perceber que isso desativa o desenho.
