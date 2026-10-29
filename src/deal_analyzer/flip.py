"""Fix-and-flip analysis: profit, ROI, 70% rule, max allowable offer."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class FlipDeal:
    purchase_price: float
    arv: float  # after-repair value
    rehab_costs: float
    holding_months: int = 6
    # Financing (hard money style). Set loan_to_cost to 0 for an all-cash flip.
    loan_to_cost: float = 0.0
    loan_rate: float = 0.11
    loan_points: float = 0.02
    finance_rehab: bool = True
    # Costs
    buy_closing_pct: float = 0.02
    sell_closing_pct: float = 0.02
    agent_commission_pct: float = 0.05
    monthly_holding: float = 0.0  # taxes, insurance, utilities per month
    contingency_pct: float = 0.10  # buffer on rehab

    @classmethod
    def from_dict(cls, d: dict) -> "FlipDeal":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class FlipResult:
    total_rehab: float
    loan_amount: float
    financing_costs: float
    holding_costs: float
    buy_closing: float
    sell_costs: float
    total_project_cost: float
    cash_required: float
    net_profit: float
    roi_on_cash: float
    annualized_roi: float
    profit_margin_on_arv: float
    seventy_percent_rule_max: float
    passes_seventy_percent_rule: bool

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_flip(deal: FlipDeal) -> FlipResult:
    total_rehab = deal.rehab_costs * (1 + deal.contingency_pct)
    financed_base = deal.purchase_price + (total_rehab if deal.finance_rehab else 0.0)
    loan = financed_base * deal.loan_to_cost

    points = loan * deal.loan_points
    interest = loan * deal.loan_rate / 12 * deal.holding_months  # interest-only
    financing = points + interest

    holding = deal.monthly_holding * deal.holding_months
    buy_closing = deal.purchase_price * deal.buy_closing_pct
    sell_costs = deal.arv * (deal.sell_closing_pct + deal.agent_commission_pct)

    total_cost = deal.purchase_price + total_rehab + financing + holding + buy_closing + sell_costs
    net_profit = deal.arv - total_cost
    cash_required = total_cost - sell_costs - loan  # sell costs come out of proceeds

    roi = net_profit / cash_required if cash_required > 0 else float("inf")
    years = deal.holding_months / 12
    annualized = (1 + roi) ** (1 / years) - 1 if years > 0 and roi > -1 and roi != float("inf") else roi

    mao = deal.arv * 0.70 - deal.rehab_costs

    return FlipResult(
        total_rehab=total_rehab,
        loan_amount=loan,
        financing_costs=financing,
        holding_costs=holding,
        buy_closing=buy_closing,
        sell_costs=sell_costs,
        total_project_cost=total_cost,
        cash_required=cash_required,
        net_profit=net_profit,
        roi_on_cash=roi,
        annualized_roi=annualized,
        profit_margin_on_arv=net_profit / deal.arv if deal.arv else 0.0,
        seventy_percent_rule_max=mao,
        passes_seventy_percent_rule=deal.purchase_price <= mao,
    )
