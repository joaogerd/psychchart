# `chart` — configuração geral do gráfico

## O que é

É a seção que define os limites do gráfico, a pressão de referência, os rótulos, o arquivo de saída e algumas opções gerais de exibição.

## Para que serve

Serve para controlar a área visível do diagrama psicrométrico e a exportação da figura.

## Parâmetros disponíveis

### Confirmado no código

- `t_min`: limite mínimo de temperatura.
- `t_max`: limite máximo de temperatura.
- `y_min`: limite mínimo do eixo Y.
- `y_max`: limite máximo do eixo Y.
- `pressure`: pressão de referência.
- `xlabel`: rótulo do eixo X.
- `ylabel`: rótulo do eixo Y.
- `title`: título opcional.
- `output`: nome ou caminho do arquivo de saída.
- `dpi`: resolução da saída.
- `style`: estilo opcional.
- `grid`: grade padrão opcional.
- `figsize`: tamanho da figura.
- `show_tw_grid`: ativa/desativa uma grade auxiliar T × W.
- `tw_grid`: opções comportamentais da grade auxiliar.
- `tw_grid_style`: opções visuais da grade auxiliar.

## Valores aceitos

### Confirmado no código

- `t_min`, `t_max`, `pressure`: números.
- `y_min`, `y_max`, `title`, `style`, `grid`: opcionais.
- `xlabel`, `ylabel`, `output`: texto.
- `dpi`: inteiro.
- `figsize`: par de números.
- `show_tw_grid`: booleano.
- `tw_grid`, `tw_grid_style`: objetos.

## Exemplo de uso

```yaml
chart:
  t_min: 10
  t_max: 45
  y_min: 0.0
  y_max: 0.035
  pressure: 101325
  xlabel: "Temperatura de bulbo seco (°C)"
  ylabel: "Razão de umidade (kg/kg)"
  title: "Exposição térmica"
  output: "psychchart.png"
  dpi: 200
  figsize: [16, 8]
  show_tw_grid: true
  tw_grid:
    x_step: 2
    y_step: 0.002
  tw_grid_style:
    alpha: 0.3
    linewidth: 0.5
```

## Observações importantes

### Confirmado no código

- `t_min`, `t_max` e `pressure` são obrigatórios.
- `y_min` e `y_max` são opcionais.
- `show_tw_grid`, `tw_grid` e `tw_grid_style` existem como contrato de configuração.

### Não foi possível validar

- O efeito visual exato de `style`, `grid`, `show_tw_grid`, `tw_grid` e `tw_grid_style` não pôde ser confirmado, porque os arquivos de plotagem do gráfico principal não foram enviados.

## Erros comuns

- Esquecer `pressure`.
- Informar `figsize` fora do formato de par numérico.
- Assumir que qualquer chave arbitrária será aceita: a configuração base do projeto é estrita e rejeita campos desconhecidos.
