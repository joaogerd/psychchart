# Render `annotate`

## O que é

Desenha anotações periódicas sobre uma camada baseada em dados.

## Para que serve

Serve para rotular pontos ao longo de uma trajetória ou série ordenada, mostrando tempo, valor ou outra informação resumida.

## Parâmetros disponíveis

- `type`
- `every`
- `template`
- `time_field`
- `value_field`
- `dx`
- `dy`
- `fontsize`
- `fontweight`
- `color`
- `zorder`

## Valores aceitos

- `type`: `annotate`
- `every`: inteiro
- `template`: texto
- `time_field`: texto
- `value_field`: texto
- `dx`, `dy`: número
- `fontsize`: número
- `fontweight`: texto
- `color`: texto
- `zorder`: inteiro

## Exemplo de uso

```yaml
render:
  - type: annotate
    every: 3
    template: "{time}h\nCTA={value:.0f}"
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

- se `every <= 0`, nada é desenhado
- a ordenação tenta usar `layer.config.temporal.time_col` quando existir
- os placeholders realmente montados no contexto são:
  - `time`
  - `value`
- o texto é desenhado em `row["_T"] + dx` e `row["_W"] + dy`

### Inconsistência importante

- o modelo legado de `temporal_overlays` documenta template com `{cta}`
- o renderizador canônico `annotate` usa `value`, não `cta`

Então, no formato canônico, o template mais seguro é algo como:

```yaml
template: "{time}h\nCTA={value:.0f}"
```

## Erros comuns

- usar `{cta}` diretamente em `data_layers`
- usar `time_field` ou `value_field` com nomes que o layer não resolve
