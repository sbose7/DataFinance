import pytest

from deal_analyzer.flip import FlipDeal, analyze_flip


def test_all_cash_flip():
    d = FlipDeal(
        purchase_price=100_000,
        arv=200_000,
        rehab_costs=40_000,
        holding_months=6,
        contingency_pct=0.0,
        buy_closing_pct=0.0,
        sell_closing_pct=0.0,
        agent_commission_pct=0.05,
        monthly_holding=500,
    )
    r = analyze_flip(d)
    assert r.loan_amount == 0
    assert r.financing_costs == 0
    # 200k - 100k - 40k - 3k holding - 10k commission
    assert r.net_profit == pytest.approx(47_000)
    assert r.cash_required == pytest.approx(143_000)
    assert r.seventy_percent_rule_max == pytest.approx(100_000)
    assert r.passes_seventy_percent_rule is True


def test_leverage_raises_roi():
    common = dict(purchase_price=200_000, arv=350_000, rehab_costs=50_000)
    cash = analyze_flip(FlipDeal(**common))
    levered = analyze_flip(FlipDeal(**common, loan_to_cost=0.85))
    assert levered.net_profit < cash.net_profit
    assert levered.roi_on_cash > cash.roi_on_cash
