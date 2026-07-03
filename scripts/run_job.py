"""Kayıtlı bir job'u tek seferlik çalıştır (dış cron buradan tetikler).

Kullanım:
    python scripts/run_job.py --list
    python scripts/run_job.py sync_league --league 203 --season 2024
    python scripts/run_job.py sync_league --league 203 --season 2024 --max-attempts 5
    # Diğer job'lara keyword argüman: --kw ad=değer (değer JSON olarak çözülür)
    python scripts/run_job.py weekly_digest_email --kw league_external_id=203
    python scripts/run_job.py run_weekly_digest --kw league_external_id=203 --kw lookback_days=14
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.scheduler import all_jobs, run_job  # noqa: E402

log = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheduler job runner")
    parser.add_argument("job", nargs="?", help="Job adı (örn. sync_league)")
    parser.add_argument("--list", action="store_true", help="Kayıtlı job'ları listele")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maks deneme")
    args, extra = parser.parse_known_args()

    setup_logging()

    if args.list:
        for spec in all_jobs():
            print(f"{spec.name}: {spec.description}")
        return

    if not args.job:
        parser.error("job adı zorunlu (`--list` ile bakabilirsiniz)")

    kwargs = _parse_job_args(args.job, extra)
    result = run_job(args.job, max_attempts=args.max_attempts, **kwargs)
    log.info(
        "job tamam: name=%s status=%s attempts=%d error=%s",
        result.job_name,
        result.status,
        result.attempts,
        result.error or "-",
    )
    if result.status != "success":
        sys.exit(1)


def _parse_job_args(job_name: str, extra: list[str]) -> dict:
    """Job'a özgü argümanları parse et."""
    if job_name == "sync_league":
        sub = argparse.ArgumentParser(prog=f"run_job {job_name}")
        sub.add_argument("--league", type=int, required=True)
        sub.add_argument("--season", type=int, required=True)
        sub.add_argument("--last", type=int, default=10)
        ns = sub.parse_args(extra)
        return {"league_id": ns.league, "season": ns.season, "last": ns.last}
    # Generic yol: her job `--kw ad=değer` alır (değer önce JSON denenip
    # çözülür: 203→int, true→bool, "x"→str; çözülmezse düz string kalır).
    sub = argparse.ArgumentParser(prog=f"run_job {job_name}")
    sub.add_argument("--kw", action="append", default=[], metavar="AD=DEĞER")
    ns = sub.parse_args(extra)
    kwargs: dict = {}
    for item in ns.kw:
        key, sep, raw = item.partition("=")
        if not sep or not key:
            raise SystemExit(f"--kw formatı ad=değer olmalı: {item!r}")
        try:
            kwargs[key] = json.loads(raw)
        except json.JSONDecodeError:
            kwargs[key] = raw
    return kwargs


if __name__ == "__main__":
    main()
