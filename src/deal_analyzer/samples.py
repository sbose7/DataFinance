"""Sample inputs for each analysis kind (used by the web app; mirrors examples/)."""

SAMPLES = {
    "rental": {
        "purchase_price": 320000, "monthly_rent": 2800, "down_payment_pct": 0.25,
        "interest_rate": 0.0725, "loan_years": 30, "closing_costs": 8000, "rehab_costs": 5000,
        "property_tax": 4200, "insurance": 1500,
    },
    "flip": {
        "purchase_price": 280000, "arv": 450000, "rehab_costs": 60000, "holding_months": 6,
        "loan_to_cost": 0.85, "loan_rate": 0.11, "loan_points": 0.02, "monthly_holding": 900,
    },
    "refi": {
        "appraised_value": 450000, "existing_loan_balance": 289000, "total_cash_in_deal": 85000,
        "monthly_rent": 3200, "monthly_expenses_ex_debt": 600,
    },
    "brrrr": {
        "purchase_price": 210000, "rehab_costs": 55000, "arv": 360000, "monthly_rent": 2700,
        "holding_months": 5, "monthly_holding": 700, "refi_rate": 0.0725,
        "property_tax": 3800, "insurance": 1400,
    },
    "project": {
        "purchase_price": 320000, "monthly_rent": 2800, "down_payment_pct": 0.25,
        "interest_rate": 0.0725, "loan_years": 30, "closing_costs": 8000, "rehab_costs": 5000,
        "property_tax": 4200, "insurance": 1500,
        "projection": {"years": 10, "appreciation": 0.035},
    },
}
