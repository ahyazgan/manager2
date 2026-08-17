"""engine.signal_audit — motor sinyal/gürültü + öngörü gücü metrikleri.

`scripts/full_season_audit.py`'nin saf (DB'siz, HTTP'siz) metrik çekirdeği.
"""

from app.engine.signal_audit.compute import (
    SignalVerdict,
    audit_engine_signal,
    spearman_ic,
)

__all__ = ["SignalVerdict", "audit_engine_signal", "spearman_ic"]
