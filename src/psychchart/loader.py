from typing import Dict, List, Tuple
from pathlib import Path

from .config import ChartConfig, IsoSet, Zone, Point
from .utils import load_yaml, ensure_sequence_of_floats, clamp


def _normalize_rh(rh: float) -> float:
    if rh > 1.5:
        rh = rh / 100.0
    if not 0.0 <= rh <= 1.0:
        raise ValueError(f"Umidade relativa inválida: {rh}")
    return rh


def load_chart_config(
    path: str | Path
) -> Tuple[ChartConfig, Dict[str, IsoSet], List[Zone], List[Point]]:
    data = load_yaml(str(path))

    # ---------------- Chart ----------------
    cfg = ChartConfig(**data.get("chart", {}))

    # ---------------- Isolines ----------------
    isolines: Dict[str, IsoSet] = {}
    for name, raw in data.get("isolines", {}).items():
        values = ensure_sequence_of_floats(raw.get("values", []), name=f"isolines.{name}.values")

        if name == "relative_humidity":
            values = [_normalize_rh(v) for v in values]

        isolines[name] = IsoSet(
            name=name,
            values=values,
            style=raw.get("style", "-"),
            color=raw.get("color"),
            cmap=raw.get("cmap") or raw.get("color_map"),
            enabled=raw.get("enabled", True),
        )

    # ---------------- Zones ----------------
    zones: List[Zone] = []
    for z in data.get("zones", []):
        z = dict(z)  # cópia defensiva
    
        if "rh_range" in z:
            z["rh_range"] = [_normalize_rh(v) for v in z["rh_range"]]
    
        zones.append(Zone(**z))


    # ---------------- Points ----------------
    points: List[Point] = []
    for p in data.get("points", []):
        p["rh"] = _normalize_rh(p["rh"])
        points.append(Point(**p))

    return cfg, isolines, zones, points

