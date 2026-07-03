"""Skaut raporu PDF export — builder + POST /reports/scout/pdf.

reportlab opsiyonel: kurulu değilse atlanır.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.reports.pdf import REPORTLAB_AVAILABLE

if not REPORTLAB_AVAILABLE:  # pragma: no cover
    pytest.skip("reportlab kurulu değil", allow_module_level=True)

from app.reports.pdf import build_scout_report_pdf  # noqa: E402

SAMPLE = {
    "player": "Mateo Ferreira", "pos": "Sol Kanat", "age": 19,
    "club": "CA Rosario", "scout": "H. Demir", "date": "2026-06-05",
    "rating": 4.5, "watches": 6, "rec": "İmzala",
    "summary": "Sol ayağı güçlü, 1v1'de etkili.",
}


def test_builder_returns_pdf_bytes():
    pdf = build_scout_report_pdf(reports=[SAMPLE], club_name="Beşiktaş")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_builder_rejects_empty_list():
    with pytest.raises(ValueError):
        build_scout_report_pdf(reports=[])


@pytest.fixture()
def client():
    return TestClient(app)


def test_endpoint_returns_pdf(client):
    r = client.post("/reports/scout/pdf", json={"reports": [SAMPLE]})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


def test_endpoint_rejects_empty_and_oversize(client):
    assert client.post("/reports/scout/pdf", json={"reports": []}).status_code == 400
    too_many = {"reports": [SAMPLE] * 51}
    assert client.post("/reports/scout/pdf", json=too_many).status_code == 400
