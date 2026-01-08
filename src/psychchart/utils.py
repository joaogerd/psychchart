"""
utils.py
--------

Funções utilitárias e auxiliares para o pacote `psychchart`.
Contém carregamento seguro de YAML, validações de config e pequenas transformações comuns.
"""
import os
import yaml
from typing import Any, Dict, Sequence, Union


def load_yaml(path: str) -> Dict[str, Any]:
    """
    Carrega um arquivo YAML e retorna um dicionário Python.

    Parâmetros:
        path (str): Caminho para o arquivo YAML.

    Retorna:
        Dict[str, Any]: Dados carregados do YAML.

    Lança:
        FileNotFoundError: se o arquivo não existir.
        yaml.YAMLError: em caso de erro de parsing.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Arquivo YAML '{path}' não encontrado.")
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data or {}


def ensure_sequence_of_floats(
    seq: Union[Sequence[Any], Any],
    length: int = None,
    name: str = "sequence"
) -> Sequence[float]:
    """
    Garante que a entrada seja uma sequência de floats válida.

    Converte elementos numéricos encontrados em float e verifica comprimento, se especificado.

    Parâmetros:
        seq (Sequence[Any] ou qualquer): Sequência de valores ou único valor.
        length (int, opcional): Comprimento exato esperado. Se None, não valida comprimento.
        name (str): Nome semântico para mensagens de erro.

    Retorna:
        Sequence[float]: Sequência de floats.

    Lança:
        ValueError: se algum elemento não puder ser convertido ou length não bater.
    """
    # Aceita valor único transformando em lista
    if not isinstance(seq, (list, tuple)):
        seq = [seq]
    # Converte para float
    try:
        float_seq = [float(x) for x in seq]
    except Exception:
        raise ValueError(f"'{name}' contém valores não numéricos: {seq}")
    # Verifica comprimento
    if length is not None and len(float_seq) != length:
        raise ValueError(
            f"'{name}' deve ter exatamente {length} elementos, mas tem {len(float_seq)}"
        )
    return float_seq


def clamp(x: float, minimum: float, maximum: float) -> float:
    """
    Limita um valor x dentro do intervalo [minimum, maximum].

    Parâmetros:
        x (float): Valor de entrada.
        minimum (float): Limite inferior.
        maximum (float): Limite superior.

    Retorna:
        float: Valor limitado.
    """
    return max(minimum, min(maximum, x))


def dict_deep_merge(a: Dict[Any, Any], b: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Mescla recursivamente dois dicionários, dando precedência aos valores de b.

    Parâmetros:
        a (Dict): Dicionário base.
        b (Dict): Dicionário cujos valores sobrescrevem a.

    Retorna:
        Dict: Novo dicionário resultante da mescla.
    """
    result = dict(a)
    for key, val in b.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = dict_deep_merge(result[key], val)
        else:
            result[key] = val
    return result



