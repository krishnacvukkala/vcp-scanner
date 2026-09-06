"""Scan orchestration — universe in, ranked records out.

The ordering here is p10's, not an optimisation: price action is settled first,
and fundamentals are only fetched for the stocks whose structure already
qualifies. That keeps the network cost down, but more importantly it means the
numbers can never talk the scanner into a setup the chart does not support.

Nothing in this module decides anything. Every verdict comes from vcp_core and
every flag from fundamentals; this file only walks the list, catches failures per
symbol so one bad ticker cannot end a scan, and sorts the output.
"""

from __future__ import annotations

import traceback
from datetime import datetime, timezone
from typing import Dict, List

import config
import data
import fundamentals
import instruments
import vcp_core

# Display order. "excluded" sits below "watch" deliberately: a §19 flag is a
# reason to look harder, not a reason to hide the chart.
VERDICT_RANK = {
    "valid_setup": 0,
    "watch": 1,
    "target_hit": 2,
    "excluded": 3,
    "structure_only": 4,
    "no_setup": 5,
    "error": 6,
}

STATUS_RANK = {
    "at_pivot": 0,
    "breakout": 1,
    "forming": 2,
    "target2_hit": 10,
    "target1_hit": 11,
    "extended": 12,
    "broken": 13,
    "no_vcp": 14
}


def _sort_key(record: dict):
    """Setups first, then the stocks closest to their pivot."""
    distance = ((record.get("plan") or {}).get("distance_to_pivot_pct")
                or {}).get("value")
    return (
        VERDICT_RANK.get(record.get("verdict"), 9),
        STATUS_RANK.get(record.get("status"), 9),
        abs(distance) if isinstance(distance, (int, float)) else 9999,
    )


def scan(
    symbols: list[str] | None = None,
    country: str = "ALL",
    exchange: str = "ALL",
    asset_class: str = "ALL",
    force: bool = False,
    with_fundamentals: bool | None = None,
    progress=None
) -> dict:
    """Run the full pipeline over a universe. Never raises."""
    started = datetime.now(tz=timezone.utc)

    if symbols is None:
        if country != "ALL" or exchange != "ALL" or asset_class != "ALL":
            universe = instruments.search_instruments("", country, exchange, asset_class)
        else:
            cat_inst = instruments.search_instruments("", "ALL", "ALL", "ALL")
            univ_csv = data.load_universe()
            seen = set()
            universe = []
            for u in univ_csv + cat_inst:
                sym = u["symbol"]
                if sym not in seen:
                    seen.add(sym)
                    universe.append(u)
    else:
        universe = [
            instruments.find_instrument(s) or {"symbol": s.strip().upper(), "exchange": "NSE", "name": s, "note": ""}
            for s in symbols if s and s.strip()
        ]

    if with_fundamentals is None:
        with_fundamentals = config.FUNDAMENTALS_ENABLED

    frames, notes = data.fetch_history(
        [row["symbol"] for row in universe], force=force, progress=progress)

    records, failures = [], []
    for row in universe:
        symbol = row["symbol"]
        exch = row.get("exchange", "NSE")
        frame = frames.get(symbol)
        if frame is None:
            failures.append({"symbol": symbol, "name": row.get("name", symbol),
                             "reason": notes.get(symbol, "DATA_UNAVAILABLE")})
            continue
        try:
            record = vcp_core.evaluate(frame, data.weekly_closes(frame))
        except Exception:
            failures.append({
                "symbol": symbol, "name": row.get("name", symbol),
                "reason": "CALCULATION_UNAVAILABLE: the detector raised on this "
                          "symbol. Traceback in the server log.",
            })
            traceback.print_exc()
            continue

        record.update({
            "symbol": symbol,
            "name": row.get("name", symbol),
            "exchange": exch,
            "country": row.get("country", "India" if exch in ("NSE", "BSE") else "Global"),
            "assetClass": row.get("assetClass", "EQUITY"),
            "note": row.get("note", ""),
            "data_note": notes.get(symbol)
        })
        _enrich_record(record)
        records.append(record)

    interesting = [r for r in records if r["verdict"] in ("valid_setup", "watch")]
    if with_fundamentals and interesting:
        import concurrent.futures

        def _eval_fund(r):
            try:
                ass = fundamentals.assess(
                    r["symbol"],
                    exchange=r.get("exchange"),
                    currency=r.get("currency"),
                    force=force
                )
                return r["symbol"], ass
            except Exception:
                return r["symbol"], {"enabled": True, "available": False, "reason": "ERROR"}

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            fund_map = dict(executor.map(_eval_fund, interesting))

        for record in interesting:
            assessment = fund_map.get(record["symbol"], {})
            record["fundamentals"] = assessment
            if assessment.get("available"):
                vcp_core.apply_exclusions(record, assessment.get("blocking"))

    if config.PRESCREEN_REQUIRED:
        shown = [r for r in records if r["prescreen"]["passed"]]
        hidden = len(records) - len(shown)
    else:
        shown, hidden = records, 0

    shown.sort(key=_sort_key)
    elapsed = (datetime.now(tz=timezone.utc) - started).total_seconds()

    # Build categorized breakdown by Country, Exchange, and Strategy Verdict
    by_country: Dict[str, List[dict]] = {}
    by_exchange: Dict[str, List[dict]] = {}
    by_verdict: Dict[str, List[dict]] = {}

    for r in shown:
        cntry = r.get("country", "Global")
        exch = r.get("exchange", "NSE")
        verd = r.get("verdict", "no_setup")

        by_country.setdefault(cntry, []).append(r)
        by_exchange.setdefault(exch, []).append(r)
        by_verdict.setdefault(verd, []).append(r)

    return {
        "as_of": started.isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed, 1),
        "universe_size": len(universe),
        "scanned": len(records),
        "results": shown,
        "categorized": {
            "by_country": by_country,
            "by_exchange": by_exchange,
            "by_verdict": by_verdict,
        },
        "hidden_by_prescreen": hidden,
        "failures": failures,
        "counts": {name: sum(1 for r in shown if r["verdict"] == name)
                   for name in VERDICT_RANK if name != "error"},
        "settings": {
            "prescreen_required": config.PRESCREEN_REQUIRED,
            "fundamentals": with_fundamentals,
            "breakout_on_close": config.BREAKOUT_ON_CLOSE,
            "difficult_market": config.DIFFICULT_MARKET,
            "history_period": config.HISTORY_PERIOD,
        },
        "user_parameters": config.user_set_params(),
        "caveats": [
            "The Chartink pre-screen narrows the universe; §22 is explicit that "
            "passing it is not a setup. It is not part of the verdict.",
            "Prices are split- and dividend-adjusted, so a pivot here can sit "
            "slightly below the level on an unadjusted chart. Re-read the exact "
            "price on your own chart before placing an order.",
            "§11: the workshop defines no short setup, and none is implemented.",
            "§23: the workshop defines no scoring formula. The ordering above is "
            "verdict then distance to pivot — a sort, not a ranking model.",
        ],
    }


def _enrich_record(record: dict) -> dict:
    import market_data
    sym = record.get("symbol", "")
    exch = record.get("exchange", "NSE")
    cntry = record.get("country", "")
    ac = record.get("assetClass", "EQUITY")
    res_info = market_data.resolve_symbol(sym, exch, ac, cntry)

    record["currency"] = res_info.get("currency", "USD" if exch != "NSE" else "INR")
    record["timezone"] = res_info.get("timezone", "UTC" if exch != "NSE" else "Asia/Kolkata")
    record["country"] = res_info.get("country", cntry or "Global")
    record["exchange"] = res_info.get("exchange", exch)
    record["providerSymbol"] = res_info.get("providerSymbol", sym)

    plan = record.get("plan") or {}
    pivot = (plan.get("pivot") or {}).get("value")
    stop = (plan.get("stop") or {}).get("value")
    close = (record.get("close") or {}).get("value")

    curr_sym = "₹" if record["currency"] == "INR" else ("$" if record["currency"] == "USD" else ("€" if record["currency"] == "EUR" else ("£" if record["currency"] == "GBP" else ("¥" if record["currency"] == "JPY" else "$"))))

    # A stock with no VCP structure must not get a trade plan.
    # Never invent fallback numbers (e.g. pivot = close, stop = close * 0.95).
    if pivot is not None and stop is not None and pivot > stop:
        risk_per_share = pivot - stop
        tp1 = round(pivot + (2.0 * risk_per_share), 2)
        tp2 = round(pivot + (3.0 * risk_per_share), 2)
        rr_ratio = round((tp1 - pivot) / risk_per_share, 2)
        rr_ratio_fmt = f"{rr_ratio:g} : 1"
        pot_risk = round(100 * risk_per_share, 2)
        pot_gain = round(100 * (tp2 - pivot), 2)
        trade_plan_available = True
        plan_reason = None
    else:
        tp1 = None
        tp2 = None
        rr_ratio = None
        rr_ratio_fmt = "N/A"
        pot_risk = None
        pot_gain = None
        trade_plan_available = False
        plan_reason = plan.get("reason") or "No valid VCP contraction structure to price"

    verdict = record.get("verdict", "no_setup")
    status = record.get("status", "no_vcp")

    if status == "target2_hit":
        signal = "TARGET 2 HIT"
    elif status == "target1_hit":
        signal = "TARGET 1 HIT"
    elif status == "broken" or verdict == "stop_loss_hit":
        signal = "STOP LOSS HIT"
    elif verdict == "valid_setup":
        signal = "Strong Buy"
    elif verdict == "watch":
        signal = "Watch (Near Pivot)"
    elif verdict == "structure_only":
        signal = "Structure Only"
    else:
        signal = "No Setup"

    record["tp1"] = tp1
    record["tp2"] = tp2
    record["ai_signal"] = signal
    # win_probability and confidence_score are not modeled by the VCP strategy engine (§25).
    # Never report invented constants.
    record["confidence_score"] = None
    record["win_probability"] = None
    record["rr_ratio"] = rr_ratio
    record["rr_ratio_fmt"] = rr_ratio_fmt
    record["potential_risk_val"] = pot_risk
    record["potential_gain_val"] = pot_gain
    record["trade_plan_available"] = trade_plan_available
    if plan_reason:
        record["trade_plan_unavailable_reason"] = plan_reason

    if trade_plan_available:
        record["ai_take"] = (
            f"{record.get('symbol', '')} ({record['exchange']}) trade offers a "
            f"{rr_ratio:g}:1 risk:reward ratio (TP1) with breakout pivot at {curr_sym}{pivot:.2f} "
            f"and stop loss at {curr_sym}{stop:.2f}."
        )
    else:
        record["ai_take"] = (
            f"No trade plan available for {record.get('symbol', '')} "
            f"({record.get('exchange', '')}): {plan_reason}."
        )
    return record


def scan_one(symbol: str, force: bool = False, exchange: str | None = None, country: str | None = None, asset_class: str | None = None) -> dict:
    """Full record for a single symbol, fundamentals included."""
    symbol = symbol.strip().upper()
    inst = instruments.find_instrument(symbol, exchange or "", country or "")
    target_ex = inst.get("exchange") if inst else (exchange or "NSE")
    target_country = inst.get("country") if inst else (country or "India")
    curr = inst.get("currency") if inst else ("INR" if target_ex in ("NSE", "BSE") else "USD")

    frames, notes = data.fetch_history([symbol], force=force)
    frame = frames.get(symbol)
    if frame is None:
        return {"symbol": symbol, "verdict": "error",
                "reason": notes.get(symbol, "DATA_UNAVAILABLE")}

    record = vcp_core.evaluate(frame, data.weekly_closes(frame))
    record["symbol"] = symbol
    record["exchange"] = target_ex
    record["country"] = target_country
    record["currency"] = curr
    record["data_note"] = notes.get(symbol)
    if config.FUNDAMENTALS_ENABLED:
        assessment = fundamentals.assess(symbol, exchange=target_ex, currency=curr)
        record["fundamentals"] = assessment
        if assessment.get("available"):
            vcp_core.apply_exclusions(record, assessment.get("blocking"))
    _enrich_record(record)
    record["history"] = ohlcv_payload(frame)
    return record


def ohlcv_payload(frame, sessions: int = 1000) -> dict:
    """Deep historical OHLCV plus moving averages, shaped for TradingView chart."""
    ind = vcp_core.indicator_frame(frame).tail(sessions)
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in ind.index],
        "open": [None if v != v else round(float(v), 2) for v in ind["Open"]],
        "high": [None if v != v else round(float(v), 2) for v in ind["High"]],
        "low": [None if v != v else round(float(v), 2) for v in ind["Low"]],
        "close": [None if v != v else round(float(v), 2) for v in ind["Close"]],
        "volume": [None if v != v else int(v) for v in ind["Volume"]],
        "sma20": [None if v != v else round(float(v), 2) for v in ind["SMA20"]],
        "sma50": [None if v != v else round(float(v), 2) for v in ind["SMA50"]],
        "sma200": [None if v != v else round(float(v), 2) for v in ind["SMA200"]],
    }
