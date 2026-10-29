"""BRRRR: Buy, Rehab, Rent, Refinance, Repeat — end-to-end in one pass."""

from __future__ import annotations

from dataclasses import dataclass, asdict

from .refi import RefiScenario, analyze_refi
from .rental import RentalDeal, analyze_rental


@dataclass
class BRRRRDeal:
    purchase_price: float
    rehab_costs: float
    arv: float
    monthly_rent: float
    # Acquisition financing (hard money / bridge). 0 = all cash.
    loan_to_cost: float = 0.85
    finance_rehab: bool = True
    acq_rate: float = 0.11
    acq_points: float = 0.02
    holding_months: int = 6
    buy_closing_pct: float = 0.02
    monthly_holding: float = 0.0
    # Refinance
    max_ltv: float = 0.75
    refi_rate: float = 0.075
    refi_years: int = 30
    refi_closing_pct: float = 0.03
    min_dscr: float = 1.0
    # Rental operations after refi
    property_tax: float = 0.0
    insurance: float = 0.0
    hoa_monthly: float = 0.0
    vacancy_pct: float = 0.05
    maintenance_pct: float = 0.05
    capex_pct: float = 0.05
    management_pct: float = 0.08

    @classmethod
    def from_dict(cls, d: dict) -> "BRRRRDeal":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class BRRRRResult:
    acquisition_loan: float
    acquisition_costs: float  # closing + points + interest + holding
    cash_in_before_refi: float
    refi_loan: float
    refi_binding_constraint: str
    cash_out: float
    cash_left_in_deal: float
    all_cash_recovered: bool
    equity_after_refi: float
    monthly_noi: float
    monthly_debt_service: float
    monthly_cash_flow: float
    annual_cash_flow: float
    dscr: float
    cash_on_cash: float

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_brrrr(d: BRRRRDeal) -> BRRRRResult:
    base = d.purchase_price + (d.rehab_costs if d.finance_rehab else 0.0)
    acq_loan = base * d.loan_to_cost
    buy_closing = d.purchase_price * d.buy_closing_pct
    points = acq_loan * d.acq_points
    interest = acq_loan * d.acq_rate / 12 * d.holding_months
    holding = d.monthly_holding * d.holding_months
    acq_costs = buy_closing + points + interest + holding
    cash_in = d.purchase_price + d.rehab_costs + acq_costs - acq_loan

    fixed_monthly = d.property_tax / 12 + d.insurance / 12 + d.hoa_monthly
    refi = analyze_refi(RefiScenario(
        appraised_value=d.arv,
        existing_loan_balance=acq_loan,
        total_cash_in_deal=cash_in,
        monthly_rent=d.monthly_rent,
        monthly_expenses_ex_debt=fixed_monthly,
        max_ltv=d.max_ltv,
        rate=d.refi_rate,
        years=d.refi_years,
        closing_cost_pct=d.refi_closing_pct,
        min_dscr=d.min_dscr,
    ))

    down_pct = 1 - refi.new_loan_amount / d.arv if d.arv else 1.0
    rental = analyze_rental(RentalDeal(
        purchase_price=d.arv,
        monthly_rent=d.monthly_rent,
        down_payment_pct=down_pct,
        interest_rate=d.refi_rate,
        loan_years=d.refi_years,
        property_tax=d.property_tax,
        insurance=d.insurance,
        hoa_monthly=d.hoa_monthly,
        vacancy_pct=d.vacancy_pct,
        maintenance_pct=d.maintenance_pct,
        capex_pct=d.capex_pct,
        management_pct=d.management_pct,
    ))

    left = refi.cash_left_in_deal
    annual = rental.annual_cash_flow
    if left > 0:
        coc = annual / left
    else:
        coc = float("inf") if annual > 0 else 0.0

    return BRRRRResult(
        acquisition_loan=acq_loan,
        acquisition_costs=acq_costs,
        cash_in_before_refi=cash_in,
        refi_loan=refi.new_loan_amount,
        refi_binding_constraint=refi.binding_constraint,
        cash_out=refi.cash_out,
        cash_left_in_deal=left,
        all_cash_recovered=left <= 0,
        equity_after_refi=d.arv - refi.new_loan_amount,
        monthly_noi=rental.monthly_noi,
        monthly_debt_service=rental.monthly_debt_service,
        monthly_cash_flow=rental.monthly_cash_flow,
        annual_cash_flow=annual,
        dscr=refi.dscr,
        cash_on_cash=coc,
    )
