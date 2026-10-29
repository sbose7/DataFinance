import json
import threading
import urllib.error
import urllib.request

import pytest

from deal_analyzer.samples import SAMPLES
from deal_analyzer.server import make_server


@pytest.fixture(scope="module")
def base():
    httpd = make_server("127.0.0.1", 0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_index(base):
    status, ctype, body = get(base + "/")
    assert status == 200 and ctype.startswith("text/html")
    assert b"Deal Analyzer" in body


def test_schema_and_samples(base):
    _, _, s = get(base + "/api/schema")
    _, _, samples = get(base + "/api/samples")
    assert set(json.loads(s)) == set(json.loads(samples)) == set(SAMPLES)


@pytest.mark.parametrize("kind", list(SAMPLES))
def test_every_sample_runs(base, kind):
    status, data = post(f"{base}/api/run/{kind}", SAMPLES[kind])
    assert status == 200
    assert "error" not in data


def test_results_are_valid_json_even_with_infinity(base):
    # all cash rental: cash_on_cash is finite, dscr None; zero invested -> inf cash_on_cash
    status, data = post(base + "/api/run/rental", {"purchase_price": 100_000, "monthly_rent": 1_000, "down_payment_pct": 0})
    assert status == 200
    assert data["cash_on_cash"] is None


def test_sensitivity_endpoint(base):
    status, data = post(base + "/api/sensitivity", {
        "kind": "flip", "inputs": SAMPLES["flip"], "metric": "net_profit",
        "x_field": "arv", "x_values": [400_000, 450_000], "y_field": "rehab_costs", "y_values": [50_000, 70_000],
    })
    assert status == 200
    assert len(data["values"]) == 2


def test_errors_are_specific(base):
    assert post(base + "/api/run/nope", {})[0] == 404
    status, data = post(base + "/api/run/rental", {"monthly_rent": 1000})
    assert status == 400 and "purchase_price" in data["error"]
    status, data = post(base + "/api/sensitivity", {
        "kind": "rental", "inputs": SAMPLES["rental"], "metric": "monthly_cash_flow",
        "x_field": "monthly_rent", "x_values": list(range(30)), "y_field": "interest_rate", "y_values": list(range(30)),
    })
    assert status == 400 and "grid" in data["error"]
