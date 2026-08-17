"""GET /admin/calibration/report + /predictor-data endpoint testleri."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import admin as admin_mod
from app.api.main import app

_SMALL = tuple(
    {
        "date": f"{'2020-01' if i < 20 else '2022-08'}-{i % 9 + 1:02d}",
        "home": "A" if i % 2 == 0 else "B",
        "away": "B" if i % 2 == 0 else "A",
        "hg": 2 if i % 2 == 0 else 0,
        "ag": 0 if i % 2 == 0 else 2,
        "comp": "xx.1",
    }
    for i in range(28)
)


@pytest.fixture()
def client(monkeypatch):
    import app.data.backtest_results as br

    monkeypatch.setattr(br, "load_match_results", lambda: _SMALL)
    admin_mod._cached_calibration_report.cache_clear()
    admin_mod._cached_predictor_data.cache_clear()
    try:
        yield TestClient(app)
    finally:
        admin_mod._cached_calibration_report.cache_clear()
        admin_mod._cached_predictor_data.cache_clear()


def test_report_endpoint_shape(client):
    r = client.get("/admin/calibration/report")
    assert r.status_code == 200
    body = r.json()
    assert body["matches"] + body["trainMatches"] == 28
    assert "trust" in body
    assert [m["key"] for m in body["markets"]] == [
        "result", "over", "btts", "lineup", "injury",
    ]
    assert body["params"]["rho"] == pytest.approx(-0.08)


def test_report_endpoint_cached(client):
    a = client.get("/admin/calibration/report").json()
    b = client.get("/admin/calibration/report").json()
    assert a == b
    assert admin_mod._cached_calibration_report.cache_info().hits >= 1


def test_predictor_data_endpoint(client):
    r = client.get("/admin/calibration/predictor-data")
    assert r.status_code == 200
    leagues = r.json()["leagues"]
    assert len(leagues) == 1
    assert {t["name"] for t in leagues[0]["teams"]} == {"A", "B"}
    assert {"muH", "muA", "rho", "ensW"} <= set(leagues[0])
