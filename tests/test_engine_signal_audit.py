"""engine.signal_audit — Spearman IC + sinyal verdict testleri."""

from __future__ import annotations

import pytest

from app.engine.signal_audit import audit_engine_signal, spearman_ic

# ---------------------------------------------------------------- spearman_ic

def test_ic_perfect_monotonic_positive():
    pairs = [(float(i), float(i * 2)) for i in range(10)]
    assert spearman_ic(pairs) == pytest.approx(1.0)


def test_ic_perfect_monotonic_negative():
    pairs = [(float(i), float(-i)) for i in range(10)]
    assert spearman_ic(pairs) == pytest.approx(-1.0)


def test_ic_nonlinear_but_monotonic_still_one():
    """Spearman rank-tabanlı — monoton nonlineer ilişki de 1.0."""
    pairs = [(float(i), float(i**3)) for i in range(1, 12)]
    assert spearman_ic(pairs) == pytest.approx(1.0)


def test_ic_too_few_pairs_none():
    pairs = [(1.0, 2.0)] * 7  # < 8 çift
    assert spearman_ic(pairs) is None


def test_ic_constant_series_none():
    pairs = [(5.0, float(i)) for i in range(10)]
    assert spearman_ic(pairs) is None
    pairs2 = [(float(i), 3.0) for i in range(10)]
    assert spearman_ic(pairs2) is None


def test_ic_with_ties_bounded():
    """Tie'lı seride ortalama-rank; sonuç [-1, 1] içinde kalmalı."""
    pairs = [(1.0, 0.0), (1.0, 1.0), (2.0, 1.0), (2.0, 2.0),
             (3.0, 2.0), (3.0, 3.0), (4.0, 3.0), (4.0, 4.0)]
    ic = spearman_ic(pairs)
    assert ic is not None
    assert -1.0 <= ic <= 1.0
    assert ic > 0.5  # belirgin pozitif ilişki


def test_ic_no_relation_near_zero():
    """Deterministik karışık seri → |IC| küçük."""
    xs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    ys = [5.0, 1.0, 8.0, 3.0, 10.0, 2.0, 7.0, 4.0, 6.0, 9.0]
    ic = spearman_ic(list(zip(xs, ys, strict=True)))
    assert ic is not None
    assert abs(ic) < 0.35


# -------------------------------------------------------- audit_engine_signal

def _samples(vals: list[float]) -> tuple[list[float], dict[int, float]]:
    """Tek takımlı basit örnek seti."""
    return vals, {1: sum(vals) / len(vals)}


def test_zero_mean_cv_is_none_not_inf():
    """Zero-sum metrik (mean≈0): CV None olmalı, inf değil."""
    vals = [-2.0, 2.0, -1.0, 1.0, -3.0, 3.0] * 4  # mean = 0, n=24
    v = audit_engine_signal(vals, {1: -1.0, 2: 1.0})
    assert v.cv is None
    assert v.verdict == "STRONG_SIGNAL"  # stdev > 0.5


def test_zero_mean_low_spread_no_signal():
    vals = [-0.01, 0.01] * 12
    v = audit_engine_signal(vals, {1: -0.01, 2: 0.01})
    assert v.cv is None
    assert v.verdict == "NO_SIGNAL"


def test_insufficient_data():
    v = audit_engine_signal([1.0, 2.0, 3.0], {1: 2.0})
    assert v.verdict == "INSUFFICIENT_DATA"


def test_flat_metric_no_signal():
    """Herkese aynı değer → CV≈0, spread≈0 → NO_SIGNAL."""
    vals = [10.0, 10.01, 9.99, 10.0] * 6
    v = audit_engine_signal(vals, {1: 10.0, 2: 10.001})
    assert v.verdict == "NO_SIGNAL"


def test_dispersed_metric_strong_signal():
    vals = [1.0, 5.0, 2.0, 8.0, 3.0, 9.0] * 4
    v = audit_engine_signal(vals, {1: 2.0, 2: 8.0})
    assert v.verdict == "STRONG_SIGNAL"


def test_predictive_labels():
    vals = [float(i) for i in range(24)]
    team_means = {1: 5.0, 2: 18.0}
    # Güçlü ilişki → PREDICTIVE
    strong = [(float(i), float(i)) for i in range(24)]
    v = audit_engine_signal(vals, team_means, strong)
    assert v.predictive == "PREDICTIVE"
    assert v.ic == pytest.approx(1.0)
    # Çift yok → N/A
    v2 = audit_engine_signal(vals, team_means, None)
    assert v2.predictive == "N/A"
    assert v2.ic is None
    assert v2.ic_pairs == 0


def test_verdict_independent_of_ic():
    """IC verdict'i değiştirmez — iki ayrı eksen olarak raporlanır."""
    vals = [1.0, 5.0, 2.0, 8.0, 3.0, 9.0] * 4
    strong_pairs = [(v, v) for v in vals]
    with_ic = audit_engine_signal(vals, {1: 2.0, 2: 8.0}, strong_pairs)
    without_ic = audit_engine_signal(vals, {1: 2.0, 2: 8.0})
    assert with_ic.verdict == without_ic.verdict
