import pytest

from deal_analyzer.mortgage import amortization_schedule, monthly_payment, remaining_balance


def test_standard_payment():
    # 240k @ 7.25% / 30y is a well-known ~$1,637.22
    assert monthly_payment(240_000, 0.0725, 30) == pytest.approx(1637.22, abs=0.01)


def test_zero_rate():
    assert monthly_payment(120_000, 0.0, 10) == pytest.approx(1000.0)


def test_interest_only():
    assert monthly_payment(300_000, 0.06, 30, interest_only=True) == pytest.approx(1500.0)


def test_zero_principal():
    assert monthly_payment(0, 0.07, 30) == 0.0


def test_schedule_pays_off():
    rows = amortization_schedule(200_000, 0.065, 30)
    assert len(rows) == 360
    assert rows[-1].balance == pytest.approx(0.0, abs=0.01)
    assert sum(r.principal for r in rows) == pytest.approx(200_000, abs=0.5)


def test_remaining_balance_matches_schedule():
    rows = amortization_schedule(200_000, 0.065, 30)
    assert remaining_balance(200_000, 0.065, 30, 60) == pytest.approx(rows[59].balance, abs=0.01)
