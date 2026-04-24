# Pipeline de renderização

## O que é

Este arquivo resume a ordem em que o gráfico é desenhado no `core` do plot.

## Para que serve

Saber essa ordem é importante porque vários elementos podem se sobrepor. Um mesmo ajuste de `alpha`, `color`, `zorder` ou `colorbar` produz efeitos diferentes dependendo da etapa em que o elemento entra.

## Ordem confirmada no código

### 1. Preparação

O gráfico cria a figura e os eixos, depois prepara o domínio termodinâmico com:

- vetor de temperatura `T`
- curva de saturação `W_sat`

### 2. Camadas de fundo

A ordem confirmada é:

1. `draw_density_field(self.ax, self)`
2. `draw_indexes(self, self.ax)`
3. `draw_index_zones(self, self.ax)`

### 3. Camadas canônicas baseadas em dados

Depois entram as camadas de `data_layers` com `draw_data_layers(self, self.ax)`.

Isso significa que `points`, `scatter`, `density`, `scalar_field`, `path` e `annotate` definidos dentro de `data_layers` entram **antes** da curva de saturação e antes das zonas/isolines clássicas.

### 4. Limite físico

A curva de saturação é desenhada em seguida.

### 5. Camadas analíticas de primeiro plano

Depois entram:

- `draw_zones(self.ax, self)`
- `draw_isolines(self.ax, self)`
- `_draw_points()`

### 6. Finalização visual

Por fim, o gráfico:

- aplica título e rótulos
- aplica limites do eixo
- desenha a grade `T × W` se habilitada
- move o eixo Y para a direita
- desenha extensões visuais da curva de saturação

## Exemplo de interpretação prática

Se você usar:

- um `index` com campo preenchido
- uma `density` em `data_layers`
- uma `zone`
- e `isolines`

o comportamento esperado é:

- o fundo de índice aparece primeiro
- a densidade do `data_layer` aparece por cima do fundo
- a curva de saturação fica acima dessas camadas
- zonas geométricas e isolinhas clássicas aparecem por cima
- pontos de referência aparecem no primeiro plano

## Observações importantes

### Confirmado no código

- o eixo Y é colocado à direita
- a curva de saturação é tratada como limite físico superior
- a grade auxiliar `T × W` é desenhada no final, alinhada aos ticks
- a curva de saturação recebe extensões visuais para “fechar” o domínio

### Inferência controlada

- em gráficos muito carregados, convém reduzir `alpha` de campos e densidades para não prejudicar `zones`, `isolines` e `points`

### Não foi possível validar

- o impacto visual exato de todos os estilos de Matplotlib (`style`) depende do ambiente e não aparece completamente no material enviado
