"""Two-variable sensitivity grids over any input and any output metric."""

from __future__ import annotations

import copy
from dataclasses import dataclass, asdict

from .kinds import run


def parse_values(spec: str) -> list[float]:
    """'0.06:0.08:0.005' (inclusive range) or '2600,2800,3000' (list)."""
    if ":" in spec:
        start, stop, step = (float(x) for x in spec.split(":"))
        if step <= 0:
            raise ValueError("step must be positive")
        vals, i = [], 0
        while True:
            v = start + i * step
            if v > stop + step * 1e-9:
                break
            vals.append(round(v, 10))
            i += 1
        return vals
    return [float(x) for x in spec.split(",") if x.strip()]


def _set(d: dict, path: str, value) -> None:
    """Set a possibly dotted key, e.g. 'projection.rent_growth'."""
    parts = path.split(".")
    cur = d
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


@dataclass
class Grid:
    kind: str
    metric: str
    x_field: str
    x_values: list[float]
    y_field: str
    y_values: list[float]
    values: list[list[float | None]]  # values[row=y][col=x]

    def to_dict(self) -> dict:
        return asdict(self)


def sensitivity(kind: str, inputs: dict, metric: str,
                x_field: str, x_values: list[float],
                y_field: str, y_values: list[float]) -> Grid:
    table: list[list[float | None]] = []
    for yv in y_values:
        row = []
        for xv in x_values:
            d = copy.deepcopy(inputs)
            _set(d, x_field, xv)
            _set(d, y_field, yv)
            result = run(kind, d)
            if metric not in result:
                raise KeyError(f"metric {metric!r} not in {kind} results; options: "
                               f"{', '.join(k for k, v in result.items() if isinstance(v, (int, float)))}")
            row.append(result[metric])
        table.append(row)
    return Grid(kind, metric, x_field, x_values, y_field, y_values, table)
