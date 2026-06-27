"""
test_api.py
===========
A simple smoke-test script for the running FastAPI server.
Run the server first (uvicorn main:app --reload --port 8000),
then run this script in a separate terminal:

    python test_api.py

Requires the 'requests' package (pip install requests --break-system-packages).
"""

import json
import requests

BASE_URL = "http://localhost:8000"


def test_health():
    res = requests.get(f"{BASE_URL}/api/health")
    print("GET /api/health ->", res.status_code, res.json())
    assert res.status_code == 200


def test_advise_example_from_spec():
    """The retirement/SIP example from the original project spec."""
    payload = {
        "age": 28,
        "goal": "retirement",
        "horizon": 30,
        "amount": 500,
        "mode": "sip",
        "risk_pref": "auto",
    }
    res = requests.post(f"{BASE_URL}/api/advise", json=payload)
    print("\nPOST /api/advise ->", res.status_code)
    data = res.json()
    print(json.dumps(data, indent=2))

    assert res.status_code == 200
    assert data["risk_profile"]["profile"] == "Aggressive"
    assert data["risk_profile"]["score"] >= 8.0

    equity_slice = next(s for s in data["allocation"]["slices"] if s["name"] == "Equity")
    assert equity_slice["pct"] >= 60

    crypto_slice = next((s for s in data["allocation"]["slices"] if s["name"] == "Crypto"), None)
    if crypto_slice:
        assert crypto_slice["pct"] <= 5  # hard cap


def test_validation_error():
    """Age out of range should return a 422 from FastAPI/Pydantic validation."""
    payload = {
        "age": 5,  # invalid: below minimum of 18
        "goal": "retirement",
        "horizon": 30,
        "amount": 500,
        "mode": "sip",
    }
    res = requests.post(f"{BASE_URL}/api/advise", json=payload)
    print("\nPOST /api/advise (invalid age) ->", res.status_code)
    assert res.status_code == 422


if __name__ == "__main__":
    test_health()
    test_advise_example_from_spec()
    test_validation_error()
    print("\nAll smoke tests passed.")
