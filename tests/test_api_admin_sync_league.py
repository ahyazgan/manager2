"""POST /admin/sync-league — onboarding sync tetikleyicisi."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.db import models
from app.db.session import get_session


@pytest.fixture()
def client(session):
    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_sync_league_triggers_background_job(client, monkeypatch):
    from app.scheduler import runner as runner_module

    calls: list[dict] = []
    monkeypatch.setattr(
        runner_module, "run_job",
        lambda name, **kw: calls.append({"name": name, **kw}),
    )

    r = client.post("/admin/sync-league?league_id=203&season=2025&last=5")
    assert r.status_code == 200
    assert r.json()["status"] == "started"
    # TestClient background task'ı response sonrasında senkron koşturur.
    assert calls == [{"name": "sync_league", "league_id": 203, "season": 2025, "last": 5}]


def test_sync_league_skips_when_already_running(session, client, monkeypatch):
    from app.scheduler import runner as runner_module

    calls: list[str] = []
    monkeypatch.setattr(
        runner_module, "run_job", lambda name, **kw: calls.append(name),
    )
    session.add(
        models.JobRun(
            job_name="sync_league", args="{}",
            started_at=datetime.now(UTC), status="running", attempts=1,
        )
    )
    session.commit()

    r = client.post("/admin/sync-league")
    assert r.status_code == 200
    assert r.json()["status"] == "already_running"
    assert calls == []
