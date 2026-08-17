"""GET /admin/decisions/calibration — confidence ↔ outcome kalibrasyon testleri."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.db import models
from app.db.session import get_session
from app.sports import football


@pytest.fixture()
def client(session):
    session.info["tenant_id"] = "t-default"

    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _seed(session):
    now = datetime.now(UTC)
    session.add(models.Tenant(
        id="t-default", slug="t-default", name="X",
        settings_json="{}", active=True, created_at=now,
    ))
    session.commit()


def _decision(
    session,
    *,
    confidence: float | None,
    outcome: str,
    decision_type: str = "substitution",
    team_id: int = 11,
    created_days_ago: int = 1,
) -> None:
    now = datetime.now(UTC)
    session.add(models.Decision(
        sport=football.SPORT_NAME, tenant_id="t-default",
        match_external_id=8001, team_external_id=team_id,
        minute=60.0, period=2, decision_type=decision_type,
        recommended=True, confidence=confidence,
        outcome=outcome, created_at=now - timedelta(days=created_days_ago),
    ))
    session.commit()


def test_empty_ledger_returns_zero_report(session, client):
    _seed(session)
    r = client.get("/admin/decisions/calibration")
    assert r.status_code == 200
    body = r.json()
    assert body["n_evaluated"] == 0
    assert body["overall"]["n"] == 0
    assert body["by_decision_type"] == {}


def test_pending_and_no_confidence_rows_excluded(session, client):
    _seed(session)
    _decision(session, confidence=0.8, outcome="pending")
    _decision(session, confidence=None, outcome="positive")
    _decision(session, confidence=0.7, outcome="neutral")
    r = client.get("/admin/decisions/calibration")
    assert r.json()["n_evaluated"] == 0


def test_overall_and_per_type_reports(session, client):
    _seed(session)
    # substitution: 3 isabet, 1 kaçırma — hepsi 0.75 güvenle
    for outcome in ("positive", "positive", "positive", "negative"):
        _decision(session, confidence=0.75, outcome=outcome)
    # formation_change: 1 kaçırma, yüksek güvenle
    _decision(
        session, confidence=0.9, outcome="negative",
        decision_type="formation_change",
    )
    body = client.get("/admin/decisions/calibration").json()
    assert body["n_evaluated"] == 5
    assert body["overall"]["n"] == 5
    assert body["overall"]["observed_rate"] == pytest.approx(0.6)
    by_type = body["by_decision_type"]
    assert set(by_type) == {"substitution", "formation_change"}
    assert by_type["substitution"]["n"] == 4
    assert by_type["substitution"]["observed_rate"] == pytest.approx(0.75)
    # 0.75 güven ↔ 0.75 gerçekleşme → bin farkı 0, iyi kalibre
    assert by_type["substitution"]["well_calibrated"] is True
    assert by_type["formation_change"]["well_calibrated"] is False


def test_team_filter(session, client):
    _seed(session)
    _decision(session, confidence=0.6, outcome="positive", team_id=11)
    _decision(session, confidence=0.6, outcome="negative", team_id=22)
    body = client.get("/admin/decisions/calibration?team_id=11").json()
    assert body["n_evaluated"] == 1
    assert body["overall"]["observed_rate"] == pytest.approx(1.0)


def test_days_window(session, client):
    _seed(session)
    _decision(session, confidence=0.6, outcome="positive", created_days_ago=400)
    _decision(session, confidence=0.6, outcome="positive", created_days_ago=1)
    body = client.get("/admin/decisions/calibration?days=30").json()
    assert body["n_evaluated"] == 1


def test_calibration_bins_present(session, client):
    _seed(session)
    for conf, outcome in [
        (0.9, "positive"), (0.9, "positive"), (0.9, "negative"),
        (0.3, "negative"), (0.3, "positive"), (0.3, "negative"),
    ]:
        _decision(session, confidence=conf, outcome=outcome)
    body = client.get("/admin/decisions/calibration").json()
    bins = body["overall"]["bins"]
    assert len(bins) == 2  # 0.2-0.4 ve 0.8-1.0 dolu
    assert all(
        {"lower", "upper", "n", "mean_predicted", "observed_rate"} <= set(b)
        for b in bins
    )
