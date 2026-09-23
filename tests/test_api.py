"""HTTP-level tests: validation must return 422 for unknown fields
or out-of-range values; valid requests return the rule payload."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.main import app  # noqa: E402

client = TestClient(app)


def post(payload):
    return client.post("/api/evaluate", json=payload)


def test_valid_request_stable():
    r = post({"target": 10, "sigma": 2, "readings": [10, 11, 10]})
    assert r.status_code == 200
    body = r.json()
    assert body["in_control"] is True
    assert body["violation"] is None
    assert len(body["points"]) == 3


def test_valid_request_violation():
    r = post({"target": 0, "sigma": 1, "readings": [0, 4]})
    assert r.status_code == 200
    v = r.json()["violation"]
    assert v["rule"] == 1 and v["evidence_indices"] == [1]


def test_unknown_field_rejected_422():
    r = post({"target": 0, "sigma": 1, "readings": [0, 1], "extra": 1})
    assert r.status_code == 422


def test_sigma_zero_rejected_422():
    r = post({"target": 0, "sigma": 0, "readings": [0, 1]})
    assert r.status_code == 422


def test_sigma_negative_rejected_422():
    r = post({"target": 0, "sigma": -3, "readings": [0, 1]})
    assert r.status_code == 422


@pytest.mark.parametrize("n", [0, 1, 201])
def test_readings_length_out_of_range_422(n):
    r = post({"target": 0, "sigma": 1, "readings": [0] * n})
    assert r.status_code == 422


def test_readings_length_bounds_accepted():
    r = post({"target": 0, "sigma": 1, "readings": [0, 1]})
    assert r.status_code == 200
    r = post({"target": 0, "sigma": 1, "readings": [5] * 200})
    assert r.status_code == 200


def test_missing_field_422():
    r = post({"target": 0, "readings": [0, 1]})
    assert r.status_code == 422


def test_wrong_type_422():
    r = post({"target": "10", "sigma": 2, "readings": [10, 11]})
    assert r.status_code == 422
    r = post({"target": 10, "sigma": 2, "readings": [10, "11"]})
    assert r.status_code == 422


def test_boolean_is_not_integer_422():
    r = post({"target": 10, "sigma": True, "readings": [10, 11]})
    assert r.status_code == 422


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
