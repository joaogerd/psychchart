# `indexes` — índices calculados no gráfico

## O que é

É a seção para índices calculados sobre o domínio do gráfico, como ITU, THI e outros índices registrados no runtime.

## Para que serve

Serve para declarar qual índice será calculado e como ele poderá ser exibido, principalmente como campo contínuo e/ou isolinhas.

## Parâmetros disponíveis

## Seção `indexes[]`

### O que é

Uma definição de índice calculado.

### Para que serve

Serve para identificar o índice, passar parâmetros e configurar sua renderização.

### Parâmetros disponíveis

### Confirmado no código

- `index`: identificador canônico.
- `name`: alias legado.
- `label`: rótulo humano.
- `parameters`: dicionário de parâmetros.
- `levels`: níveis explícitos.
- `cmap`: mapa de cores.
- `vmin`: mínimo de normalização.
- `vmax`: máximo de normalização.
- `render`: bloco de renderização.

### Valores aceitos

- `index`, `name`, `label`, `cmap`: texto.
- `parameters`: objeto.
- `levels`: lista de números.
- `vmin`, `vmax`: números.
- `render`: objeto.

### Exemplo de uso

```yaml
indexes:
  - index: ITU
    label: ITU
    levels: [72, 78, 84]
    cmap: Spectral_r
    vmin: 68
    vmax: 95
    render:
      field:
        alpha: 0.65
        colorbar: true
      isolines:
        levels: [72, 78, 84]
        style: "-"
        color: black
        linewidth: 0.5
        alpha: 0.8
        label: true
        label_fontsize: 8
        label_fmt: "{index} = {value:.0f}"
```

### Observações importantes

### Confirmado no código

- `name` ainda é aceito por compatibilidade, mas é promovido para `index`.
- O modelo de índice aceita chaves extras (`extra="allow"`) para compatibilidade com formatos antigos.
- O índice é inválido se nem `index` nem `name` forem fornecidos.

### Não foi possível validar

- O efeito visual exato de `cmap`, `vmin`, `vmax` e `levels` no renderer de índices, porque o arquivo de plotagem de índices não foi enviado.

### Erros comuns

- Definir um índice sem `index` e sem `name`.
- Misturar chaves legadas e modernas assumindo que todas terão efeito visual confirmado.

---

## Seção `render.field`

### O que é

Configuração de campo contínuo para um índice calculado.

### Para que serve

Serve para pedir uma representação preenchida/contínua do índice.

### Parâmetros disponíveis

### Confirmado no código

- `alpha`
- `colorbar`

### Valores aceitos

- `alpha`: número opcional.
- `colorbar`: booleano opcional.

### Exemplo de uso

```yaml
render:
  field:
    alpha: 0.6
    colorbar: true
```

### Observações importantes

### Não foi possível validar

- Como o renderer de índices usa `alpha` e `colorbar`, porque esse renderer não foi enviado.

### Erros comuns

- Assumir que o simples fato de declarar `field` garante o desenho sem que o backend do índice exista no runtime.

---

## Seção `render.isolines`

### O que é

Configuração de isolinhas para um índice calculado.

### Para que serve

Serve para desenhar contornos em níveis específicos do índice.

### Parâmetros disponíveis

### Confirmado no código

- `levels`
- `style`
- `color`
- `linewidth`
- `alpha`
- `label`
- `label_fontsize`
- `label_fmt`

### Valores aceitos

- `levels`: lista de números.
- `style`, `color`, `label_fmt`: texto opcional.
- `linewidth`, `alpha`: números opcionais.
- `label`: booleano opcional.
- `label_fontsize`: inteiro opcional.

### Exemplo de uso

```yaml
render:
  isolines:
    levels: [72, 78, 84]
    style: ":"
    color: black
    linewidth: 0.4
    alpha: 0.8
    label: true
    label_fontsize: 8
    label_fmt: "{index} = {value:.0f}"
```

### Observações importantes

### Confirmado no código

- O bloco `render` aceita somente `field`, somente `isolines` ou ambos.

### Não foi possível validar

- O conjunto real de placeholders aceitos em `label_fmt` pelo renderer de índices.

### Erros comuns

- Declarar `levels` em um lugar e esperar que outro bloco use automaticamente esses níveis.
