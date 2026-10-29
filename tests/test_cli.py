import json
from pathlib import Path

import pytest

from deal_analyzer.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.mark.parametrize("cmd", ["rental", "flip", "refi"])
def test_examples_run(cmd, capsys):
    assert main([cmd, str(EXAMPLES / f"{cmd}.json")]) == 0
    assert "analysis" in capsys.readouterr().out


@pytest.mark.parametrize("cmd", ["rental", "flip", "refi"])
def test_json_output(cmd, capsys):
    main([cmd, str(EXAMPLES / f"{cmd}.json"), "--json"])
    assert isinstance(json.loads(capsys.readouterr().out), dict)


@pytest.mark.parametrize("cmd", ["brrrr", "project"])
def test_new_examples_run(cmd, capsys):
    assert main([cmd, str(EXAMPLES / f"{cmd}.json")]) == 0
    out = capsys.readouterr().out
    assert "BRRRR analysis" in out or "Exit summary" in out


def test_project_overrides_and_csv(tmp_path, capsys):
    out_csv = tmp_path / "hold.csv"
    main(["project", str(EXAMPLES / "project.json"), "--years", "3", "--csv", str(out_csv), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert len(data["years"]) == 3
    assert len(out_csv.read_text().strip().splitlines()) == 4


def test_compare_cli(capsys):
    main(["compare", "rental", str(EXAMPLES / "rental.json"), str(EXAMPLES / "rental_cheaper.json"),
          "--sort-by", "cash_on_cash", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["labels"][0] == "rental_cheaper"


def test_sensitivity_cli(capsys):
    main(["sensitivity", "rental", str(EXAMPLES / "rental.json"),
          "--x", "interest_rate=0.06:0.07:0.005", "--y", "monthly_rent=2600,2800", "--metric", "monthly_cash_flow"])
    out = capsys.readouterr().out
    assert "Sensitivity" in out and "6.50%" in out


def test_sensitivity_bad_metric():
    with pytest.raises(SystemExit):
        main(["sensitivity", "rental", str(EXAMPLES / "rental.json"),
              "--x", "interest_rate=0.06", "--y", "monthly_rent=2600", "--metric", "nope"])


def test_amortize_csv(tmp_path):
    out = tmp_path / "a.csv"
    main(["amortize", "100000", "0.06", "30", "--csv", str(out)])
    assert len(out.read_text().strip().splitlines()) == 361


def test_amortize(capsys):
    main(["amortize", "100000", "0.06", "30", "--months", "2"])
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 3
