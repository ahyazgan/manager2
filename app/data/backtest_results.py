"""Backtest maç sonuçları yükleyici — engine.strength'in veri kaynağı.

`app/data/static/match_results.json`: 5 büyük lig, 2017-2023, ~10.8k maç
(frontend/src/lib/match-results.json ile aynı içerik; model backend'e
taşındığı için kanonik kopya artık burada).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.engine.strength import MatchResult

_DATA_PATH = Path(__file__).resolve().parent / "static" / "match_results.json"


@lru_cache(maxsize=1)
def load_match_results() -> tuple[MatchResult, ...]:
    """Tarih-sıralı ham maç satırları (immutable — process başına 1 kez okunur)."""
    rows = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return tuple(sorted(rows, key=lambda m: m["date"]))
