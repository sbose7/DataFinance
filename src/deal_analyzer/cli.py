"""Command-line interface.

    deal-analyzer rental  examples/rental.json
    deal-analyzer flip    examples/flip.json --json
    deal-analyzer refi    examples/refi.json
    deal-analyzer brrrr   examples/brrrr.json
    deal-analyzer project examples/project.json --years 15 --csv hold.csv
    deal-analyzer compare rental examples/rental.json examples/rental_cheaper.json --sort-by cash_on_cash
    deal-analyzer sensitivity rental examples/rental.json \\
        --x interest_rate=0.06:0.08:0.005 --y monthly_rent=2600:3000:100 --metric monthly_cash_flow
    deal-analyzer amortize 240000 0.0725 30 --months 12
    deal-analyzer serve --port 8000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .compare import compare
from .finance import clean
from .kinds import KINDS, run, scalar_items
from .mortgage import amortization_schedule
from .sensitivity import parse_values, sensitivity

PCT_HINTS = ("rate", "roi", "cash_on_cash", "irr", "margin", "_pct", "growth", "appreciation", "ltv")
RATIO_HINTS = ("dscr", "multiplier", "multiple")
COUNT_FIELDS = {"year", "years", "month", "holding_months"}


def fmt(key: str, value) -> str:
    if value is None:
        return "n/a" if "dscr" in key or "irr" in key else "∞"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, str):
        return value
    if key in COUNT_FIELDS:
        return str(int(value))
    if any(h in key for h in RATIO_HINTS):
        return f"{value:.2f}"
    if any(h in key for h in PCT_HINTS):
        return f"{value * 100:.2f}%"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def label(key: str) -> str:
    special = {"noi": "NOI", "dscr": "DSCR", "roi": "ROI", "irr": "IRR", "arv": "ARV", "ltv": "LTV",
               "capex": "CapEx", "pct": "%", "acq": "acquisition"}
    s = " ".join(special.get(w, w) for w in key.split("_"))
    return s[0].upper() + s[1:]


def print_table(title: str, data: dict) -> None:
    rows = [(label(k), fmt(k, v)) for k, v in data.items()]
    width = max(len(k) for k, _ in rows)
    print(f"\n{title}\n{'-' * len(title)}")
    for k, v in rows:
        print(f"  {k.ljust(width)}  {v}")
    print()


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _dump(obj) -> None:
    print(json.dumps(clean(obj), indent=2))


# --- single-deal commands -------------------------------------------------

def cmd_single(args: argparse.Namespace) -> int:
    result = run(args.command, _load(args.file))
    if args.json:
        _dump(result)
        return 0
    print_table(f"{KINDS[args.command].title} analysis", scalar_items(result))
    return 0


def cmd_project(args: argparse.Namespace) -> int:
    inputs = _load(args.file)
    proj = inputs.setdefault("projection", {})
    for opt in ("years", "rent_growth", "expense_growth", "appreciation", "selling_cost_pct"):
        v = getattr(args, opt)
        if v is not None:
            proj[opt] = v
    result = run("project", inputs)

    if args.csv:
        rows = result["years"]
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    if args.json:
        _dump(result)
        return 0

    cols = [("year", "Yr"), ("gross_income", "Income"), ("noi", "NOI"), ("debt_service", "Debt"),
            ("cash_flow", "Cash flow"), ("loan_balance", "Loan bal"), ("property_value", "Value"),
            ("equity", "Equity"), ("cash_on_cash", "CoC")]
    table = [[h for _, h in cols]] + [[fmt(k, r[k]) for k, _ in cols] for r in result["years"]]
    widths = [max(len(row[i]) for row in table) for i in range(len(cols))]
    print("\nHold projection\n---------------")
    for i, row in enumerate(table):
        print("  " + "  ".join(c.rjust(widths[j]) for j, c in enumerate(row)))
        if i == 0:
            print("  " + "  ".join("-" * w for w in widths))
    summary = {k: result[k] for k in ("cash_invested", "sale_price", "selling_costs", "loan_payoff",
                                      "net_sale_proceeds", "total_cash_flow", "total_profit",
                                      "equity_multiple", "irr", "average_cash_on_cash")}
    print_table("Exit summary", summary)
    if args.csv:
        print(f"Wrote yearly table to {args.csv}")
    return 0


# --- multi-deal commands --------------------------------------------------

def cmd_compare(args: argparse.Namespace) -> int:
    deals = {Path(p).stem: _load(p) for p in args.files}
    result = compare(args.kind, deals, sort_by=args.sort_by, descending=not args.ascending)
    if args.json:
        _dump(result)
        return 0
    labels = result["labels"]
    rows = [["Metric"] + labels]
    for m, vals in result["metrics"].items():
        rows.append([label(m)] + [fmt(m, v) for v in vals])
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    title = f"{KINDS[args.kind].title} comparison"
    print(f"\n{title}\n{'-' * len(title)}")
    for i, r in enumerate(rows):
        print("  " + r[0].ljust(widths[0]) + "  " + "  ".join(c.rjust(widths[j + 1]) for j, c in enumerate(r[1:])))
        if i == 0:
            print("  " + "  ".join("-" * w for w in widths))
    print()
    return 0


def _axis(spec: str) -> tuple[str, list[float]]:
    if "=" not in spec:
        raise SystemExit(f"axis must look like field=start:stop:step or field=a,b,c (got {spec!r})")
    field, values = spec.split("=", 1)
    return field, parse_values(values)


def cmd_sensitivity(args: argparse.Namespace) -> int:
    xf, xv = _axis(args.x)
    yf, yv = _axis(args.y)
    try:
        grid = sensitivity(args.kind, _load(args.file), args.metric, xf, xv, yf, yv)
    except KeyError as e:
        raise SystemExit(str(e.args[0]))
    if args.json:
        _dump(grid.to_dict())
        return 0
    xleaf, yleaf = xf.split(".")[-1], yf.split(".")[-1]
    header = [f"{label(yleaf)} \\ {label(xleaf)}"] + [fmt(xleaf, v) for v in xv]
    rows = [header] + [[fmt(yleaf, y)] + [fmt(args.metric, c) for c in row] for y, row in zip(yv, grid.values)]
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    title = f"Sensitivity: {label(args.metric)}"
    print(f"\n{title}\n{'-' * len(title)}")
    for i, r in enumerate(rows):
        print("  " + r[0].ljust(widths[0]) + "  " + "  ".join(c.rjust(widths[j + 1]) for j, c in enumerate(r[1:])))
        if i == 0:
            print("  " + "  ".join("-" * w for w in widths))
    print()
    return 0


# --- utilities ------------------------------------------------------------

def cmd_amortize(args: argparse.Namespace) -> int:
    rows = amortization_schedule(args.principal, args.rate, args.years)
    if args.months:
        rows = rows[: args.months]
    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["month", "payment", "principal", "interest", "balance"])
            for r in rows:
                w.writerow([r.month, round(r.payment, 2), round(r.principal, 2), round(r.interest, 2), round(r.balance, 2)])
        print(f"Wrote {len(rows)} rows to {args.csv}")
        return 0
    print(f"{'Month':>5} {'Payment':>12} {'Principal':>12} {'Interest':>12} {'Balance':>14}")
    for row in rows:
        print(f"{row.month:>5} {row.payment:>12,.2f} {row.principal:>12,.2f} {row.interest:>12,.2f} {row.balance:>14,.2f}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import serve
    serve(args.host, args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="deal-analyzer", description="Underwrite real estate deals.")
    sub = p.add_subparsers(dest="command", required=True)

    for name in ("rental", "flip", "refi", "brrrr"):
        sp = sub.add_parser(name, help=f"{KINDS[name].title} analysis")
        sp.add_argument("file", help="JSON file with deal inputs")
        sp.add_argument("--json", action="store_true", help="Output raw JSON")
        sp.set_defaults(func=cmd_single)

    pj = sub.add_parser("project", help="Multi-year hold projection with IRR")
    pj.add_argument("file", help="Rental JSON, optionally with a 'projection' object")
    pj.add_argument("--years", type=int)
    pj.add_argument("--rent-growth", dest="rent_growth", type=float)
    pj.add_argument("--expense-growth", dest="expense_growth", type=float)
    pj.add_argument("--appreciation", type=float)
    pj.add_argument("--selling-cost-pct", dest="selling_cost_pct", type=float)
    pj.add_argument("--csv", help="Write the yearly table to this CSV file")
    pj.add_argument("--json", action="store_true")
    pj.set_defaults(func=cmd_project)

    cp = sub.add_parser("compare", help="Compare several deals side by side")
    cp.add_argument("kind", choices=list(KINDS))
    cp.add_argument("files", nargs="+")
    cp.add_argument("--sort-by", dest="sort_by", help="Metric to rank deals by (best first)")
    cp.add_argument("--ascending", action="store_true", help="Sort lowest first")
    cp.add_argument("--json", action="store_true")
    cp.set_defaults(func=cmd_compare)

    se = sub.add_parser("sensitivity", help="Two-variable sensitivity table")
    se.add_argument("kind", choices=list(KINDS))
    se.add_argument("file")
    se.add_argument("--x", required=True, help="field=start:stop:step or field=a,b,c (columns)")
    se.add_argument("--y", required=True, help="field=start:stop:step or field=a,b,c (rows)")
    se.add_argument("--metric", required=True, help="Result field to show, e.g. monthly_cash_flow or irr")
    se.add_argument("--json", action="store_true")
    se.set_defaults(func=cmd_sensitivity)

    am = sub.add_parser("amortize", help="Print an amortization schedule")
    am.add_argument("principal", type=float)
    am.add_argument("rate", type=float, help="Annual rate as decimal, e.g. 0.07")
    am.add_argument("years", type=int)
    am.add_argument("--months", type=int, default=0, help="Only show first N months")
    am.add_argument("--csv", help="Write schedule to this CSV file instead")
    am.set_defaults(func=cmd_amortize)

    sv = sub.add_parser("serve", help="Run the local web app")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8000)
    sv.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
