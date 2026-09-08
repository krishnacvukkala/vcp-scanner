"""Local Flask server for the Gateway Dashboard.

SECURITY, stated plainly: this app has no authentication, no authorisation and
no CSRF protection. It binds to 127.0.0.1 (config.HOST) so only your own
machine can reach it, and that loopback bind is the *only* thing protecting it.
Any process running as you can call these endpoints, including the POST ones.
Do not change HOST to 0.0.0.0, do not put it behind a tunnel, and do not run it
on a shared machine. It is a single-user desktop tool.

It also never places orders and holds no broker credentials — the worst a
request can do is spend Yahoo Finance bandwidth or clear the local price cache.

Endpoints
    GET  /                     the dashboard
    GET  /api/scan             scan the universe (params: force, fundamentals,
                               symbols)
    GET  /api/stock/<symbol>   one stock, in full, with chart series
    GET  /api/settings         config values with their SOURCE/USER provenance
    POST /api/size             position size from *your* risk budget (§17)
    POST /api/cache/clear      delete the on-disk price cache
"""

from __future__ import annotations

import math
import threading

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask.json.provider import DefaultJSONProvider

import config
import data
import market_data
import scanner
import store
import vcp_core


def _scrub(obj):
    """Recursively replace NaN/infinity with None and unbox numpy scalars.

    json.dumps would happily emit the literal `NaN`, which is not valid JSON and
    which JSON.parse rejects outright. Silently turning it into 0 would be worse
    — §25 forbids presenting a missing number as a real one — so it becomes null
    and the UI renders it as unavailable.
    """
    if isinstance(obj, dict):
        return {key: _scrub(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_scrub(value) for value in obj]
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        value = float(obj)
        return value if math.isfinite(value) else None
    if isinstance(obj, pd.Timestamp):
        return obj.strftime("%Y-%m-%d")
    return obj


class SafeJSONProvider(DefaultJSONProvider):
    """Serialises pandas/numpy values and keeps the output valid JSON."""

    sort_keys = False

    def dumps(self, obj, **kwargs):
        return super().dumps(_scrub(obj), **kwargs)

    @staticmethod
    def default(obj):
        if isinstance(obj, np.ndarray):
            return _scrub(obj.tolist())
        if isinstance(obj, pd.Series):
            return _scrub(obj.tolist())
        if isinstance(obj, pd.Timestamp):
            return obj.strftime("%Y-%m-%d")
        return DefaultJSONProvider.default(obj)


app = Flask(__name__, static_folder="static", static_url_path="/static")
app.json = SafeJSONProvider(app)

_scan_lock = threading.Lock()
_last_scan: dict | None = None


def _flag(name: str, default: bool = False) -> bool:
    raw = request.args.get(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/scan")
def api_scan():
    """Serve a scan.

    Where the answer comes from depends on what is actually possible:

    1. A short explicit symbol list is always scanned live — one or a few
       symbols finish well inside any request budget.
    2. Otherwise, if Supabase holds a completed scan, that is served. It is
       the same payload shape a live scan returns, plus a `stored` block
       saying how old it is, so the UI can be honest about freshness.
    3. Otherwise the universe is scanned live — correct on your own machine,
       and refused on a serverless host, where it would time out and return
       an error page that looks like a bug rather than a limit.
    """
    global _last_scan
    symbols = request.args.get("symbols")
    symbols = [s for s in symbols.split(",") if s.strip()] if symbols else None

    country = request.args.get("country", "ALL")
    exchange = request.args.get("exchange", "ALL")
    asset_class = request.args.get("assetClass", "ALL")
    unfiltered = not symbols and country == "ALL" and exchange == "ALL" and asset_class == "ALL"

    # 1. A handful of named symbols: scan them live, here and now.
    live_symbol_request = bool(symbols) and len(symbols) <= config.LIVE_SCAN_MAX_SYMBOLS

    # 2. Stored scan.
    if not live_symbol_request and store.enabled():
        # On serverless, a full live universe scan cannot finish inside the request budget,
        # so serving the latest complete stored scan is always the correct behavior.
        if not _flag("force") or config.ON_SERVERLESS:
            try:
                stored = store.latest_scan(country, exchange, asset_class)
            except store.StoreError as exc:
                app.logger.warning("Supabase read failed: %s", exc)
                stored = None
            if stored:
                if _flag("force"):
                    stored["refreshed_from_store"] = True
                return jsonify(stored)

    if _flag("cached") and _last_scan and unfiltered:
        return jsonify(_last_scan)

    # 3. Live scan of a universe — only where that can actually finish.
    if not live_symbol_request and config.ON_SERVERLESS:
        return jsonify({
            "error": "NO_STORED_SCAN",
            "message": "This hosted dashboard serves scans from the database; "
                       "it does not scan the universe inside a web request, "
                       "because that cannot finish inside the time limit. No "
                       "completed scan is stored yet.",
            "how_to_fix": "Run the 'Scheduled VCP scan' workflow in GitHub "
                          "Actions (Actions -> Scheduled VCP scan -> Run "
                          "workflow), or run "
                          "`python -m gatewaydashboard.jobs.run_scan` locally "
                          "with the Supabase environment variables set.",
            "supabase": store.health(),
            "results": [], "counts": {}, "failures": [],
        }), 503

    if not _scan_lock.acquire(blocking=False):
        if _last_scan:
            res = dict(_last_scan)
            res["is_scanning"] = True
            res["message"] = "A scan is currently running. Returning latest data."
            return jsonify(res)
        return jsonify({"error": "A scan is already running. Please wait a moment...", "is_scanning": True}), 409
    try:
        result = scanner.scan(
            symbols=symbols,
            country=country,
            exchange=exchange,
            asset_class=asset_class,
            force=_flag("force"),
            with_fundamentals=_flag("fundamentals", config.FUNDAMENTALS_ENABLED),
        )
        if unfiltered:
            _last_scan = result
        return jsonify(result)
    finally:
        _scan_lock.release()


@app.get("/api/health")
def api_health():
    """Says out loud whether storage is wired up. Worth checking first when
    the dashboard looks empty."""
    return jsonify({
        "ok": True,
        "serverless": config.ON_SERVERLESS,
        "cache_dir": str(data.CACHE_PATH),
        "supabase": store.health(),
    })


@app.get("/api/scan/history")
def api_scan_history():
    """Recent stored runs — how the UI shows that scans are still happening."""
    if not store.enabled():
        return jsonify({"available": False,
                        "reason": "Supabase is not configured."})
    try:
        return jsonify({"available": True, "runs": store.recent_runs(20)})
    except store.StoreError as exc:
        return jsonify({"available": False, "reason": str(exc)}), 502


import instruments


@app.get("/api/market-data/instruments")
def api_market_data_instruments():
    country = request.args.get("country", "ALL")
    return jsonify({
        "countries": instruments.get_all_countries(),
        "exchanges": instruments.get_exchanges_for_country(country),
        "assetClasses": instruments.get_asset_classes(),
        "instruments": instruments.search_instruments(country=country)
    })


@app.get("/api/market-data/search")
def api_market_data_search():
    q = request.args.get("q", "")
    country = request.args.get("country", "ALL")
    exchange = request.args.get("exchange", "ALL")
    asset_class = request.args.get("assetClass", "ALL")
    return jsonify({
        "query": q,
        "results": instruments.search_instruments(q, country, exchange, asset_class)
    })


@app.get("/api/market-data/ohlc")
def api_market_data_ohlc():
    """Chart series. Reads the Supabase cache first — the scheduled job stores
    this exact payload for every candidate, so opening a chart is a database
    read rather than a Yahoo round trip. Falls through to a live fetch for
    anything not cached, and writes what it fetched back."""
    symbol = request.args.get("symbol", "RELIANCE")
    exchange = request.args.get("exchange", "NSE")
    timeframe = request.args.get("timeframe", "1D")
    country = request.args.get("country", "")
    asset_class = request.args.get("assetClass", "EQUITY")
    force = _flag("force")

    if not force and store.enabled():
        try:
            cached = store.get_ohlcv(symbol, timeframe)
        except store.StoreError as exc:
            app.logger.warning("OHLC cache read failed: %s", exc)
            cached = None
        if cached:
            cached = dict(cached)
            cached["cached"] = True
            cached["cache_source"] = "supabase"
            return jsonify(cached)

    payload = market_data.MarketDataProvider.get_historical_ohlc(
        symbol=symbol,
        exchange=exchange,
        timeframe=timeframe,
        country=country,
        asset_class=asset_class,
        force=force,
    )

    if store.enabled() and payload.get("candles"):
        try:
            store.put_ohlcv(symbol, payload, timeframe=timeframe,
                            exchange=exchange)
        except store.StoreError as exc:
            app.logger.warning("OHLC cache write failed: %s", exc)

    return jsonify(payload)


@app.get("/api/stock/<symbol>")
def api_stock(symbol: str):
    return jsonify(scanner.scan_one(symbol, force=_flag("force")))


@app.get("/api/settings")
def api_settings():
    """Every tunable, with who owns it. The UI badges results from this."""
    return jsonify({
        "parameters": [
            {"name": name, "value": getattr(config, name, None), **meta}
            for name, meta in sorted(config.PARAM_PROVENANCE.items())
        ],
        "user_owned": sorted(config.user_set_params()),
        "verdict_parameters": vcp_core.verdict_parameters(),
        "undefined_in_source": {
            "PARTIAL_EXIT_R_MULTIPLE": config.PARTIAL_EXIT_R_MULTIPLE,
            "note": "§28 lists the parameters the workshop leaves undefined. "
                    "Where one is still None here, the rule that needs it is "
                    "switched off rather than guessed at.",
        },
        "not_implemented": {
            "short_setup": "§11 — the workshop covers no short setup",
            "scoring_model": "§23 — no weighted scoring formula exists in the "
                             "source; results are sorted, not scored",
            "sell_alerts_13": "§22 — the 13 sell alerts are qualitative in the "
                              "source and are shown as a checklist",
            "code_3_stocks": "§20 — referenced on p18 but never defined",
        },
    })


@app.post("/api/size")
def api_size():
    """§17 gives no sizing formula, so every input here has to come from you."""
    body = request.get_json(silent=True) or {}
    try:
        capital = float(body["capital"])
        risk_pct = float(body["risk_pct"]) / 100.0
        entry = float(body["entry"])
        stop = float(body["stop"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"available": False,
                        "reason": "capital, risk_pct, entry and stop are "
                                  "required and must be numbers"}), 400
    return jsonify(vcp_core.position_size(capital, risk_pct, entry, stop))


@app.post("/api/cache/clear")
def api_clear_cache():
    global _last_scan
    removed = data.clear_cache()
    _last_scan = None
    return jsonify({"removed": removed,
                    "note": "the next scan re-downloads everything from Yahoo"})


def main():
    print(f"Gateway Dashboard  http://{config.HOST}:{config.PORT}")
    print("No authentication — loopback only. Ctrl-C to stop.")
    app.run(host=config.HOST, port=config.PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
