"""Buy-and-hold rental analysis: cash flow, cap rate, cash-on-cash, DSCR."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from .mortgage import monthly_payment


@dataclass
class RentalDeal:
    purchase_price: float
    monthly_rent: float
    down_payment_pct: float = 0.25
    interest_rate: float = 0.07
    loan_years: int = 30
    interest_only: bool = False
    closing_costs: float = 0.0
    rehab_costs: float = 0.0
    # Annual fixed expenses
    property_tax: float = 0.0
    insurance: float = 0.0
    hoa_monthly: float = 0.0
    other_monthly: float = 0.0
    # Expenses as a percent of gross rent
    vacancy_pct: float = 0.05
    maintenance_pct: float = 0.05
    capex_pct: float = 0.05
    management_pct: float = 0.08
    other_income_monthly: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "RentalDeal":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class RentalResult:
    loan_amount: float
    cash_invested: float
    gross_monthly_income: float
    monthly_operating_expenses: float
    monthly_noi: float
    monthly_debt_service: float
    monthly_cash_flow: float
    annual_cash_flow: float
    cap_rate: float
    cash_on_cash: float
    dscr: float | None
    gross_rent_multiplier: float
    one_percent_rule: bool
    breakeven_rent: float
    expense_breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_rental(deal: RentalDeal) -> RentalResult:
    loan = deal.purchase_price * (1 - deal.down_payment_pct)
    cash_invested = deal.purchase_price * deal.down_payment_pct + deal.closing_costs + deal.rehab_costs

    gross = deal.monthly_rent + deal.other_income_monthly
    pct_total = deal.vacancy_pct + deal.maintenance_pct + deal.capex_pct + deal.management_pct
    breakdown = {
        "vacancy": deal.monthly_rent * deal.vacancy_pct,
        "maintenance": deal.monthly_rent * deal.maintenance_pct,
        "capex": deal.monthly_rent * deal.capex_pct,
        "management": deal.monthly_rent * deal.management_pct,
        "property_tax": deal.property_tax / 12,
        "insurance": deal.insurance / 12,
        "hoa": deal.hoa_monthly,
        "other": deal.other_monthly,
    }
    opex = sum(breakdown.values())
    noi = gross - opex
    debt = monthly_payment(loan, deal.interest_rate, deal.loan_years, deal.interest_only)
    cash_flow = noi - debt

    all_in = deal.purchase_price + deal.rehab_costs
    cap_rate = (noi * 12) / all_in if all_in else 0.0
    coc = (cash_flow * 12) / cash_invested if cash_invested else float("inf")
    dscr = noi / debt if debt else None
    grm = deal.purchase_price / (deal.monthly_rent * 12) if deal.monthly_rent else float("inf")

    fixed = breakdown["property_tax"] + breakdown["insurance"] + breakdown["hoa"] + breakdown["other"]
    # Rent R such that R*(1 - pct_total) + other_income - fixed - debt = 0
    denom = 1 - pct_total
    breakeven = (fixed + debt - deal.other_income_monthly) / denom if denom > 0 else float("inf")

    return RentalResult(
        loan_amount=loan,
        cash_invested=cash_invested,
        gross_monthly_income=gross,
        monthly_operating_expenses=opex,
        monthly_noi=noi,
        monthly_debt_service=debt,
        monthly_cash_flow=cash_flow,
        annual_cash_flow=cash_flow * 12,
        cap_rate=cap_rate,
        cash_on_cash=coc,
        dscr=dscr,
        gross_rent_multiplier=grm,
        one_percent_rule=deal.monthly_rent >= 0.01 * all_in,
        breakeven_rent=max(breakeven, 0.0),
        expense_breakdown=breakdown,
    )
