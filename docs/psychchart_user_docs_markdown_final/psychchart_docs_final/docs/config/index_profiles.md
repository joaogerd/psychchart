# Profiles semânticos de índices

## O que é

São perfis que definem a semântica visual padrão de alguns índices.

## Para que serve

Um profile pode fornecer, por padrão:

- `levels`
- `colors`
- `labels`
- `mode`
- `clip_to_saturation`

Isso ajuda o renderer a escolher faixas e rótulos sem precisar repetir tudo no YAML.

## Profiles confirmados nos arquivos enviados

- `ITU`
- `TE`

## Exemplo de uso indireto

Você não precisa necessariamente declarar o profile no YAML. O renderer tenta localizar o profile pelo nome do índice.

Exemplo:

```yaml
indexes:
  - index: ITU
    render:
      field:
        alpha: 0.6
        colorbar: true
```

Nesse caso, o renderer pode usar os níveis e labels semânticos de `ITU` caso você não informe outros.

## Valores confirmados

### `ITU`

- `levels`: `[0, 72, 78, 84, 90, 200]`
- 5 cores semânticas
- labels:
  - `Confort`
  - `Warning`
  - `Danger`
  - `Extreme`
  - `Fatal`

### `TE`

- `levels`: `[0, 1.5, 5.5, 11.0, 25, 200]`
- 5 cores semânticas
- labels:
  - `Comfort`
  - `Warning`
  - `Danger`
  - `Fatigue`
  - `Extreme`

## Observações importantes

### Confirmado no código

- o registry de index profiles exposto nos arquivos enviados contém `ITU` e `TE`
- os labels do profile podem ser aplicados na colorbar quando a contagem bate com o número de intervalos

### Não foi possível validar

- se existem outros profiles fora dos arquivos enviados
- se `mode` e `clip_to_saturation` já são consumidos em todos os renderizadores atuais

## Pontos que merecem atenção

- os labels de `ITU` misturam idiomas (`Confort`, `Warning`, `Danger`, etc.)
- isso não impede o uso, mas é uma inconsistência semântica de apresentação
