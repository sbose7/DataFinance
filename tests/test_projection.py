import pytest

from deal_analyzer.finance import npv
from deal_analyzer.projection import ProjectionAssumptions, project
from deal_analyzer.rental import RentalDeal, analyze_rental


def deal(**kw):
    base = dict(purchase_price=300_000, monthly_rent=2_600, down_payment_pct=0.25, interest_rate=0.07,
                closing_costs=6_000, property_tax=3_600, insurance=1_200)
    base.update(kw)
    return RentalDeal(**base)


def test_year_one_matches_rental_analysis():
    d = deal()
    p = project(d, ProjectionAssumptions(years=5))
    r = analyze_rental(d)
    assert p.years[0].noi == pytest.approx(r.monthly_noi * 12)
    assert p.years[0].cash_flow == pytest.approx(r.annual_cash_flow)
    assert p.cash_invested == pytest.approx(r.cash_invested)


def test_no_growth_is_flat():
    p = project(deal(), ProjectionAssumptions(years=4, rent_growth=0, expense_growth=0, appreciation=0))
    flows = {round(y.cash_flow, 6) for y in p.years}
    assert len(flows) == 1
    assert p.sale_price == pytest.approx(300_000)


def test_balance_falls_and_equity_rises():
    p = project(deal(), ProjectionAssumptions(years=10))
    bal = [y.loan_balance for y in p.years]
    eq = [y.equity for y in p.years]
    assert all(a > b for a, b in zip(bal, bal[1:]))
    assert all(a < b for a, b in zip(eq, eq[1:]))


def test_irr_is_consistent_with_cash_flows():
    p = project(deal(), ProjectionAssumptions(years=10))
    assert p.cash_flows[0] == pytest.approx(-p.cash_invested)
    assert npv(p.irr, p.cash_flows) == pytest.approx(0, abs=1e-3)
    assert p.total_profit == pytest.approx(sum(p.cash_flows))


def test_interest_only_keeps_balance():
    p = project(deal(interest_only=True), ProjectionAssumptions(years=3))
    assert all(y.loan_balance == pytest.approx(225_000) for y in p.years)


def test_loan_paid_off_stops_debt_service():
    p = project(deal(loan_years=2), ProjectionAssumptions(years=4))
    assert p.years[2].debt_service == 0
    assert p.years[3].loan_balance == pytest.approx(0, abs=0.01)


def test_starting_value_override():
    p = project(deal(), ProjectionAssumptions(years=1, appreciation=0, starting_value=350_000))
    assert p.sale_price == pytest.approx(350_000)
