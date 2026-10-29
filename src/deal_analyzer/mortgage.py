"""Loan math: payments, balances, amortization."""

from __future__ import annotations

from dataclasses import dataclass


def monthly_payment(principal: float, annual_rate: float, years: int, interest_only: bool = False) -> float:
    """Monthly principal + interest payment.

    annual_rate is a decimal (0.07 for 7%).
    """
    if principal <= 0:
        return 0.0
    r = annual_rate / 12
    if interest_only:
        return principal * r
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def remaining_balance(principal: float, annual_rate: float, years: int, months_paid: int) -> float:
    """Loan balance after a number of monthly payments."""
    if principal <= 0:
        return 0.0
    r = annual_rate / 12
    n = years * 12
    months_paid = min(months_paid, n)
    if r == 0:
        return principal * (1 - months_paid / n)
    pmt = monthly_payment(principal, annual_rate, years)
    return principal * (1 + r) ** months_paid - pmt * ((1 + r) ** months_paid - 1) / r


@dataclass
class AmortizationRow:
    month: int
    payment: float
    principal: float
    interest: float
    balance: float


def amortization_schedule(principal: float, annual_rate: float, years: int) -> list[AmortizationRow]:
    """Full month-by-month schedule."""
    rows: list[AmortizationRow] = []
    balance = principal
    r = annual_rate / 12
    pmt = monthly_payment(principal, annual_rate, years)
    for m in range(1, years * 12 + 1):
        interest = balance * r
        princ = min(pmt - interest, balance)
        balance -= princ
        rows.append(AmortizationRow(m, princ + interest, princ, interest, max(balance, 0.0)))
    return rows
