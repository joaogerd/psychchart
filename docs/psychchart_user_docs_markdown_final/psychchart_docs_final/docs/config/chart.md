# `chart`

## O que é

É o bloco com as opções globais do gráfico psicrométrico.

## Para que serve

Define:

- domínio visível
- pressão de referência
- textos do gráfico
- tamanho da figura
- parte da grade auxiliar
- metadados de exportação

## Parâmetros disponíveis

- `t_min`
- `t_max`
- `y_min`
- `y_max`
- `pressure`
- `xlabel`
- `ylabel`
- `title`
- `output`
- `dpi`
- `style`
- `grid`
- `figsize`
- `show_tw_grid`
- `tw_grid`
- `tw_grid_style`

## Valores aceitos

### Obrigatórios

- `t_min`: número
- `t_max`: número
- `pressure`: número
- `xlabel`: texto
- `ylabel`: texto
- `output`: texto
- `dpi`: inteiro

### Opcionais

- `y_min`: número
- `y_max`: número
- `title`: texto
- `style`: texto
- `grid`: booleano
- `figsize`: tupla/lista com dois números
- `show_tw_grid`: booleano
- `tw_grid`: dicionário
- `tw_grid_style`: dicionário

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
  title: "Carta psicrométrica"
  output: "psychchart.png"
  dpi: 200
  style: "default"
  show_tw_grid: true
  tw_grid_style:
    alpha: 0.3
    linewidth: 0.5
    linestyle: ":"
```

## Observações importantes

### Confirmado no código

- `style` é aplicado antes da criação da figura.
- o gráfico move o eixo Y para a direita.
- `t_min` e `t_max` são aplicados como limite do eixo X.
- `y_min` e `y_max` são aplicados se algum deles estiver definido.
- `show_tw_grid` controla o desenho da grade auxiliar `T × W`.
- `tw_grid_style` é usado no desenho real da grade auxiliar.
- a grade auxiliar segue os ticks atuais do eixo.
- as linhas da grade são cortadas pela curva de saturação.

### Inferência controlada

- `figsize` maior tende a ajudar quando há muitas isolinhas, rótulos e overlays
- `y_max` influencia onde algumas labels e extensões da saturação aparecem

### Não foi possível validar

- `tw_grid`: o campo existe, mas no `core` enviado o uso direto dele não ficou comprovado
- `grid`: o campo existe no modelo, mas o `core` enviado não o usa explicitamente
- `output` e `dpi`: existem no contrato, mas `draw()` não salva o arquivo; eles podem ser usados por outro fluxo de exportação
- o efeito visual exato de cada `style` depende do backend/ambiente

## Erros comuns

- achar que `output` já faz o arquivo ser salvo automaticamente no `draw()`
- usar `tw_grid` esperando efeito visível sem configurar `show_tw_grid` e `tw_grid_style`
- esquecer `y_max` quando quiser controlar melhor labels e topo do gráfico
