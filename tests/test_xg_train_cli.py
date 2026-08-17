"""xg.train CLI — --competitions/--max-matches plumbing testleri."""

from __future__ import annotations

import argparse
import sys

import pytest

from app.engine.xg import train as train_mod
from app.engine.xg.train import _parse_competitions


def test_parse_competitions_single():
    assert _parse_competitions("11:90") == [(11, 90)]


def test_parse_competitions_multi_with_spaces():
    assert _parse_competitions("11:90, 43:106") == [(11, 90), (43, 106)]


@pytest.mark.parametrize("raw", ["", "11", "11-90", "a:b", "11:90,,x"])
def test_parse_competitions_invalid(raw):
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_competitions(raw)


def test_cli_passes_competitions_and_max_matches(tmp_path, monkeypatch):
    """CLI argümanları _load_statsbomb_shots'a gerçekten ulaşıyor."""
    captured: dict = {}

    def _fake_load(*, competitions=None, max_matches=None):
        captured["competitions"] = competitions
        captured["max_matches"] = max_matches
        return train_mod.generate_synthetic_shots(n=300, seed=7)

    monkeypatch.setattr(train_mod, "_load_statsbomb_shots", _fake_load)
    out = tmp_path / "xg_test.pkl"
    monkeypatch.setattr(sys, "argv", [
        "train", "--output", str(out), "--source", "statsbomb_open",
        "--competitions", "11:4,43:106", "--max-matches", "5",
    ])
    assert train_mod.main() == 0
    assert captured["competitions"] == [(11, 4), (43, 106)]
    assert captured["max_matches"] == 5
    assert out.is_file()


def test_cli_synthetic_ignores_statsbomb_args(tmp_path, monkeypatch):
    called = False

    def _fake_load(**kw):
        nonlocal called
        called = True

    monkeypatch.setattr(train_mod, "_load_statsbomb_shots", _fake_load)
    out = tmp_path / "xg_syn.pkl"
    monkeypatch.setattr(sys, "argv", [
        "train", "--output", str(out), "--source", "synthetic", "--n", "300",
    ])
    assert train_mod.main() == 0
    assert called is False
    assert out.is_file()
