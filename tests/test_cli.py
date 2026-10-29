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


def test_amortize(capsys):
    main(["amortize", "100000", "0.06", "30", "--months", "2"])
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 3
