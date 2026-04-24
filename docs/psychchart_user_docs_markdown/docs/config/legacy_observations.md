# `observations` — formato legado para dados observacionais

## O que é

É o formato legado para datasets observacionais. Ele ainda é aceito, mas pode ser convertido automaticamente para `data_layers`.

## Para que serve

Serve para descrever um arquivo observacional, opcionalmente com densidade e índices de dados.

## Parâmetros disponíveis

## Seção `observations[]`

### Confirmado no código

- `file`
- `format` (padrão: `parquet`)
- `data_indexes`
- `density`

## Valores aceitos

- `file`: texto.
- `format`: texto.
- `data_indexes`: lista.
- `density`: objeto opcional.

## Exemplo de uso

```yaml
observations:
  - file: "data/animals.parquet"
    format: parquet
    data_indexes:
      - index: CTA
        scatter: true
        scalar_field: false
        cmap: viridis
        alpha: 0.6
        colorbar: true
    density:
      bins: [80, 80]
      cmap: magma
      alpha: 0.5
      colorbar: true
      normalize: true
```

## Observações importantes

### Confirmado no código

- Quando `data_layers` não é fornecido, `observations` é convertido para `data_layers`.
- Na conversão automática:
  - `file` vira `data`
  - `format` é preservado
  - a projeção é fixada em `t_col: T`, `rh_col: RH`, `rh_unit: auto`
  - cada `data_index` vira um campo e um ou mais blocos de `render`
  - `density` vira um `render` do tipo `density`
- Se o `data_index.index` for `ICF`, a conversão cria um campo `data_index` com `source_col: behavior`.
- Para outros índices, a conversão assume que já existe uma coluna com o mesmo nome do índice.

### Não foi possível validar

- Se todos os arquivos observacionais reais do projeto usam mesmo `T` e `RH` como nomes de coluna. Isso é apenas o que a conversão automática assume.

## Erros comuns

- Usar nomes de coluna diferentes de `T` e `RH` e esperar que a conversão automática descubra isso sozinha.
- Esperar que `observations` seja o formato preferido atual.

---

## Seção `data_indexes[]`

## O que é

Define como uma variável escalar do dataset observacional deve ser exibida.

## Para que serve

Serve para pedir scatter, campo escalar ou ambos para uma variável associada ao dataset.

## Parâmetros disponíveis

### Confirmado no código

- `index`
- `scatter` (padrão: `true`)
- `scalar_field` (padrão: `false`)
- `bins`
- `cmap`
- `alpha`
- `colorbar`

## Valores aceitos

- `index`: texto.
- `scatter`, `scalar_field`, `colorbar`: booleano.
- `bins`: par numérico inteiro.
- `cmap`: texto.
- `alpha`: número.

## Exemplo de uso

```yaml
data_indexes:
  - index: CTA
    scatter: true
    scalar_field: true
    bins: [50, 50]
    cmap: plasma
    alpha: 0.6
    colorbar: true
```

## Observações importantes

### Confirmado no código

- `scatter` e `scalar_field` são independentes.
- É possível pedir apenas scatter, apenas campo escalar ou ambos.

## Erros comuns

- Esperar que `index` calcule um valor novo sem existir backend ou coluna correspondente.

---

## Seção `density`

## O que é

Resumo de densidade do dataset observacional.

## Para que serve

Serve para transformar nuvem de pontos em campo 2D de densidade.

## Parâmetros disponíveis

### Confirmado no código

- `bins`
- `cmap`
- `vmin`
- `vmax`
- `alpha`
- `colorbar`
- `normalize`

## Valores aceitos

- `bins`: par de inteiros.
- `cmap`: texto.
- `vmin`, `vmax`: números opcionais.
- `alpha`: número.
- `colorbar`, `normalize`: booleanos.

## Exemplo de uso

```yaml
density:
  bins: [60, 60]
  cmap: viridis
  alpha: 0.6
  colorbar: true
  normalize: true
```

## Observações importantes

### Confirmado no código

- `normalize` existe no contrato.

### Não foi possível validar

- O significado matemático exato de `normalize`, porque a implementação de `to_density_field` não foi enviada.
