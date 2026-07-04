"""weekly_digest_email job'u — digest üret + e-posta kanalına gönder."""

from __future__ import annotations

from app.notifications.base import NotificationResult
from app.scheduler import jobs as jobs_module
from app.scheduler.registry import get


class _CtxSession:
    def __init__(self, s):
        self.s = s

    def __enter__(self):
        return self.s

    def __exit__(self, *a):
        return False


def test_weekly_digest_email_registered():
    spec = get("weekly_digest_email")
    assert callable(spec.handler)
    assert "e-posta" in spec.description


def test_weekly_digest_email_sends_formatted_text(session, monkeypatch):
    monkeypatch.setattr(jobs_module, "SessionLocal", lambda: _CtxSession(session))

    sent: list[dict] = []

    class _FakeChannel:
        def send(self, text, *, recipient=None, timeout_seconds=10.0):
            sent.append({"text": text, "recipient": recipient})
            return NotificationResult(channel="email", success=True, stub=True)

    import app.notifications.email as email_module
    monkeypatch.setattr(email_module, "EmailChannel", _FakeChannel)

    # Boş DB'de bile digest üretimi + gönderim düşmemeli (boş liderlik listeleri).
    jobs_module.weekly_digest_email_handler(
        league_external_id=203, recipient="td@kulup.com",
    )

    assert len(sent) == 1
    assert sent[0]["recipient"] == "td@kulup.com"
    # İlk satır e-posta konusu olur — lig kimliğini taşımalı.
    first_line = sent[0]["text"].splitlines()[0]
    assert "203" in first_line
    assert "Haftalık" in first_line


def test_weekly_digest_notify_sends_to_all_channels(session, monkeypatch):
    monkeypatch.setattr(jobs_module, "SessionLocal", lambda: _CtxSession(session))

    sent: list[str] = []

    class _FakeNotifier:
        def send_all(self, text, *, timeout_seconds=10.0):
            sent.append(text)
            return {
                "telegram": NotificationResult(channel="telegram", success=True, stub=True),
                "email": NotificationResult(channel="email", success=True, stub=True),
            }

    import app.notifications as notifications_module
    monkeypatch.setattr(
        notifications_module, "build_default_notifier", lambda: _FakeNotifier(),
    )

    jobs_module.weekly_digest_notify_handler(league_external_id=203)

    assert len(sent) == 1
    assert "203" in sent[0].splitlines()[0]


def test_weekly_digest_notify_registered():
    spec = get("weekly_digest_notify")
    assert callable(spec.handler)
    assert "kanal" in spec.description.lower()
