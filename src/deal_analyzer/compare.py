"""Side-by-side comparison of several deals of the same kind."""

from __future__ import annotations

from .kinds import run, scalar_items


def compare(kind: str, deals: dict[str, dict], sort_by: str | None = None, descending: bool = True) -> dict:
    """deals maps a label (e.g. a file name) to its inputs.

    Returns {"labels": [...], "metrics": {metric: [value per label]}}.
    """
    results = {label: scalar_items(run(kind, inputs)) for label, inputs in deals.items()}
    labels = list(results)
    if sort_by:
        missing = [l for l in labels if sort_by not in results[l]]
        if missing:
            raise KeyError(f"metric {sort_by!r} not in {kind} results")
        def key(l):
            v = results[l][sort_by]
            return float("-inf") if v is None else v
        labels.sort(key=key, reverse=descending)
    metric_names: list[str] = []
    for l in labels:
        for m in results[l]:
            if m not in metric_names:
                metric_names.append(m)
    return {
        "kind": kind,
        "labels": labels,
        "metrics": {m: [results[l].get(m) for l in labels] for m in metric_names},
    }
