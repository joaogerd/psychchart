# `indexes`

## O que é

É a seção usada para índices calculados no domínio inteiro do gráfico, como `ITU` e `TE`.

## Para que serve

Permite desenhar índices de duas formas:

- como campo contínuo (`field`)
- como isolinhas (`isolines`)

As duas formas podem coexistir no mesmo índice.

## Parâmetros disponíveis

### Em cada item de `indexes`

- `index`
- `name` (legado)
- `label`
- `parameters`
- `levels`
- `cmap`
- `vmin`
- `vmax`
- `render`

### `render.field`

- `alpha`
- `colorbar`

### `render.isolines`

- `levels`
- `style`
- `color`
- `linewidth`
- `alpha`
- `label`
- `label_fontsize`
- `label_fmt`

## Valores aceitos

### Identificação

- `index`: texto, identificador canônico do índice
- `name`: alias legado para `index`

### Faixas e cores

- `levels`: lista de números
- `cmap`: texto com nome de colormap
- `vmin`, `vmax`: números

### `render.field`

- `alpha`: número
- `colorbar`: booleano

### `render.isolines`

- `levels`: lista de números
- `style`: texto compatível com estilo de linha do Matplotlib
- `color`: texto
- `linewidth`: número
- `alpha`: número
- `label`: booleano
- `label_fontsize`: inteiro
- `label_fmt`: texto

## Exemplo de uso

### Campo preenchido

```yaml
indexes:
  - index: ITU
    label: ITU
    levels: [0, 72, 78, 84, 90, 200]
    render:
      field:
        alpha: 0.65
        colorbar: true
```

### Campo + isolinhas

```yaml
indexes:
  - index: ITU
    label: ITU
    render:
      field:
        alpha: 0.55
        colorbar: true
      isolines:
        levels: [72, 78, 84, 90]
        style: "-"
        color: black
        linewidth: 0.4
        alpha: 0.9
        label: true
        label_fmt: "{index} = {value:.0f}"
```

## Observações importantes

### Confirmado no código

- `draw_indexes()` só desenha um índice se houver `render.field` e/ou `render.isolines`.
- em `field`, a prioridade para níveis é:
  1. `cfg.levels`
  2. `profile.levels`
  3. render contínuo sem níveis
- quando há `levels`, o campo é desenhado com `contourf`.
- quando não há `levels`, o campo usa `pcolormesh`.
- se houver profile com `labels` e o número de labels bater com o número de intervalos, a colorbar pode usar esses rótulos semânticos.
- em `isolines`, a prioridade dos níveis é:
  1. `render.isolines.levels`
  2. `cfg.levels`
  3. `profile.levels`
- labels de isolinhas usam `label_fmt` se informado; caso contrário, usam `"{index} = {value:.0f}"`.

### Compatibilidade legada confirmada

Se `render` não existir, o normalizador tenta converter campos antigos:

- `mode: isolines` ou presença de campos como `style`, `color`, `linewidth`, `label` etc. → `render.isolines`
- `mode: filled` ou presença de `colorbar` → `render.field`

### Inferência controlada

- `levels` no nível do índice pode funcionar como referência comum para campo e isolinhas, a menos que `render.isolines.levels` sobrescreva esse valor

### Não foi possível validar

- o catálogo completo de índices suportados pelo backend de cálculo não foi totalmente enviado
- o clipping físico detalhado do campo por saturação depende de funções auxiliares não totalmente disponíveis no material

## Erros comuns

- declarar o índice sem `render`
- confundir `levels` do índice com `levels` específicos das isolinhas
- usar `name` e `index` juntos sem necessidade
