import pytest

from deal_analyzer.compare import compare
from deal_analyzer.kinds import KINDS, run, schema
from deal_analyzer.sensitivity import parse_values, sensitivity

RENTAL = {"purchase_price": 300_000, "monthly_rent": 2_600, "property_tax": 3_600, "insurance": 1_200}


def test_parse_values_range_and_list():
    assert parse_values("0.06:0.08:0.01") == [0.06, 0.07, 0.08]
    assert parse_values("1,2, 3") == [1.0, 2.0, 3.0]
    with pytest.raises(ValueError):
        parse_values("1:2:0")


def test_grid_shape_and_monotonic():
    g = sensitivity("rental", RENTAL, "monthly_cash_flow",
                    "interest_rate", [0.06, 0.07, 0.08], "monthly_rent", [2_400, 2_600])
    assert len(g.values) == 2 and len(g.values[0]) == 3
    assert g.values[0][0] > g.values[0][2]  # higher rate, less cash flow
    assert g.values[1][1] > g.values[0][1]  # more rent, more cash flow


def test_grid_cell_matches_direct_run():
    g = sensitivity("rental", RENTAL, "cap_rate", "monthly_rent", [2_700], "property_tax", [4_000])
    direct = run("rental", {**RENTAL, "monthly_rent": 2_700, "property_tax": 4_000})
    assert g.values[0][0] == pytest.approx(direct["cap_rate"])


def test_dotted_paths_for_projection():
    g = sensitivity("project", RENTAL, "irr", "projection.appreciation", [0.02, 0.05],
                    "projection.years", [5])
    assert g.values[0][1] > g.values[0][0]


def test_unknown_metric():
    with pytest.raises(KeyError):
        sensitivity("rental", RENTAL, "nope", "monthly_rent", [1], "property_tax", [1])


def test_compare_sorts():
    deals = {"cheap": {**RENTAL, "purchase_price": 250_000}, "pricey": {**RENTAL, "purchase_price": 350_000}}
    out = compare("rental", deals, sort_by="cash_on_cash")
    assert out["labels"] == ["cheap", "pricey"]
    assert len(out["metrics"]["cap_rate"]) == 2
    assert "expense_breakdown" not in out["metrics"]


def test_schema_covers_every_kind():
    s = schema()
    assert set(s) == set(KINDS)
    project_groups = {g["key"] for g in s["project"]["groups"]}
    assert project_groups == {None, "projection"}
    rental_fields = {f["name"]: f for f in s["rental"]["groups"][0]["fields"]}
    assert rental_fields["purchase_price"]["required"] is True
    assert rental_fields["interest_only"]["type"] == "bool"
    assert rental_fields["loan_years"]["type"] == "int"
