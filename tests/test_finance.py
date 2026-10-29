import math

import pytest

from deal_analyzer.finance import clean, irr, npv


def test_npv_zero_rate_is_sum():
    assert npv(0, [-100, 50, 60]) == pytest.approx(10)


def test_irr_simple():
    # -100 now, +110 in a year -> 10%
    assert irr([-100, 110]) == pytest.approx(0.10, abs=1e-8)


def test_irr_zeroes_npv():
    flows = [-93_000, 525, 1_130, 1_754, 2_396, 3_057, 3_738, 4_440, 5_162, 5_907, 230_466]
    r = irr(flows)
    assert npv(r, flows) == pytest.approx(0, abs=1e-4)


def test_irr_undefined_without_sign_change():
    assert irr([100, 100, 100]) is None
    assert irr([-100, -5]) is None


def test_clean_replaces_inf_and_nan():
    out = clean({"a": math.inf, "b": [1.0, math.nan], "c": {"d": -math.inf}, "e": "x"})
    assert out == {"a": None, "b": [1.0, None], "c": {"d": None}, "e": "x"}
