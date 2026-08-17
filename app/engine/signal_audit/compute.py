"""Sinyal/gürültü + öngörü gücü metrikleri (saf fonksiyonlar).

İki soru ayrı ayrı cevaplanır:

1. **Varyans** (CV + takım-arası spread): metrik takımlar arasında ayrışıyor mu?
   Ayrışmayan metrik (herkese aynı sayı) bilgi taşımaz. Ama ayrışmak tek başına
   "işe yarar" demek değildir — gürültü de ayrışır.
2. **Concurrent IC** (Spearman rank korelasyonu, metrik ↔ maçın gol farkı):
   metrik maç sonucuyla ilişkili mi? Aynı maç içi ölçüm olduğu için buna
   "predictive" değil "concurrent" validity denir; k→k+1 walk-forward IC için
   takım başına yeterli maç serisi gerekir (StatsBomb Open La Liga verisi
   Barca-merkezli olduğundan burada mümkün değil).

CV, mean≈0 iken tanımsızdır (zero-sum metrikler, örn. match_dominance).
Eski sürüm bu durumda `inf` döndürüp sıralamanın tepesine oturuyordu;
artık `None` döner ve sıralama |IC|'ye dayanır.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

# Verdict eşikleri
_MIN_SAMPLES = 20
_MEAN_ZERO_EPS = 1e-6
_IC_MIN_PAIRS = 8

# IC gücü etiketleri: |IC| eşikleri (finans literatürü IC>0.05'i bile değerli
# sayar; burada tek-maç gürültüsü yüksek olduğundan eşikler daha muhafazakar)
_IC_STRONG = 0.30
_IC_WEAK = 0.15


@dataclass(frozen=True)
class SignalVerdict:
    """Bir motorun sezon audit özeti."""

    n_samples: int
    mean: float
    stdev: float
    cv: float | None  # mean≈0 ise None (tanımsız), inf değil
    team_spread: float
    n_teams: int
    ic: float | None  # Spearman(metrik, gol farkı); n<8 veya sabit seri → None
    ic_pairs: int
    verdict: str  # STRONG_SIGNAL | MODERATE | NO_SIGNAL | INSUFFICIENT_DATA
    predictive: str  # PREDICTIVE | WEAK | NONE | N/A


def _rank(values: list[float]) -> list[float]:
    """Ortalama-rank (tie'lar rank ortalaması alır) — Spearman için."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman_ic(pairs: list[tuple[float, float]]) -> float | None:
    """Spearman rank korelasyonu — (metrik, hedef) çiftleri.

    n < _IC_MIN_PAIRS veya iki seriden biri sabitse None (anlamsız).
    """
    if len(pairs) < _IC_MIN_PAIRS:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    rx = _rank(xs)
    ry = _rank(ys)
    mx = statistics.mean(rx)
    my = statistics.mean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx**0.5 * vy**0.5)


def _predictive_label(ic: float | None) -> str:
    if ic is None:
        return "N/A"
    a = abs(ic)
    if a >= _IC_STRONG:
        return "PREDICTIVE"
    if a >= _IC_WEAK:
        return "WEAK"
    return "NONE"


def audit_engine_signal(
    samples: list[float],
    team_means: dict[int, float],
    outcome_pairs: list[tuple[float, float]] | None = None,
) -> SignalVerdict:
    """Bir motorun tüm maç-takım örneklerinden sinyal kararı üret.

    `samples`: tüm maç-takım değerleri (takımlar birleşik).
    `team_means`: takım başına sezon ortalaması (spread için).
    `outcome_pairs`: (metrik değeri, o maçtaki gol farkı) çiftleri — IC için.
    """
    n = len(samples)
    mean = statistics.mean(samples) if samples else 0.0
    stdev = statistics.pstdev(samples) if n > 1 else 0.0
    cv = (stdev / abs(mean)) if abs(mean) > _MEAN_ZERO_EPS else None
    team_spread = (
        (max(team_means.values()) - min(team_means.values()))
        if len(team_means) > 1
        else 0.0
    )
    ic = spearman_ic(outcome_pairs or [])

    if n < _MIN_SAMPLES:
        verdict = "INSUFFICIENT_DATA"
    elif cv is None:
        # mean ≈ 0 (zero-sum metrikler) → mutlak stdev/spread'e bak
        verdict = (
            "STRONG_SIGNAL" if stdev > 0.5 or team_spread > 1.0 else "NO_SIGNAL"
        )
    elif cv < 0.05 and (team_spread / abs(mean)) < 0.10:
        verdict = "NO_SIGNAL"
    elif cv >= 0.30 or (team_spread / abs(mean)) >= 0.30:
        verdict = "STRONG_SIGNAL"
    else:
        verdict = "MODERATE"

    return SignalVerdict(
        n_samples=n,
        mean=round(mean, 4),
        stdev=round(stdev, 4),
        cv=round(cv, 4) if cv is not None else None,
        team_spread=round(team_spread, 4),
        n_teams=len(team_means),
        ic=round(ic, 4) if ic is not None else None,
        ic_pairs=len(outcome_pairs or []),
        verdict=verdict,
        predictive=_predictive_label(ic),
    )
