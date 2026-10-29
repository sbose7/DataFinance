"""General time-value-of-money helpers."""

from __future__ import annotations

import math
from typing import Sequence


def npv(rate: float, cash_flows: Sequence[float]) -> float:
    """Net present value; cash_flows[0] is at t=0."""
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))


def irr(cash_flows: Sequence[float], lo: float = -0.9999, hi: float = 10.0, tol: float = 1e-10) -> float | None:
    """Internal rate of return by bisection.

    Returns None when the flows don't change sign within [lo, hi]
    (e.g. all positive or all negative), where IRR is undefined.
    """
    f_lo, f_hi = npv(lo, cash_flows), npv(hi, cash_flows)
    if math.isnan(f_lo) or math.isnan(f_hi) or f_lo * f_hi > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        f_mid = npv(mid, cash_flows)
        if abs(f_mid) < tol or (hi - lo) < tol:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def clean(obj):
    """Make results JSON-safe: inf/nan -> None, recursively."""
    if isinstance(obj, float):
        return None if math.isinf(obj) or math.isnan(obj) else obj
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return obj
