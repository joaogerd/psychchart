"""
config.py
----------
Definições de configurações e estruturas de dados para o diagrama psicrométrico.
Contém dataclasses para representar parâmetros de gráfico, isolinhas, zonas e pontos.
"""

from dataclasses import dataclass, field
from typing import Sequence, List, Optional

@dataclass
class ChartConfig:
    """
    Parâmetros principais de configuração para geração do diagrama psicrométrico.

    Attributes:
        t_min (float): Temperatura mínima (°C) exibida no eixo horizontal.
        t_max (float): Temperatura máxima (°C) exibida no eixo horizontal.
        y_min (Optional[float]): Limite inferior da umidade absoluta (kg/kg). Se None, inicia em 0.
        y_max (Optional[float]): Limite superior da umidade absoluta (kg/kg). Se None, calculado automaticamente.
        pressure (float): Pressão atmosférica (Pa) usada nos cálculos psicrométricos.
        output (str): Caminho/ nome do arquivo de saída para o gráfico gerado.
        dpi (int): Resolução (dots per inch) do arquivo de saída.
        style (Optional[str]): Estilo do Matplotlib (ex: 'seaborn', 'ggplot'). Se None, mantém estilo padrão.
    """
    t_min: float = 0.0
    t_max: float = 50.0
    y_min: Optional[float] = None
    y_max: Optional[float] = None
    pressure: float = 101_325.0
    output: str = "chart.png"
    dpi: int = 150
    style: Optional[str] = None

@dataclass
class IsoSet:
    """
    Definição de um conjunto de isolinhas a serem desenhadas no diagrama.

    Attributes:
        name (str): Identificador da isolinha (ex: 'relative_humidity', 'enthalpy').
        values (Sequence[float]): Lista de valores para cada isolinha.
        style (str): Estilo de linha Matplotlib (ex: '-', '--', ':').
        color (Optional[str]): Cor fixa das linhas (ex: 'red'); ignorado se cmap for definido.
        cmap (Optional[str]): Nome do colormap Matplotlib para colorir isolinhas pela magnitude.
        enabled (bool): Indica se a isolinha deve ser desenhada.
    """
    name: str
    values: Sequence[float] = field(default_factory=list)
    style: str = "-"
    color: Optional[str] = None
    cmap: Optional[str] = None
    enabled: bool = True

@dataclass
class Zone:
    """
    Representa uma região poligonal ou retangular a destacar no diagrama.

    Attributes:
        name (str): Nome da zona para exibição na legenda.
        vertices (Optional[List[List[float]]]): Lista de pares [T, RH] definindo polígonos customizados.
        t_range (Optional[Sequence[float]]): Intervalo [T_min, T_max] para retângulos ou zonas acompanhando UR.
        rh_range (Optional[Sequence[float]]): Intervalo [RH_min, RH_max] para retângulos ou zonas acompanhando UR.
        follow_rh (bool): Se True, gera polígono acompanhando as curvas de UR entre t_range.
        edgecolor (str): Cor da borda da zona.
        facecolor (Optional[str]): Cor de preenchimento da zona; 'none' ou None para transparente.
        linewidth (float): Espessura da borda (pt).
    """
    name: str
    vertices: Optional[List[List[float]]] = None
    t_range: Optional[Sequence[float]] = None
    rh_range: Optional[Sequence[float]] = None
    follow_rh: bool = False
    edgecolor: str = "k"
    facecolor: Optional[str] = None
    linewidth: float = 1.5

@dataclass
class Point:
    """
    Marca um ponto específico no diagrama com um label.

    Attributes:
        label (str): Texto a ser exibido próximo ao ponto.
        t (float): Temperatura de bulbo seco do ponto (°C).
        rh (float): Umidade relativa do ponto (0–1).
        marker (str): Símbolo Matplotlib para o ponto (ex: 'o', 's', '^').
        color (str): Cor do marcador e do texto (ex: 'black', '#FF0000').
    """
    label: str
    t: float
    rh: float
    marker: str = "o"
    color: str = "k"
