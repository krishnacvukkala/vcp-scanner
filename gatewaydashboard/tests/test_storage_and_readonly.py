"""Regression tests for the two things that broke the hosted dashboard.

1. A read-only filesystem must not fail a scan. This is the exact bug that
   returned 500 from /api/scan on Vercel: an unguarded mkdir inside the cache
   writer, on a deployment filesystem where only /tmp is writable.

2. The Supabase round trip must give the dashboard back the same payload shape
   a live scan produces — otherwise a stored scan renders differently from a
   live one and there are two rendering paths to keep correct instead of one.

The Supabase test runs against a stub PostgREST server in-process, so it needs
no account, no network and no keys.

    python -m pytest gatewaydashboard/tests/test_storage_and_readonly.py -v
"""

from __future__ import annotations

import os
import sys
import threading
from datetime import datetime, timezone
from wsgiref.simple_server import make_server

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# 1. Read-only filesystem
# ---------------------------------------------------------------------------

@pytest.fixture()
def read_only_fs(monkeypatch):
    """Make every mkdir and file write raise Errno 30, the way Vercel's
    deployment filesystem does. Simulated rather than done with chmod,
    because tests often run as root, and root ignores permission bits."""
    from pathlib import Path

    def deny(*args, **kwargs):
        raise OSError(30, "Read-only file system")

    monkeypatch.setattr(Path, "mkdir", deny)
    monkeypatch.setattr("pandas.DataFrame.to_csv", deny)
    return deny


def test_price_cache_write_survives_read_only_filesystem(tmp_path, monkeypatch,
                                                          read_only_fs):
    import data
    import pandas as pd

    monkeypatch.setattr(data, "CACHE_PATH", tmp_path / "cache")
    frame = pd.DataFrame(
        {"Open": [1.0], "High": [1.0], "Low": [1.0], "Close": [1.0], "Volume": [1]},
        index=pd.to_datetime(["2026-01-01"]),
    )

    data._write_cache("RELIANCE", frame)          # must not raise
    assert not (tmp_path / "cache").exists()


def test_fundamentals_cache_path_survives_read_only_filesystem(tmp_path, monkeypatch,
                                                                read_only_fs):
    import fundamentals

    monkeypatch.setattr(fundamentals, "FUND_CACHE_DIR", tmp_path / "fundamentals")

    path = fundamentals._fund_cache_file("RELIANCE")   # must not raise
    assert path.name == "RELIANCE.pkl"
    assert fundamentals._read_fund_cache("RELIANCE") is None


def test_cache_moves_to_tmp_on_serverless(monkeypatch):
    """VERCEL=1 must relocate the cache off the read-only deployment tree."""
    import importlib
    monkeypatch.setenv("VERCEL", "1")
    config = importlib.reload(importlib.import_module("config"))
    try:
        assert config.ON_SERVERLESS is True
        assert config.CACHE_DIR.startswith("/tmp")
    finally:
        monkeypatch.delenv("VERCEL", raising=False)
        importlib.reload(config)


# ---------------------------------------------------------------------------
# 2. Supabase round trip, against a stub PostgREST
# ---------------------------------------------------------------------------

class _StubPostgrest:
    """The slice of PostgREST that store.py actually uses."""

    def __init__(self):
        self.tables: dict[str, list[dict]] = {
            "scan_runs": [], "scan_results": [],
            "ohlcv_cache": [], "fundamentals_cache": [],
        }

    def __call__(self, environ, start_response):
        import json
        from urllib.parse import parse_qs

        table = environ["PATH_INFO"].rsplit("/", 1)[-1]
        method = environ["REQUEST_METHOD"]
        query = parse_qs(environ.get("QUERY_STRING", ""))
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = json.loads(environ["wsgi.input"].read(length)) if length else None
        rows = self.tables.setdefault(table, [])

        def respond(payload, status="200 OK"):
            data = json.dumps(payload).encode()
            start_response(status, [("Content-Type", "application/json"),
                                    ("Content-Length", str(len(data)))])
            return [data]

        if method == "POST":
            incoming = body if isinstance(body, list) else [body]
            inserted = []
            for raw in incoming:
                row = dict(raw)
                if table == "scan_runs":
                    row.setdefault("id", f"run-{len(rows) + 1}")
                else:
                    key = ("run_id", "symbol") if table == "scan_results" else ("symbol", "timeframe")
                    rows[:] = [r for r in rows
                               if any(r.get(k) != row.get(k) for k in key)]
                rows.append(row)
                inserted.append(row)
            return respond(inserted)

        if method == "PATCH":
            raw_id = query.get("id", ["eq."])[0]
            target = raw_id[3:] if raw_id.startswith("eq.") else raw_id
            for row in rows:
                if row.get("id") == target:
                    row.update(body)
            return respond([])

        # GET
        matched = rows
        for field, values in query.items():
            if field in ("select", "order", "limit"):
                continue
            v0 = values[0]
            wanted = v0[3:] if v0.startswith("eq.") else v0
            matched = [r for r in matched if str(r.get(field)) == wanted]
        if "order" in query and matched:
            field = query["order"][0].split(".")[0]
            reverse = query["order"][0].endswith(".desc")
            matched = sorted(matched, key=lambda r: str(r.get(field) or ""),
                             reverse=reverse)
        if "limit" in query:
            matched = matched[: int(query["limit"][0])]
        return respond(matched)


@pytest.fixture()
def stub_supabase(monkeypatch):
    stub = _StubPostgrest()
    server = make_server("127.0.0.1", 0, stub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    import config
    import store
    monkeypatch.setattr(config, "SUPABASE_URL",
                        f"http://127.0.0.1:{server.server_address[1]}")
    monkeypatch.setattr(config, "SUPABASE_SERVICE_ROLE_KEY", "stub-key")
    monkeypatch.setattr(config, "SUPABASE_ENABLED", True)
    yield stub, store
    server.shutdown()


def _record(symbol, verdict, close, pivot=None, stop=None):
    """A record shaped like vcp_core.evaluate() + scanner's enrichment."""
    return {
        "symbol": symbol, "name": f"{symbol} Ltd", "exchange": "NSE",
        "country": "India", "assetClass": "EQUITY", "currency": "INR",
        "verdict": verdict, "status": "forming", "as_of": "2026-09-05",
        "close": {"value": close, "origin": "confirmed"},
        "vcp": {"present": True, "waves": [{"depth_pct": 12.0},
                                            {"depth_pct": 6.0}]},
        "plan": {"available": True,
                 "pivot": {"value": pivot}, "stop": {"value": stop},
                 "distance_to_pivot_pct": {"value": -2.5},
                 "risk_pct": {"value": 7.1}},
        "gates": [], "prescreen": {"passed": True},
    }


def test_round_trip_preserves_the_live_scan_shape(stub_supabase):
    stub, store = stub_supabase

    records = [
        _record("RELIANCE", "valid_setup", 1400.0, pivot=1420.0, stop=1320.0),
        _record("TCS", "watch", 3100.0, pivot=3200.0, stop=3000.0),
        _record("INFY", "no_setup", 1500.0),
    ]
    live = {
        "universe_size": 3, "scanned": 3, "elapsed_seconds": 12.3,
        "hidden_by_prescreen": 0,
        "counts": {"valid_setup": 1, "watch": 1, "no_setup": 1},
        "settings": {"fundamentals": True}, "user_parameters": ["SWING_WINDOW"],
        "caveats": ["§11: no short setup."], "failures": [],
        "results": records,
    }

    run_id = store.start_run(datetime.now(tz=timezone.utc), source="pytest")
    assert store.save_results(run_id, records) == 3
    store.finish_run(run_id, live, source="pytest")

    stored = store.latest_scan()
    assert stored is not None

    # The keys the dashboard reads must all survive the round trip.
    for key in ("as_of", "results", "categorized", "counts", "settings",
                "user_parameters", "caveats", "failures", "universe_size",
                "scanned", "hidden_by_prescreen"):
        assert key in stored, f"stored payload is missing {key!r}"

    assert {r["symbol"] for r in stored["results"]} == {"RELIANCE", "TCS", "INFY"}
    assert stored["counts"] == live["counts"]
    assert stored["categorized"]["by_verdict"]["valid_setup"][0]["symbol"] == "RELIANCE"

    # Records come back byte-identical — a stored verdict is the engine's own.
    original = {r["symbol"]: r for r in records}
    for result in stored["results"]:
        assert result == original[result["symbol"]]

    # And the payload says it is stored, with an age, so the UI can be honest.
    assert stored["is_stored"] is True
    assert stored["stored"]["age_hours"] is not None
    assert stored["stored"]["stale"] is False
    assert "Stored scan from" in stored["caveats"][0]


def test_ordering_is_the_scanners_not_the_databases(stub_supabase):
    stub, store = stub_supabase
    import scanner

    records = [_record("ZZZ", "no_setup", 10.0),
               _record("AAA", "valid_setup", 20.0, pivot=21.0, stop=19.0)]
    run_id = store.start_run(datetime.now(tz=timezone.utc))
    store.save_results(run_id, records)
    store.finish_run(run_id, {"results": records, "counts": {}})

    stored = store.latest_scan()
    assert [r["symbol"] for r in stored["results"]] == ["AAA", "ZZZ"]
    assert scanner.VERDICT_RANK["valid_setup"] < scanner.VERDICT_RANK["no_setup"]


def test_incomplete_run_is_never_served(stub_supabase):
    """A job that dies mid-scan must not surface as an empty scan."""
    stub, store = stub_supabase
    store.start_run(datetime.now(tz=timezone.utc), source="pytest")   # left 'running'
    assert store.latest_scan() is None
    assert store.health()["latest_run"] is None


def test_failed_run_is_recorded_but_not_served(stub_supabase):
    stub, store = stub_supabase
    run_id = store.start_run(datetime.now(tz=timezone.utc))
    store.fail_run(run_id, "yfinance exploded")
    assert store.latest_scan() is None
    assert stub.tables["scan_runs"][0]["status"] == "failed"
    assert "yfinance" in stub.tables["scan_runs"][0]["error"]


def test_stale_scan_is_labelled_stale(stub_supabase, monkeypatch):
    stub, store = stub_supabase
    import config
    monkeypatch.setattr(config, "STORED_SCAN_STALE_HOURS", 24.0)

    records = [_record("RELIANCE", "valid_setup", 1400.0, 1420.0, 1320.0)]
    old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    run_id = store.start_run(old)
    store.save_results(run_id, records)
    store.finish_run(run_id, {"results": records, "counts": {}})

    stored = store.latest_scan()
    assert stored["stored"]["stale"] is True
    assert stored["caveats"][0].startswith("STALE:")


def test_promoted_columns_are_derived_not_invented(stub_supabase):
    """The flat columns exist for SQL filtering; they must agree with the
    record they were derived from, and be null where the engine had nothing."""
    stub, store = stub_supabase

    with_plan = _record("RELIANCE", "valid_setup", 1400.0, pivot=1420.0, stop=1320.0)
    without_plan = _record("INFY", "no_setup", 1500.0)          # pivot/stop are None

    run_id = store.start_run(datetime.now(tz=timezone.utc))
    store.save_results(run_id, [with_plan, without_plan])

    rows = {r["symbol"]: r for r in stub.tables["scan_results"]}
    assert rows["RELIANCE"]["pivot"] == 1420.0
    assert rows["RELIANCE"]["close"] == 1400.0
    assert rows["RELIANCE"]["contractions"] == 2
    assert rows["INFY"]["pivot"] is None, "a missing pivot must stay missing"
    assert rows["INFY"]["stop"] is None


def test_ohlcv_cache_round_trip(stub_supabase):
    stub, store = stub_supabase
    payload = {"symbol": "RELIANCE", "timeframe": "1D",
               "candles": [{"time": "2026-09-05", "open": 1, "high": 2,
                            "low": 0.5, "close": 1.5, "volume": 100}]}
    store.put_ohlcv("RELIANCE", payload, timeframe="1D", exchange="NSE")
    assert store.get_ohlcv("RELIANCE", "1D") == payload
    assert store.get_ohlcv("RELIANCE", "1W") is None          # different series
    assert store.get_ohlcv("RELIANCE", "1D", max_age_hours=0) is None   # too old


def test_store_is_a_no_op_when_unconfigured(monkeypatch):
    import config
    import store
    monkeypatch.setattr(config, "SUPABASE_ENABLED", False)
    assert store.enabled() is False
    assert store.health()["configured"] is False
    with pytest.raises(store.StoreError):
        store.latest_run()


# ---------------------------------------------------------------------------
# 3. The API served from storage
# ---------------------------------------------------------------------------

def test_api_scan_serves_the_stored_run(stub_supabase):
    stub, store = stub_supabase
    import app as A

    records = [_record("RELIANCE", "valid_setup", 1400.0, 1420.0, 1320.0)]
    run_id = store.start_run(datetime.now(tz=timezone.utc), source="pytest")
    store.save_results(run_id, records)
    store.finish_run(run_id, {"results": records, "scanned": 1,
                              "universe_size": 1,
                              "counts": {"valid_setup": 1}}, source="pytest")

    response = A.app.test_client().get("/api/scan")
    assert response.status_code == 200
    body = response.get_json()
    assert body["is_stored"] is True
    assert body["stored"]["source"] == "pytest"
    assert body["results"][0]["symbol"] == "RELIANCE"


def test_api_scan_on_serverless_without_data_explains_itself(monkeypatch):
    """No stored scan on a serverless host: a 503 that says what to do beats
    a timeout, and beats an empty table that looks like 'no setups today'."""
    import app as A
    import config
    monkeypatch.setattr(config, "ON_SERVERLESS", True)
    monkeypatch.setattr(config, "SUPABASE_ENABLED", False)

    response = A.app.test_client().get("/api/scan")
    assert response.status_code == 503
    body = response.get_json()
    assert body["error"] == "NO_STORED_SCAN"
    assert "Actions" in body["how_to_fix"]
    assert body["results"] == []
