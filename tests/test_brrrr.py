import math

import pytest

from deal_analyzer.brrrr import BRRRRDeal, analyze_brrrr


def make(**kw):
    base = dict(purchase_price=150_000, rehab_costs=50_000, arv=300_000, monthly_rent=2_600,
                loan_to_cost=0.0, acq_points=0.0, buy_closing_pct=0.0, holding_months=4,
                refi_closing_pct=0.0, property_tax=2_400, insurance=1_200)
    base.update(kw)
    return BRRRRDeal(**base)


def test_all_cash_purchase_then_refi():
    r = analyze_brrrr(make())
    assert r.acquisition_loan == 0
    assert r.cash_in_before_refi == pytest.approx(200_000)
    assert r.refi_loan == pytest.approx(225_000)  # 75% of 300k, LTV-limited
    assert r.refi_binding_constraint == "LTV"
    assert r.cash_out == pytest.approx(225_000)
    assert r.cash_left_in_deal == pytest.approx(-25_000)
    assert r.all_cash_recovered
    assert r.equity_after_refi == pytest.approx(75_000)


def test_infinite_return_when_all_cash_back_and_positive_cash_flow():
    r = analyze_brrrr(make(monthly_rent=3_500))
    assert r.monthly_cash_flow > 0
    assert math.isinf(r.cash_on_cash)


def test_financed_acquisition_costs():
    r = analyze_brrrr(make(loan_to_cost=0.8, acq_rate=0.12, acq_points=0.02, holding_months=6))
    loan = 200_000 * 0.8
    assert r.acquisition_loan == pytest.approx(loan)
    assert r.acquisition_costs == pytest.approx(loan * 0.02 + loan * 0.12 / 2)
    assert r.cash_out == pytest.approx(r.refi_loan - loan)
