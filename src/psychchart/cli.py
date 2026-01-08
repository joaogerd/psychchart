"""
cli.py
-------

Interface de linha de comando para o pacote psychchart.
Permite gerar diagramas psicrométricos a partir de um arquivo de configuração YAML.

Uso:
    python -m psychchart.cli CONFIG_FILE.yaml
    ou, após instalação via pip:
    psychchart CONFIG_FILE.yaml
"""

import sys
import argparse
import yaml
from typing import Dict, Any

from .config import ChartConfig, IsoSet, Zone, Point
from .plot import PsychChart
from .loader import load_chart_config


def main() -> None:
    """
    Ponto de entrada para o CLI.

    Lê um arquivo YAML de configuração, instancia:
      - ChartConfig
      - dicionário de IsoSet
      - lista de Zone
      - lista de Point
    Desenha o diagrama psicrométrico e salva o arquivo de saída.
    """
    parser = argparse.ArgumentParser(
        description="Gera diagrama psicrométrico a partir de YAML de configuração."
    )
    parser.add_argument(
        "config",
        metavar="CONFIG",
        type=str,
        help="Caminho para o arquivo YAML de configuração."
    )
    args = parser.parse_args()

    try:
        cfg, isolines, zones, points = load_chart_config(args.config)
        chart = PsychChart(cfg, isolines, zones, points)
        ax = chart.draw()
        ax.figure.savefig(cfg.output, dpi=cfg.dpi, bbox_inches="tight")
        print(f"[OK] Gráfico salvo em '{cfg.output}'")
    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        sys.exit(1)





if __name__ == "__main__":
    main()
