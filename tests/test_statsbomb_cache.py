"""StatsBombOpen disk cache — hit/miss/atomik yazma/traversal testleri."""

from __future__ import annotations

import json

import pytest

from app.data.sources.statsbomb_open import StatsBombOpen


@pytest.fixture(autouse=True)
def _reset_breaker():
    StatsBombOpen._breaker = None
    yield
    StatsBombOpen._breaker = None


class _CountingClient:
    """httpx.Client sahtesi — çağrı sayar, sabit payload döner."""

    calls = 0
    payload: list = [{"match_id": 1}]

    def __init__(self, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, **kw):
        _CountingClient.calls += 1

        class _R:
            status_code = 200
            text = ""

            @staticmethod
            def json():
                return _CountingClient.payload

        return _R()


@pytest.fixture()
def counting_http(monkeypatch):
    _CountingClient.calls = 0
    monkeypatch.setattr(
        "app.data.sources.statsbomb_open.httpx.Client", _CountingClient
    )
    return _CountingClient


def test_cache_miss_fetches_and_writes(tmp_path, counting_http):
    adapter = StatsBombOpen(cache_dir=tmp_path)
    data = adapter._fetch_json("matches/11/4.json")
    assert data == [{"match_id": 1}]
    assert counting_http.calls == 1
    cached = tmp_path / "matches" / "11" / "4.json"
    assert cached.is_file()
    assert json.loads(cached.read_text(encoding="utf-8")) == [{"match_id": 1}]


def test_cache_hit_skips_network(tmp_path, counting_http):
    adapter = StatsBombOpen(cache_dir=tmp_path)
    adapter._fetch_json("events/100.json")
    assert counting_http.calls == 1
    # İkinci çağrı diskten dönmeli — HTTP sayacı artmaz
    data = adapter._fetch_json("events/100.json")
    assert data == [{"match_id": 1}]
    assert counting_http.calls == 1


def test_cache_shared_across_instances(tmp_path, counting_http):
    StatsBombOpen(cache_dir=tmp_path)._fetch_json("competitions.json")
    StatsBombOpen(cache_dir=tmp_path)._fetch_json("competitions.json")
    assert counting_http.calls == 1


def test_no_cache_dir_always_fetches(counting_http):
    adapter = StatsBombOpen(cache_dir=None)
    # Settings default'u boş — cache kapalı
    if adapter._cache_dir is not None:
        pytest.skip("STATSBOMB_CACHE_DIR set in environment")
    adapter._fetch_json("competitions.json")
    adapter._fetch_json("competitions.json")
    assert counting_http.calls == 2


def test_cache_env_default(tmp_path, counting_http, monkeypatch):
    """cache_dir verilmezse STATSBOMB_CACHE_DIR settings'ten okunur."""
    from app.core.config import get_settings

    monkeypatch.setenv("STATSBOMB_CACHE_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        adapter = StatsBombOpen()
        assert adapter._cache_dir == tmp_path
        adapter._fetch_json("competitions.json")
        assert (tmp_path / "competitions.json").is_file()
    finally:
        get_settings.cache_clear()


def test_traversal_path_not_cached(tmp_path, counting_http):
    """`..` içeren path cache dizini dışına yazamaz — cache bypass edilir."""
    adapter = StatsBombOpen(cache_dir=tmp_path)
    adapter._fetch_json("../evil.json")
    assert not (tmp_path.parent / "evil.json").exists()
    assert _CountingClient.calls == 1


def test_no_tmp_leftover_after_write(tmp_path, counting_http):
    adapter = StatsBombOpen(cache_dir=tmp_path)
    adapter._fetch_json("events/5.json")
    leftovers = list(tmp_path.rglob("*.tmp"))
    assert leftovers == []
