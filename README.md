# DataFinance (deal-analyzer)

Underwrite real estate deals from the command line: buy-and-hold rentals, fix-and-flips, and cash-out / DSCR refinances (the BRRRR loop). Pure Python, no dependencies.

## Install

```bash
git clone https://github.com/sbose7/DataFinance.git
cd DataFinance
pip install -e ".[dev]"
```

## Usage

Each command takes a JSON file of inputs. See `examples/` for every field.

```bash
deal-analyzer rental examples/rental.json
deal-analyzer flip   examples/flip.json
deal-analyzer refi   examples/refi.json
deal-analyzer amortize 240000 0.0725 30 --months 12
```

Add `--json` to any analysis command for machine-readable output.

```
Refinance analysis
------------------
  Max loan by LTV      $337,500
  Max loan by DSCR     $371,846
  New loan             $337,500 (LTV-limited)
  Closing costs        $10,125
  Cash out             $38,375
  Cash left in deal    $46,625
  New P&I / mo         $2,360
  DSCR (rent / PITIA)  1.08
  Meets min DSCR       yes
```

## What it calculates

| Command | Metrics |
|---|---|
| `rental` | NOI, cash flow, cap rate, cash-on-cash, DSCR (NOI/debt), GRM, 1% rule, breakeven rent |
| `flip` | Total project cost, cash required, net profit, ROI and annualized ROI, margin on ARV, 70% rule max offer |
| `refi` | Loan sized by the tighter of LTV and DSCR, cash out, cash left in deal, post-refi DSCR (rent/PITIA) |
| `amortize` | Month-by-month principal, interest, balance |

### Assumptions worth knowing

- Rates and percentages are decimals (`0.07` = 7%).
- Rental expenses split into percent-of-rent (vacancy, maintenance, capex, management) and fixed (tax, insurance, HOA).
- Flip financing is modeled as interest-only hard money with points; set `loan_to_cost` to `0` for all cash. A rehab contingency (default 10%) is added on top of the rehab budget.
- Refi DSCR uses the common investor-loan definition, rent ÷ PITIA, where `monthly_expenses_ex_debt` is the T, I, and A.

## Use as a library

```python
from deal_analyzer import RentalDeal, analyze_rental

r = analyze_rental(RentalDeal(purchase_price=320_000, monthly_rent=2_800, property_tax=4_200, insurance=1_500))
print(r.monthly_cash_flow, r.cap_rate, r.dscr)
```

## Development

```bash
pytest
```

## Roadmap

- Multi-year projections (rent growth, appreciation, equity build, IRR)
- Sensitivity tables (rate × rent, ARV × rehab)
- Side-by-side deal comparison
- Web UI

## License

MIT
