"""Haftalık digest bildirimi — push/email teslimi (pull-only'den çıkış).

`run_weekly_digest` job'ı şimdiye dek sadece agent_outputs'a yazıyordu;
bu modül üretilen özeti yapılandırılmış kanallara (Email/Telegram/WhatsApp —
`app/notifications`) kısa, telefona uygun bir mesaj olarak iletir.

daily_brief._maybe_notify_brief ile aynı sözleşme: best-effort — kanal yoksa
no-op, gönderim hatası job'ı bozmaz.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

log = get_logger(__name__)

# ai_brief mesajda bu uzunlukta kırpılır (SMS/telegram tek ekran)
_BRIEF_MAX_CHARS = 400


def format_weekly_digest_message(output: dict[str, Any], summary: str) -> str:
    """WeeklyDigestAgent çıktısını kısa bildirim metnine çevir (saf)."""
    league = output.get("league_external_id", "?")
    lines = [f"📊 Haftalık özet — lig {league}"]
    if summary:
        lines.append(summary)

    leaders = output.get("form_leaders") or []
    if leaders:
        tops = ", ".join(
            f"#{item.get('team_external_id', '?')} "
            f"({item.get('points_per_game', '?')} p/maç)"
            for item in leaders[:3]
        )
        lines.append(f"Form liderleri: {tops}")

    upcoming = output.get("upcoming_matches") or []
    if upcoming:
        lines.append(f"Önümüzdeki hafta {len(upcoming)} maç var.")

    acc = output.get("accuracy") or {}
    if acc.get("sample_count"):
        lines.append(
            f"Tahmin kalibrasyonu: Brier {acc.get('brier_score')} "
            f"({acc['sample_count']} örnek)"
        )

    brief = (output.get("ai_brief") or "").strip()
    if brief:
        if len(brief) > _BRIEF_MAX_CHARS:
            brief = brief[: _BRIEF_MAX_CHARS - 1] + "…"
        lines.append(brief)
    return "\n".join(lines)


def notify_weekly_digest(output: dict[str, Any], summary: str) -> None:
    """Digest'i aktif bildirim kanallarına gönder (best-effort, no-op'lu)."""
    try:
        from app.notifications import build_default_notifier

        notifier = build_default_notifier()
        if not notifier.active_channel_names():
            return
        notifier.send_all(format_weekly_digest_message(output, summary))
    except Exception as e:  # noqa: BLE001 — bildirim digest job'ını bozmamalı
        log.warning("weekly digest bildirimi gönderilemedi: %s", e)
