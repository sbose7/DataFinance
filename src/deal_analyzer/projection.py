"""Multi-year hold projection: growth, paydown, appreciation, sale, IRR."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from .finance import irr
from .mortgage import monthly_payment, remaining_balance
from .rental import RentalDeal


@dataclass
class ProjectionAssumptions:
    years: int = 10
    rent_growth: float = 0.03
    expense_growth: float = 0.03
    appreciation: float = 0.03
    selling_cost_pct: float = 0.06
    # Starting market value; defaults to purchase price + rehab when 0.
    starting_value: float = 0.0

    @classmethod
    def from_dict(cls, d: dict | None) -> "ProjectionAssumptions":
        d = d or {}
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class YearRow:
    year: int
    gross_income: float
    operating_expenses: float
    noi: float
    debt_service: float
    cash_flow: float
    cumulative_cash_flow: float
    loan_balance: float
    property_value: float
    equity: float
    cash_on_cash: float


@dataclass
class ProjectionResult:
    cash_invested: float
    years: list[YearRow] = field(default_factory=list)
    sale_price: float = 0.0
    selling_costs: float = 0.0
    loan_payoff: float = 0.0
    net_sale_proceeds: float = 0.0
    total_cash_flow: float = 0.0
    total_profit: float = 0.0
    equity_multiple: float = 0.0
    irr: float | None = None
    average_cash_on_cash: float = 0.0
    cash_flows: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def project(deal: RentalDeal, a: ProjectionAssumptions) -> ProjectionResult:
    loan = deal.purchase_price * (1 - deal.down_payment_pct)
    cash_invested = deal.purchase_price * deal.down_payment_pct + deal.closing_costs + deal.rehab_costs
    pmt = monthly_payment(loan, deal.interest_rate, deal.loan_years, deal.interest_only)
    pct_total = deal.vacancy_pct + deal.maintenance_pct + deal.capex_pct + deal.management_pct
    fixed_monthly = deal.property_tax / 12 + deal.insurance / 12 + deal.hoa_monthly + deal.other_monthly
    value0 = a.starting_value or (deal.purchase_price + deal.rehab_costs)

    rows: list[YearRow] = []
    cumulative = 0.0
    flows = [-cash_invested]
    for y in range(1, a.years + 1):
        rg = (1 + a.rent_growth) ** (y - 1)
        eg = (1 + a.expense_growth) ** (y - 1)
        rent = deal.monthly_rent * rg * 12
        gross = rent + deal.other_income_monthly * rg * 12
        opex = rent * pct_total + fixed_monthly * eg * 12
        noi = gross - opex

        months_before = (y - 1) * 12
        months_left = max(deal.loan_years * 12 - months_before, 0)
        debt = pmt * min(12, months_left) if not deal.interest_only else pmt * 12
        cf = noi - debt
        cumulative += cf

        if deal.interest_only:
            balance = loan
        else:
            balance = remaining_balance(loan, deal.interest_rate, deal.loan_years, y * 12)
        value = value0 * (1 + a.appreciation) ** y

        rows.append(YearRow(
            year=y,
            gross_income=gross,
            operating_expenses=opex,
            noi=noi,
            debt_service=debt,
            cash_flow=cf,
            cumulative_cash_flow=cumulative,
            loan_balance=balance,
            property_value=value,
            equity=value - balance,
            cash_on_cash=cf / cash_invested if cash_invested else float("inf"),
        ))
        flows.append(cf)

    last = rows[-1] if rows else None
    sale_price = last.property_value if last else value0
    selling = sale_price * a.selling_cost_pct
    payoff = last.loan_balance if last else loan
    net_sale = sale_price - selling - payoff
    if rows:
        flows[-1] += net_sale

    total_cf = sum(r.cash_flow for r in rows)
    total_profit = total_cf + net_sale - cash_invested
    inflows = total_cf + net_sale

    return ProjectionResult(
        cash_invested=cash_invested,
        years=rows,
        sale_price=sale_price,
        selling_costs=selling,
        loan_payoff=payoff,
        net_sale_proceeds=net_sale,
        total_cash_flow=total_cf,
        total_profit=total_profit,
        equity_multiple=inflows / cash_invested if cash_invested else float("inf"),
        irr=irr(flows) if cash_invested > 0 else None,
        average_cash_on_cash=(total_cf / len(rows) / cash_invested) if rows and cash_invested else 0.0,
        cash_flows=flows,
    )
