import pytest

from deal_analyzer.mortgage import monthly_payment
from deal_analyzer.refi import RefiScenario, analyze_refi


def test_ltv_limited():
    s = RefiScenario(
        appraised_value=400_000,
        existing_loan_balance=200_000,
        total_cash_in_deal=80_000,
        monthly_rent=4_000,
        monthly_expenses_ex_debt=500,
        closing_cost_pct=0.0,
    )
    r = analyze_refi(s)
    assert r.binding_constraint == "LTV"
    assert r.new_loan_amount == pytest.approx(300_000)
    assert r.cash_out == pytest.approx(100_000)
    assert r.cash_left_in_deal == pytest.approx(-20_000)


def test_dscr_limited_lands_on_min_dscr():
    s = RefiScenario(
        appraised_value=600_000,
        existing_loan_balance=200_000,
        total_cash_in_deal=100_000,
        monthly_rent=2_500,
        monthly_expenses_ex_debt=500,
        min_dscr=1.25,
    )
    r = analyze_refi(s)
    assert r.binding_constraint == "DSCR"
    assert r.dscr == pytest.approx(1.25, abs=1e-6)
    assert r.meets_min_dscr
    assert monthly_payment(r.new_loan_amount, s.rate, s.years) == pytest.approx(2_500 / 1.25 - 500)
