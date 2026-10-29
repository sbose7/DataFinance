import pytest

from deal_analyzer.rental import RentalDeal, analyze_rental


def make(**kw):
    base = dict(
        purchase_price=200_000,
        monthly_rent=2_000,
        down_payment_pct=0.25,
        interest_rate=0.07,
        property_tax=2_400,
        insurance=1_200,
        vacancy_pct=0.05,
        maintenance_pct=0.05,
        capex_pct=0.05,
        management_pct=0.10,
    )
    base.update(kw)
    return RentalDeal(**base)


def test_basic_metrics():
    r = analyze_rental(make())
    assert r.loan_amount == 150_000
    assert r.cash_invested == 50_000
    # 25% of rent + 300/mo fixed = 800
    assert r.monthly_operating_expenses == pytest.approx(800)
    assert r.monthly_noi == pytest.approx(1_200)
    assert r.cap_rate == pytest.approx(1_200 * 12 / 200_000)
    assert r.one_percent_rule is True


def test_breakeven_rent_zeroes_cash_flow():
    r = analyze_rental(make())
    r2 = analyze_rental(make(monthly_rent=r.breakeven_rent))
    assert r2.monthly_cash_flow == pytest.approx(0, abs=0.01)


def test_all_cash_has_no_dscr():
    r = analyze_rental(make(down_payment_pct=1.0))
    assert r.dscr is None
    assert r.monthly_debt_service == 0


def test_from_dict_ignores_unknown_keys():
    d = RentalDeal.from_dict({"purchase_price": 1, "monthly_rent": 1, "notes": "x"})
    assert d.purchase_price == 1
