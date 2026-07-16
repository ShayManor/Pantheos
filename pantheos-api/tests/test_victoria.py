"""VictoriaMetrics client — urllib mocked so no TSDB is needed."""
import contextlib
import io
import json
import urllib.request

import pytest

from app import victoria


@pytest.fixture(autouse=True)
def _reset_probe(monkeypatch):
    monkeypatch.setattr(victoria, "_probe_cache", (False, 0.0))


def _fake_urlopen(payload=None, exc=None):
    @contextlib.contextmanager
    def opener(url, timeout=None):
        if exc is not None:
            raise exc
        yield io.BytesIO(json.dumps(payload).encode("utf-8"))
    return opener


def test_base_url_env(monkeypatch):
    monkeypatch.setenv("PANTHEOS_VM_URL", "http://vm:9999/")
    assert victoria.base_url() == "http://vm:9999"


def test_available_true(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(payload={}))
    assert victoria.available() is True


def test_available_false_on_error(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(exc=OSError("refused")))
    assert victoria.available() is False


def test_available_uses_cache(monkeypatch):
    monkeypatch.setattr(victoria, "_probe_cache", (True, float("inf")))
    # urlopen would raise if called; cache short-circuits it.
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(exc=AssertionError("probed")))
    assert victoria.available() is True


def test_query_value(monkeypatch):
    payload = {"data": {"result": [{"value": [123, "4.5"]}]}}
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(payload=payload))
    assert victoria.query("up") == 4.5


def test_query_empty_result(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(payload={"data": {"result": []}}))
    assert victoria.query("up") is None


def test_query_error(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(exc=OSError()))
    assert victoria.query("up") is None


def test_query_range_buckets(monkeypatch):
    # now=1000; start=1000-1200=... step= (1200)/4=300. Two samples land in buckets 0 and 3.
    def opener_for(url, timeout=None):
        raise AssertionError

    calls = {"n": 0}

    @contextlib.contextmanager
    def opener(url, timeout=None):
        calls["n"] += 1
        if "query_range" in url:
            body = {"data": {"result": [{"values": [[400, "1"], [1300, "2"]]}]}}
        else:  # the time() instant query
            body = {"data": {"result": [{"value": [0, "1600"]}]}}
        yield io.BytesIO(json.dumps(body).encode("utf-8"))

    monkeypatch.setattr(urllib.request, "urlopen", opener)
    out = victoria.query_range("x", minutes=20, points=4)
    assert len(out) == 4
    assert out[0] == 1.0  # ts=400 → bucket 0
    assert 2.0 in out     # ts=1300 lands in a later bucket


def test_query_range_now_none(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(payload={"data": {"result": []}}))
    assert victoria.query_range("x") is None


def test_query_range_error(monkeypatch):
    calls = {"n": 0}

    @contextlib.contextmanager
    def opener(url, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            yield io.BytesIO(json.dumps({"data": {"result": [{"value": [0, "1600"]}]}}).encode())
        else:
            raise OSError("boom")

    monkeypatch.setattr(urllib.request, "urlopen", opener)
    assert victoria.query_range("x") is None


def test_query_range_empty(monkeypatch):
    @contextlib.contextmanager
    def opener(url, timeout=None):
        if "query_range" in url:
            body = {"data": {"result": []}}
        else:
            body = {"data": {"result": [{"value": [0, "1600"]}]}}
        yield io.BytesIO(json.dumps(body).encode())

    monkeypatch.setattr(urllib.request, "urlopen", opener)
    out = victoria.query_range("x", points=5)
    assert out == [0.0] * 5
