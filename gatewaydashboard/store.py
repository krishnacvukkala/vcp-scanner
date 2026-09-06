"""Supabase persistence for scan runs, results and the data caches.

Why this module exists
----------------------
A full scan takes minutes: 160-odd symbols, a Yahoo download per batch and a
fundamentals call per candidate. That is fine on your own machine and
impossible inside a serverless request, which is why the hosted dashboard used
to fail rather than scan. So the work moves off the request path entirely:

    scheduled job (GitHub Actions)  ->  scans  ->  writes here
    hosted dashboard                ->  reads here  ->  answers in milliseconds

Nothing in this module decides anything. It stores what the engine produced and
hands it back unchanged; `record` is kept verbatim as JSON precisely so that a
stored result and a live one render identically.

Degrading honestly
------------------
With SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY unset the module reports
`enabled() is False` and every call becomes a no-op returning None. The app
then behaves exactly as it did before storage existed — live scans, nothing
persisted. A storage failure is never allowed to fail a scan, but it is also
never silently swallowed: writes raise `StoreError`, and the caller decides.
Reads return None so the caller can fall back to scanning live.

Transport is the PostgREST endpoint every Supabase project exposes, over
`requests` (already a yfinance dependency). No extra package, no SDK pin.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

import config

logger = logging.getLogger(__name__)

# PostgREST rejects very large request bodies, and a scan record is a fat
# object (every gate, wave and rule detail). 40 rows per POST keeps each body
# comfortably small while still making the whole write a handful of calls.
_ROWS_PER_WRITE = 40
_TIMEOUT = 20


class StoreError(RuntimeError):
    """A Supabase call failed. Carries the HTTP status and body."""


def enabled() -> bool:
    return bool(config.SUPABASE_ENABLED)


def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def _request(method: str, path: str, *, params=None, payload=None, prefer=None):
    if not enabled():
        raise StoreError("Supabase is not configured (SUPABASE_URL / "
                         "SUPABASE_SERVICE_ROLE_KEY are unset).")
    import requests

    url = f"{config.SUPABASE_URL}/rest/v1/{path}"
    response = requests.request(
        method,
        url,
        params=params,
        headers=_headers({"Prefer": prefer} if prefer else None),
        data=json.dumps(payload, default=str) if payload is not None else None,
        timeout=_TIMEOUT,
    )
    if response.status_code >= 400:
        raise StoreError(f"{method} {path} -> {response.status_code}: "
                         f"{response.text[:400]}")
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _chunks(rows: list, size: int) -> Iterable[list]:
    for start in range(0, len(rows), size):
        yield rows[start:start + size]


# ---------------------------------------------------------------------------
# Writing a scan
# ---------------------------------------------------------------------------

def start_run(started_at: datetime, source: str = "manual") -> str:
    """Open a run row and return its id. The row stays 'running' until
    finish_run, so a job that dies half way is visibly incomplete rather than
    looking like a scan that found nothing."""
    rows = _request(
        "POST", "scan_runs",
        payload=[{"started_at": started_at.isoformat(),
                  "status": "running",
                  "source": source}],
        prefer="return=representation",
    )
    return rows[0]["id"]


def _num(value):
    """Unwrap the engine's {'value': x, 'origin': ...} tag, tolerating None."""
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None      # drop NaN


def _row_for(run_id: str, record: dict) -> dict:
    plan = record.get("plan") or {}
    vcp = record.get("vcp") or {}
    return {
        "run_id": run_id,
        "symbol": record.get("symbol"),
        "name": record.get("name"),
        "exchange": record.get("exchange"),
        "country": record.get("country"),
        "asset_class": record.get("assetClass"),
        "currency": record.get("currency"),
        "verdict": record.get("verdict"),
        "status": record.get("status"),
        "as_of": record.get("as_of"),
        "close": _num(record.get("close")),
        "contractions": len(vcp.get("waves") or []) or None,
        "distance_to_pivot_pct": _num(plan.get("distance_to_pivot_pct")),
        "risk_pct": _num(plan.get("risk_pct")),
        "pivot": _num(plan.get("pivot")),
        "stop": _num(plan.get("stop")),
        "record": record,
    }


def save_results(run_id: str, records: list[dict]) -> int:
    """Write every scanned record. Returns how many rows were written."""
    written = 0
    for chunk in _chunks([_row_for(run_id, r) for r in records], _ROWS_PER_WRITE):
        _request("POST", "scan_results", payload=chunk,
                 prefer="resolution=merge-duplicates,return=minimal")
        written += len(chunk)
    return written


def finish_run(run_id: str, result: dict, source: str = "manual") -> None:
    """Mark the run complete and record its summary. Only after this does the
    dashboard consider the run readable — see latest_scan()."""
    _request(
        "PATCH", "scan_runs",
        params={"id": f"eq.{run_id}"},
        payload={
            "finished_at": datetime.now(tz=timezone.utc).isoformat(),
            "status": "complete",
            "source": source,
            "universe_size": result.get("universe_size"),
            "scanned": result.get("scanned"),
            "elapsed_seconds": result.get("elapsed_seconds"),
            "hidden_by_prescreen": result.get("hidden_by_prescreen", 0),
            "counts": result.get("counts") or {},
            "settings": result.get("settings") or {},
            "user_parameters": result.get("user_parameters") or [],
            "caveats": result.get("caveats") or [],
            "failures": result.get("failures") or [],
        },
        prefer="return=minimal",
    )


def fail_run(run_id: str, message: str) -> None:
    """Record that a run died. A failed run is never served to the dashboard,
    but it stays visible in the table so a silent cron failure is findable."""
    try:
        _request("PATCH", "scan_runs", params={"id": f"eq.{run_id}"},
                 payload={"status": "failed",
                          "finished_at": datetime.now(tz=timezone.utc).isoformat(),
                          "error": message[:2000]},
                 prefer="return=minimal")
    except StoreError:
        logger.exception("could not mark run %s as failed", run_id)


# ---------------------------------------------------------------------------
# Reading a scan
# ---------------------------------------------------------------------------

def latest_run() -> dict | None:
    rows = _request("GET", "scan_runs", params={
        "status": "eq.complete",
        "order": "started_at.desc",
        "limit": "1",
    })
    return rows[0] if rows else None


def latest_scan(country: str = "ALL", exchange: str = "ALL",
                asset_class: str = "ALL") -> dict | None:
    """Rebuild the exact payload scanner.scan() returns, from the newest
    completed run.

    The shape is reproduced deliberately: the dashboard should not be able to
    tell a stored scan from a live one, so no frontend change is needed and
    there is only ever one rendering path to keep correct. The only additions
    are the `stored` block and `is_stored`, which the UI may use to show how
    old the data is — never to change a verdict.
    """
    run = latest_run()
    if not run:
        return None

    params = {"run_id": f"eq.{run['id']}", "select": "record", "limit": "5000"}
    if country and country != "ALL":
        params["country"] = f"eq.{country}"
    if exchange and exchange != "ALL":
        params["exchange"] = f"eq.{exchange}"
    if asset_class and asset_class != "ALL":
        params["asset_class"] = f"eq.{asset_class}"

    rows = _request("GET", "scan_results", params=params) or []
    records = [row["record"] for row in rows if row.get("record")]

    # Re-sort here rather than trusting the stored order: a filtered read
    # returns a subset, and the ordering rule belongs to the scanner.
    import scanner
    records.sort(key=scanner._sort_key)

    by_country: dict[str, list] = {}
    by_exchange: dict[str, list] = {}
    by_verdict: dict[str, list] = {}
    for record in records:
        by_country.setdefault(record.get("country", "Global"), []).append(record)
        by_exchange.setdefault(record.get("exchange", "NSE"), []).append(record)
        by_verdict.setdefault(record.get("verdict", "no_setup"), []).append(record)

    filtered = (country, exchange, asset_class) != ("ALL", "ALL", "ALL")
    counts = (run.get("counts") or {}) if not filtered else {
        name: sum(1 for r in records if r.get("verdict") == name)
        for name in scanner.VERDICT_RANK if name != "error"
    }

    age_hours = _age_hours(run.get("started_at"))
    caveats = list(run.get("caveats") or [])
    caveats.insert(0, _freshness_caveat(run.get("started_at"), age_hours))

    return {
        "as_of": run.get("started_at"),
        "elapsed_seconds": run.get("elapsed_seconds"),
        "universe_size": run.get("universe_size") if not filtered else len(records),
        "scanned": run.get("scanned") if not filtered else len(records),
        "results": records,
        "categorized": {"by_country": by_country,
                        "by_exchange": by_exchange,
                        "by_verdict": by_verdict},
        "hidden_by_prescreen": run.get("hidden_by_prescreen", 0),
        "failures": run.get("failures") or [],
        "counts": counts,
        "settings": run.get("settings") or {},
        "user_parameters": run.get("user_parameters") or [],
        "caveats": caveats,
        "is_stored": True,
        "stored": {
            "run_id": run.get("id"),
            "started_at": run.get("started_at"),
            "finished_at": run.get("finished_at"),
            "source": run.get("source"),
            "age_hours": round(age_hours, 1) if age_hours is not None else None,
            "stale": bool(age_hours is not None
                          and age_hours > config.STORED_SCAN_STALE_HOURS),
        },
    }


def _age_hours(started_at: str | None) -> float | None:
    if not started_at:
        return None
    try:
        stamp = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return (datetime.now(tz=timezone.utc) - stamp).total_seconds() / 3600.0


def _freshness_caveat(started_at: str | None, age_hours: float | None) -> str:
    if age_hours is None:
        return ("These results were stored by a scheduled scan; the run time "
                "could not be read.")
    when = (started_at or "")[:16].replace("T", " ")
    if age_hours > config.STORED_SCAN_STALE_HOURS:
        return (f"STALE: this scan ran {age_hours:.0f}h ago ({when} UTC) and no "
                f"newer one has completed. Prices have moved since. Check that "
                f"the scheduled scanner is still running before acting on any "
                f"level below.")
    return (f"Stored scan from {when} UTC ({age_hours:.1f}h old). Levels are "
            f"as of that run's closing data, not live prices.")


def recent_runs(limit: int = 20) -> list[dict]:
    return _request("GET", "scan_runs", params={
        "select": "id,started_at,finished_at,status,source,scanned,"
                  "universe_size,elapsed_seconds,counts",
        "order": "started_at.desc",
        "limit": str(limit),
    }) or []


# ---------------------------------------------------------------------------
# Caches
# ---------------------------------------------------------------------------

def get_ohlcv(symbol: str, timeframe: str = "1D",
              max_age_hours: float = 12.0) -> dict | None:
    """Return the cached /api/market-data/ohlc payload, or None if absent or
    too old. The stored payload is that endpoint's own response, so the chart
    cannot tell a cache hit from a live fetch."""
    rows = _request("GET", "ohlcv_cache", params={
        "symbol": f"eq.{symbol.upper()}",
        "timeframe": f"eq.{timeframe}",
        "limit": "1",
    })
    if not rows:
        return None
    row = rows[0]
    age = _age_hours(row.get("updated_at"))
    if age is not None and age > max_age_hours:
        return None
    return row.get("payload")


def put_ohlcv(symbol: str, payload: dict, timeframe: str = "1D",
              exchange: str | None = None,
              provider_symbol: str | None = None) -> None:
    candles = (payload or {}).get("candles") or []
    _request("POST", "ohlcv_cache",
             payload=[{"symbol": symbol.upper(),
                       "timeframe": timeframe,
                       "provider_symbol": provider_symbol
                                          or (payload or {}).get("providerSymbol"),
                       "exchange": exchange or (payload or {}).get("exchange"),
                       "candles": len(candles),
                       "payload": payload,
                       "updated_at": datetime.now(tz=timezone.utc).isoformat()}],
             prefer="resolution=merge-duplicates,return=minimal")


def get_fundamentals(symbol: str, max_age_hours: float = 12.0) -> dict | None:
    rows = _request("GET", "fundamentals_cache", params={
        "symbol": f"eq.{symbol.upper()}", "limit": "1"})
    if not rows:
        return None
    row = rows[0]
    age = _age_hours(row.get("updated_at"))
    if age is not None and age > max_age_hours:
        return None
    return row.get("payload")


def put_fundamentals(symbol: str, payload: dict,
                     exchange: str | None = None) -> None:
    _request("POST", "fundamentals_cache",
             payload=[{"symbol": symbol.upper(),
                       "exchange": exchange,
                       "payload": payload,
                       "updated_at": datetime.now(tz=timezone.utc).isoformat()}],
             prefer="resolution=merge-duplicates,return=minimal")


def prune(keep: int = 60) -> int | None:
    """Delete all but the newest `keep` runs (calls the SQL helper)."""
    try:
        return _request("POST", "rpc/prune_scan_history", payload={"keep": keep})
    except StoreError:
        logger.exception("prune failed")
        return None


def health() -> dict:
    """Used by /api/health so a misconfigured deployment says so out loud."""
    if not enabled():
        return {"configured": False,
                "reason": "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are unset; "
                          "the app is running in live-scan-only mode."}
    try:
        run = latest_run()
    except StoreError as exc:
        return {"configured": True, "reachable": False, "error": str(exc)}
    if not run:
        return {"configured": True, "reachable": True, "latest_run": None,
                "note": "connected, but no completed scan has been stored yet."}
    age = _age_hours(run.get("started_at"))
    return {
        "configured": True,
        "reachable": True,
        "latest_run": {
            "id": run.get("id"),
            "started_at": run.get("started_at"),
            "source": run.get("source"),
            "scanned": run.get("scanned"),
            "age_hours": round(age, 1) if age is not None else None,
            "stale": bool(age is not None
                          and age > config.STORED_SCAN_STALE_HOURS),
        },
    }
