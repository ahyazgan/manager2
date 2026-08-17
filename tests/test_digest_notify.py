"""scheduler.digest_notify — haftalık digest bildirim testleri."""

from __future__ import annotations

from app.scheduler import digest_notify
from app.scheduler.digest_notify import (
    format_weekly_digest_message,
    notify_weekly_digest,
)

_OUTPUT = {
    "league_external_id": 203,
    "form_leaders": [
        {"team_external_id": 611, "points_per_game": 2.6},
        {"team_external_id": 607, "points_per_game": 2.2},
        {"team_external_id": 619, "points_per_game": 2.0},
        {"team_external_id": 622, "points_per_game": 1.8},
    ],
    "upcoming_matches": [{"match_id": 1}, {"match_id": 2}],
    "accuracy": {"brier_score": 0.58, "sample_count": 40},
    "ai_brief": "Lider değişmedi; bu hafta derbi var.",
}


def test_format_contains_key_sections():
    msg = format_weekly_digest_message(_OUTPUT, "özet satırı")
    assert "lig 203" in msg
    assert "özet satırı" in msg
    assert "#611" in msg and "#607" in msg and "#619" in msg
    assert "#622" not in msg  # ilk 3 lider
    assert "2 maç" in msg
    assert "Brier 0.58" in msg
    assert "derbi" in msg


def test_format_tolerates_empty_output():
    msg = format_weekly_digest_message({}, "")
    assert msg.startswith("📊")


def test_format_truncates_long_brief():
    out = dict(_OUTPUT, ai_brief="x" * 1000)
    msg = format_weekly_digest_message(out, "")
    assert "…" in msg
    assert len(msg) < 700


def test_notify_sends_when_channel_active(monkeypatch):
    sent: list[str] = []

    class _FakeNotifier:
        def active_channel_names(self):
            return ["email"]

        def send_all(self, text):
            sent.append(text)
            return {}

    import app.notifications as notif

    monkeypatch.setattr(notif, "build_default_notifier", lambda: _FakeNotifier())
    notify_weekly_digest(_OUTPUT, "özet")
    assert len(sent) == 1
    assert "lig 203" in sent[0]


def test_notify_noop_without_channels(monkeypatch):
    class _FakeNotifier:
        def active_channel_names(self):
            return []

        def send_all(self, text):  # pragma: no cover
            raise AssertionError("kanal yokken gönderilmemeli")

    import app.notifications as notif

    monkeypatch.setattr(notif, "build_default_notifier", lambda: _FakeNotifier())
    notify_weekly_digest(_OUTPUT, "özet")


def test_notify_swallows_channel_errors(monkeypatch, caplog):
    class _FakeNotifier:
        def active_channel_names(self):
            return ["telegram"]

        def send_all(self, text):
            raise RuntimeError("SMTP down")

    import app.notifications as notif

    monkeypatch.setattr(notif, "build_default_notifier", lambda: _FakeNotifier())
    notify_weekly_digest(_OUTPUT, "özet")  # exception yüzeye çıkmamalı
    assert digest_notify is not None
