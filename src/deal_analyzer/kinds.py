"""Registry of analysis kinds: one place that maps a name to inputs and an analyzer.

Everything that works on "any kind of deal" (compare, sensitivity, the web UI)
goes through here, so adding a new analysis means adding one entry.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Callable

from .brrrr import BRRRRDeal, analyze_brrrr
from .flip import FlipDeal, analyze_flip
from .projection import ProjectionAssumptions, project
from .refi import RefiScenario, analyze_refi
from .rental import RentalDeal, analyze_rental


@dataclass(frozen=True)
class InputGroup:
    name: str
    cls: type
    key: str | None = None  # None = top-level keys; otherwise nested under this key


@dataclass(frozen=True)
class Kind:
    name: str
    title: str
    groups: tuple[InputGroup, ...]
    run: Callable[[dict], dict]


def _run_rental(d: dict) -> dict:
    return analyze_rental(RentalDeal.from_dict(d)).to_dict()


def _run_flip(d: dict) -> dict:
    return analyze_flip(FlipDeal.from_dict(d)).to_dict()


def _run_refi(d: dict) -> dict:
    return analyze_refi(RefiScenario.from_dict(d)).to_dict()


def _run_brrrr(d: dict) -> dict:
    return analyze_brrrr(BRRRRDeal.from_dict(d)).to_dict()


def _run_project(d: dict) -> dict:
    return project(RentalDeal.from_dict(d), ProjectionAssumptions.from_dict(d.get("projection"))).to_dict()


KINDS: dict[str, Kind] = {
    "rental": Kind("rental", "Rental", (InputGroup("Deal", RentalDeal),), _run_rental),
    "flip": Kind("flip", "Flip", (InputGroup("Deal", FlipDeal),), _run_flip),
    "refi": Kind("refi", "Refinance", (InputGroup("Refinance", RefiScenario),), _run_refi),
    "brrrr": Kind("brrrr", "BRRRR", (InputGroup("Deal", BRRRRDeal),), _run_brrrr),
    "project": Kind(
        "project",
        "Hold projection",
        (InputGroup("Deal", RentalDeal), InputGroup("Projection", ProjectionAssumptions, "projection")),
        _run_project,
    ),
}


def run(kind: str, inputs: dict) -> dict:
    if kind not in KINDS:
        raise KeyError(f"unknown kind {kind!r}; choose from {', '.join(KINDS)}")
    return KINDS[kind].run(inputs)


def _type_name(f: dataclasses.Field) -> str:
    t = f.type if isinstance(f.type, str) else getattr(f.type, "__name__", str(f.type))
    if "bool" in t:
        return "bool"
    if "int" in t:
        return "int"
    return "float"


def schema() -> dict:
    """Field metadata for every kind, used by the web UI to build forms."""
    out = {}
    for k in KINDS.values():
        groups = []
        for g in k.groups:
            fields = []
            for f in dataclasses.fields(g.cls):
                default = None if f.default is dataclasses.MISSING else f.default
                fields.append({"name": f.name, "type": _type_name(f), "default": default,
                               "required": f.default is dataclasses.MISSING})
            groups.append({"name": g.name, "key": g.key, "fields": fields})
        out[k.name] = {"title": k.title, "groups": groups}
    return out


def scalar_items(result: dict) -> dict:
    """Only the top-level numbers/bools/strings from a result (drops tables and breakdowns)."""
    return {k: v for k, v in result.items() if isinstance(v, (int, float, str, bool)) or v is None}
