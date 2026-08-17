"""engine.strength — walk-forward güç modeli + kalibrasyon backtest testleri."""

from __future__ import annotations

import pytest

from app.engine.strength import (
    SPLIT,
    compute_calibration_report,
    predictor_data,
    run_core,
    run_elo,
)
from app.engine.strength.compute import (
    _blend_ledgers,
    _bootstrap_ci,
    _metrics_of,
    _probs,
)

TRAIN_DAY = "2020-01-{:02d}"
TEST_DAY = "2022-08-{:02d}"


def _match(date, home, away, hg, ag, comp="xx.1", hst=None, ast=None):
    m = {"date": date, "home": home, "away": away, "hg": hg, "ag": ag, "comp": comp}
    if hst is not None:
        m["hst"] = hst
    if ast is not None:
        m["ast"] = ast
    return m


def _season(n_train=30, n_test=10):
    """Sentetik veri: Kartal hep 3-0 kazanır, Leylek hep kaybeder."""
    ms = []
    for i in range(n_train):
        home, away = ("Kartal", "Leylek") if i % 2 == 0 else ("Leylek", "Kartal")
        hg, ag = (3, 0) if home == "Kartal" else (0, 3)
        ms.append(_match(TRAIN_DAY.format(i % 28 + 1), home, away, hg, ag,
                         hst=hg * 2, ast=ag * 2))
    for i in range(n_test):
        home, away = ("Kartal", "Leylek") if i % 2 == 0 else ("Leylek", "Kartal")
        hg, ag = (3, 0) if home == "Kartal" else (0, 3)
        ms.append(_match(TEST_DAY.format(i % 28 + 1), home, away, hg, ag,
                         hst=hg * 2, ast=ag * 2))
    return ms


# ----------------------------------------------------------------- bootstrap

def test_bootstrap_deterministic_and_ordered():
    rows = [
        {"pH": 0.5, "pD": 0.3, "pA": 0.2, "actual": "H", "hit": True},
        {"pH": 0.2, "pD": 0.3, "pA": 0.5, "actual": "A", "hit": True},
        {"pH": 0.6, "pD": 0.2, "pA": 0.2, "actual": "D", "hit": False},
    ] * 10
    a = _bootstrap_ci(rows, b=100)
    b = _bootstrap_ci(rows, b=100)
    assert a == b  # sabit seed → deterministik
    for key in ("accuracy", "brier", "logLoss", "ece"):
        lo, hi = a[key]
        assert lo <= hi


# --------------------------------------------------------------------- probs

def test_probs_sum_to_one():
    p = _probs(1.4, 1.1, -0.08)
    assert sum(p) == pytest.approx(1.0)


def test_dixon_coles_bumps_draw():
    """Negatif ρ → beraberlik payı saf Poisson'a göre artar."""
    _, pd_dc, _ = _probs(1.0, 1.0, -0.08)
    _, pd_pure, _ = _probs(1.0, 1.0, 0.0)
    assert pd_dc > pd_pure


# ------------------------------------------------------------------ run_core

def test_walk_forward_learns_strengths():
    """Hep kazanan takım pozitif atk+def gücü biriktirir."""
    st = run_core(_season())
    k = "xx.1|Kartal"
    le = "xx.1|Leylek"
    assert st["atk"][k] + st["def"][k] > st["atk"][le] + st["def"][le]
    assert len(st["ledger"]) == 40


def test_first_match_prediction_is_league_base():
    """İlk maçta güçler 0 — tahmin sadece lig tabanından gelir (sızıntı yok)."""
    ms = _season()
    st = run_core(ms)
    first = st["ledger"][0]
    # Güç öğrenilmeden favori ilan edilemez: ev olasılığı deplasmanın
    # ezici üstünlüğünü henüz bilemez
    assert first["pH"] > 0.15


def test_ledger_rows_have_markets():
    row = run_core(_season())["ledger"][0]
    assert set(("pOver", "pBTTS", "yOver", "yBTTS")) <= set(row)


# ---------------------------------------------------------------- blend fix

def test_blend_market_passthrough_when_other_has_no_opinion():
    """Elo defteri market üretmez → ensemble marketi AD'ninkiyle AYNI kalmalı
    (0 ile harman olasılığı 0.7× küçültüp kalibrasyonu bozuyordu)."""
    ms = _season()
    ad = run_core(ms)["ledger"]
    elo = run_elo(ms)
    ens = _blend_ledgers(ad, elo, 0.7)
    assert ens[0]["pOver"] == pytest.approx(ad[0]["pOver"], abs=1e-4)
    assert ens[0]["pBTTS"] == pytest.approx(ad[0]["pBTTS"], abs=1e-4)


# ------------------------------------------------------------------ metrics

def test_metrics_perfect_predictor():
    rows = [
        {"pH": 1.0, "pD": 0.0, "pA": 0.0, "actual": "H", "hit": True},
        {"pH": 0.0, "pD": 1.0, "pA": 0.0, "actual": "D", "hit": True},
    ]
    m = _metrics_of(rows, "t")
    assert m["accuracy"] == 1.0
    assert m["brier"] == pytest.approx(0.0)
    assert m["ece"] == pytest.approx(0.0)


# ------------------------------------------------------------------- report

def test_report_shape_and_determinism():
    ms = _season()
    r1 = compute_calibration_report(ms)
    r2 = compute_calibration_report(ms)
    assert r1 == r2  # seeded bootstrap → tam deterministik
    assert r1["matches"] == 10
    assert r1["trainMatches"] == 30
    assert {"accuracy", "brier", "logLoss", "ece"} <= set(r1["ci"])
    assert [m["key"] for m in r1["markets"]] == [
        "result", "over", "btts", "lineup", "injury",
    ]
    assert r1["params"]["rho"] == pytest.approx(-0.08)


def test_report_dominant_team_high_accuracy():
    """Deterministik sezonda model test setinde yüksek isabet tutturmalı."""
    r = compute_calibration_report(_season())
    assert r["accuracy"] >= 0.8


# ------------------------------------------------------------ predictor_data

def test_predictor_data_last_season_teams_only():
    ms = _season()
    # Eski takım: sadece train'de görünür — çıktıda olmamalı
    ms.insert(0, _match("2019-01-01", "Emekli", "Kartal", 0, 5))
    pd = predictor_data(ms)
    assert len(pd) == 1
    names = {t["name"] for t in pd[0]["teams"]}
    assert names == {"Kartal", "Leylek"}
    ratings = [t["rating"] for t in pd[0]["teams"]]
    assert ratings == sorted(ratings, reverse=True)
    assert pd[0]["teams"][0]["name"] == "Kartal"


def test_split_boundary():
    assert SPLIT == "2022-07-01"
