"""Cash-out / DSCR refinance analysis (the "R" in BRRRR)."""

from __future__ import annotations

from dataclasses import dataclass, asdict

from .mortgage import monthly_payment


@dataclass
class RefiScenario:
    appraised_value: float
    existing_loan_balance: float
    total_cash_in_deal: float  # everything you've put in so far
    monthly_rent: float
    monthly_expenses_ex_debt: float  # taxes, insurance, HOA (PITIA minus P&I) + any opex lender counts
    max_ltv: float = 0.75
    rate: float = 0.075
    years: int = 30
    closing_cost_pct: float = 0.03
    min_dscr: float = 1.0
    interest_only: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "RefiScenario":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class RefiResult:
    ltv_max_loan: float
    dscr_max_loan: float
    new_loan_amount: float
    binding_constraint: str
    closing_costs: float
    cash_out: float
    cash_left_in_deal: float
    new_monthly_payment: float
    dscr: float
    meets_min_dscr: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _max_loan_for_payment(payment: float, rate: float, years: int, interest_only: bool) -> float:
    if payment <= 0:
        return 0.0
    unit = monthly_payment(1.0, rate, years, interest_only)
    return payment / unit if unit else 0.0


def analyze_refi(s: RefiScenario) -> RefiResult:
    """Size a refinance by the tighter of LTV and DSCR.

    DSCR here is the common investor-loan definition: rent / PITIA,
    where PITIA = new P&I + monthly_expenses_ex_debt.
    """
    ltv_loan = s.appraised_value * s.max_ltv

    # rent / (P&I + exp) >= min_dscr  ->  P&I <= rent/min_dscr - exp
    max_pi = s.monthly_rent / s.min_dscr - s.monthly_expenses_ex_debt
    dscr_loan = _max_loan_for_payment(max_pi, s.rate, s.years, s.interest_only)

    loan = min(ltv_loan, dscr_loan)
    binding = "LTV" if ltv_loan <= dscr_loan else "DSCR"
    loan = max(loan, 0.0)

    closing = loan * s.closing_cost_pct
    cash_out = loan - s.existing_loan_balance - closing
    pmt = monthly_payment(loan, s.rate, s.years, s.interest_only)
    pitia = pmt + s.monthly_expenses_ex_debt
    dscr = s.monthly_rent / pitia if pitia else float("inf")

    return RefiResult(
        ltv_max_loan=ltv_loan,
        dscr_max_loan=dscr_loan,
        new_loan_amount=loan,
        binding_constraint=binding,
        closing_costs=closing,
        cash_out=cash_out,
        cash_left_in_deal=s.total_cash_in_deal - cash_out,
        new_monthly_payment=pmt,
        dscr=dscr,
        meets_min_dscr=dscr >= s.min_dscr - 1e-9,
    )
