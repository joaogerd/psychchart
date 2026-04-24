# `isolines` — famílias de isolinhas semânticas

## O que é

É a seção que define famílias de isolinhas como umidade relativa, entalpia, volume específico e outras famílias registradas.

## Para que serve

Serve para configurar valores de contorno e estilo visual dessas famílias.

## Parâmetros disponíveis

### Confirmado no código

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

- `name`: texto.
- `enabled`: booleano opcional.
- `values`: lista de números.
- `color`, `linestyle`, `cmap`, `label_fmt`: texto opcional.
- `linewidth`, `alpha`: número opcional.
- `labels`: booleano opcional.
- `label_fontsize`: inteiro opcional.

## Exemplo de uso

### Formato canônico dentro de `app.isolines`

```yaml
isolines:
  relative_humidity:
    values: [30, 50, 70]
    color: gray
    linestyle: "--"
    alpha: 0.5
    labels: true
    label_fontsize: 8
```

### Formato legado aceito pela normalização

```yaml
isolines:
  - name: relative_humidity
    values: [30, 50, 70]
    color: gray
```

## Observações importantes

### Confirmado no código

- O formato legado em lista é convertido para dicionário.
- Após normalização, a chave do dicionário vira o `name` canônico.
- Quando `name == relative_humidity`, os valores em `values` são normalizados para fração.
- Para `relative_humidity`, tanto `[30, 50, 70]` quanto `[0.3, 0.5, 0.7]` são aceitos.

### Não foi possível validar

- O efeito visual final de `cmap`, porque o renderer de isolinhas do gráfico principal não foi enviado.

## Erros comuns

- Esquecer `name` ao usar o formato legado em lista.
- Informar umidade relativa fora do intervalo aceito.
- Misturar porcentagem e fração sem perceber que tudo será armazenado internamente como fração.
