"""Command-line interface.

    deal-analyzer rental examples/rental.json
    deal-analyzer flip examples/flip.json --json
    deal-analyzer refi examples/refi.json
    deal-analyzer amortize 300000 0.07 30 --months 12
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .flip import FlipDeal, analyze_flip
from .mortgage import amortization_schedule
from .refi import RefiScenario, analyze_refi
from .rental import RentalDeal, analyze_rental


def _money(x: float) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):,.0f}"


def _pct(x: float) -> str:
    if x in (float("inf"), float("-inf")):
        return "∞"
    return f"{x * 100:.2f}%"


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _print_rows(title: str, rows: list[tuple[str, str]]) -> None:
    width = max(len(k) for k, _ in rows)
    print(f"\n{title}\n{'-' * len(title)}")
    for k, v in rows:
        print(f"  {k.ljust(width)}  {v}")
    print()


def cmd_rental(args: argparse.Namespace) -> int:
    r = analyze_rental(RentalDeal.from_dict(_load(args.file)))
    if args.json:
        print(json.dumps(r.to_dict(), indent=2))
        return 0
    _print_rows("Rental analysis", [
        ("Loan amount", _money(r.loan_amount)),
        ("Cash invested", _money(r.cash_invested)),
        ("Gross income / mo", _money(r.gross_monthly_income)),
        ("Operating expenses / mo", _money(r.monthly_operating_expenses)),
        ("NOI / mo", _money(r.monthly_noi)),
        ("Debt service / mo", _money(r.monthly_debt_service)),
        ("Cash flow / mo", _money(r.monthly_cash_flow)),
        ("Cash flow / yr", _money(r.annual_cash_flow)),
        ("Cap rate", _pct(r.cap_rate)),
        ("Cash-on-cash", _pct(r.cash_on_cash)),
        ("DSCR (NOI / debt)", f"{r.dscr:.2f}" if r.dscr is not None else "n/a"),
        ("Gross rent multiplier", f"{r.gross_rent_multiplier:.1f}"),
        ("1% rule", "pass" if r.one_percent_rule else "fail"),
        ("Breakeven rent", _money(r.breakeven_rent)),
    ])
    return 0


def cmd_flip(args: argparse.Namespace) -> int:
    r = analyze_flip(FlipDeal.from_dict(_load(args.file)))
    if args.json:
        print(json.dumps(r.to_dict(), indent=2))
        return 0
    _print_rows("Flip analysis", [
        ("Rehab (w/ contingency)", _money(r.total_rehab)),
        ("Loan amount", _money(r.loan_amount)),
        ("Financing costs", _money(r.financing_costs)),
        ("Holding costs", _money(r.holding_costs)),
        ("Buy closing", _money(r.buy_closing)),
        ("Selling costs", _money(r.sell_costs)),
        ("Total project cost", _money(r.total_project_cost)),
        ("Cash required", _money(r.cash_required)),
        ("Net profit", _money(r.net_profit)),
        ("ROI on cash", _pct(r.roi_on_cash)),
        ("Annualized ROI", _pct(r.annualized_roi)),
        ("Margin on ARV", _pct(r.profit_margin_on_arv)),
        ("70% rule max offer", _money(r.seventy_percent_rule_max)),
        ("70% rule", "pass" if r.passes_seventy_percent_rule else "fail"),
    ])
    return 0


def cmd_refi(args: argparse.Namespace) -> int:
    r = analyze_refi(RefiScenario.from_dict(_load(args.file)))
    if args.json:
        print(json.dumps(r.to_dict(), indent=2))
        return 0
    _print_rows("Refinance analysis", [
        ("Max loan by LTV", _money(r.ltv_max_loan)),
        ("Max loan by DSCR", _money(r.dscr_max_loan)),
        ("New loan", f"{_money(r.new_loan_amount)} ({r.binding_constraint}-limited)"),
        ("Closing costs", _money(r.closing_costs)),
        ("Cash out", _money(r.cash_out)),
        ("Cash left in deal", _money(r.cash_left_in_deal)),
        ("New P&I / mo", _money(r.new_monthly_payment)),
        ("DSCR (rent / PITIA)", f"{r.dscr:.2f}"),
        ("Meets min DSCR", "yes" if r.meets_min_dscr else "no"),
    ])
    return 0


def cmd_amortize(args: argparse.Namespace) -> int:
    rows = amortization_schedule(args.principal, args.rate, args.years)
    if args.months:
        rows = rows[: args.months]
    print(f"{'Month':>5} {'Payment':>12} {'Principal':>12} {'Interest':>12} {'Balance':>14}")
    for row in rows:
        print(f"{row.month:>5} {row.payment:>12,.2f} {row.principal:>12,.2f} {row.interest:>12,.2f} {row.balance:>14,.2f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="deal-analyzer", description="Underwrite real estate deals.")
    sub = p.add_subparsers(dest="command", required=True)

    for name, fn, help_ in [
        ("rental", cmd_rental, "Buy-and-hold rental analysis"),
        ("flip", cmd_flip, "Fix-and-flip analysis"),
        ("refi", cmd_refi, "Cash-out / DSCR refinance sizing"),
    ]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("file", help="JSON file with deal inputs")
        sp.add_argument("--json", action="store_true", help="Output raw JSON")
        sp.set_defaults(func=fn)

    am = sub.add_parser("amortize", help="Print an amortization schedule")
    am.add_argument("principal", type=float)
    am.add_argument("rate", type=float, help="Annual rate as decimal, e.g. 0.07")
    am.add_argument("years", type=int)
    am.add_argument("--months", type=int, default=0, help="Only show first N months")
    am.set_defaults(func=cmd_amortize)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
