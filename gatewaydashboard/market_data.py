"""Market Data Abstraction Layer & NSE Symbol Resolver.

Provides:
1. resolve_symbol(symbol, exchange): Symbol resolution layer for NSE and non-NSE tickers.
2. MarketDataProvider: Abstracted market data interface fetching normalized OHLC candles.
3. Validation, caching, and Asia/Kolkata timezone handling for NSE equities.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

# Configure logger
logger = logging.getLogger("market_data")
logging.basicConfig(level=logging.INFO)

import instruments

# In-memory cache for OHLC datasets: (provider_symbol, exchange, timeframe) -> (timestamp, candle_list)
_OHLC_CACHE: Dict[Tuple[str, str, str], Tuple[float, List[Dict[str, Any]]]] = {}
CACHE_TTL_DAILY = 3600 * 6  # 6 hours for daily/weekly/monthly
CACHE_TTL_INTRADAY = 300   # 5 minutes for intraday


def resolve_symbol(
    symbol: str,
    exchange: str = "NSE",
    asset_class: str = "EQUITY",
    country: str = ""
) -> Dict[str, str]:
    """Exchange-aware symbol-resolution layer for global markets.

    Examples:
    resolve_symbol("RELIANCE", "NSE") -> {"symbol": "RELIANCE", "exchange": "NSE", "providerSymbol": "RELIANCE.NS", "currency": "INR", "timezone": "Asia/Kolkata"}
    resolve_symbol("AAPL", "NASDAQ") -> {"symbol": "AAPL", "exchange": "NASDAQ", "providerSymbol": "AAPL", "currency": "USD", "timezone": "America/New_York"}
    resolve_symbol("ES=F", "CME") -> {"symbol": "ES=F", "exchange": "CME", "providerSymbol": "ES=F", "currency": "USD", "timezone": "America/Chicago"}
    """
    raw_symbol = (symbol or "").strip().upper()
    exch = (exchange or "NSE").strip().upper()
    ac = (asset_class or "EQUITY").strip().upper()

    if not raw_symbol:
        return {"symbol": "", "exchange": exch, "providerSymbol": "", "currency": "USD", "timezone": "UTC", "country": "Global", "assetClass": ac}

    # First check global instrument registry
    inst = instruments.find_instrument(raw_symbol, exch, country)
    if inst:
        return {
            "symbol": inst["symbol"],
            "exchange": inst["exchange"],
            "providerSymbol": inst["providerSymbol"],
            "currency": inst["currency"],
            "timezone": inst["timezone"],
            "country": inst["country"],
            "assetClass": inst["assetClass"],
            "name": inst["name"]
        }

    # Exchange-specific dynamic resolution rules
    if exch == "NSE" or raw_symbol.endswith(".NS"):
        disp = raw_symbol[:-3] if raw_symbol.endswith(".NS") else raw_symbol
        prov = raw_symbol if raw_symbol.endswith(".NS") else f"{raw_symbol}.NS"
        return {"symbol": disp, "exchange": "NSE", "providerSymbol": prov, "currency": "INR", "timezone": "Asia/Kolkata", "country": "India", "assetClass": ac, "name": disp}

    elif exch == "BSE" or raw_symbol.endswith(".BO"):
        disp = raw_symbol[:-3] if raw_symbol.endswith(".BO") else raw_symbol
        prov = raw_symbol if raw_symbol.endswith(".BO") else f"{raw_symbol}.BO"
        return {"symbol": disp, "exchange": "BSE", "providerSymbol": prov, "currency": "INR", "timezone": "Asia/Kolkata", "country": "India", "assetClass": ac, "name": disp}

    elif exch == "XETRA" or raw_symbol.endswith(".DE"):
        disp = raw_symbol[:-3] if raw_symbol.endswith(".DE") else raw_symbol
        prov = raw_symbol if raw_symbol.endswith(".DE") else f"{raw_symbol}.DE"
        return {"symbol": disp, "exchange": "XETRA", "providerSymbol": prov, "currency": "EUR", "timezone": "Europe/Berlin", "country": "Germany", "assetClass": ac, "name": disp}

    elif exch == "LSE" or raw_symbol.endswith(".L"):
        disp = raw_symbol[:-2] if raw_symbol.endswith(".L") else raw_symbol
        prov = raw_symbol if raw_symbol.endswith(".L") else f"{raw_symbol}.L"
        return {"symbol": disp, "exchange": "LSE", "providerSymbol": prov, "currency": "GBP", "timezone": "Europe/London", "country": "United Kingdom", "assetClass": ac, "name": disp}

    elif exch == "TSE" or raw_symbol.endswith(".T"):
        disp = raw_symbol[:-2] if raw_symbol.endswith(".T") else raw_symbol
        prov = raw_symbol if raw_symbol.endswith(".T") else f"{raw_symbol}.T"
        return {"symbol": disp, "exchange": "TSE", "providerSymbol": prov, "currency": "JPY", "timezone": "Asia/Tokyo", "country": "Japan", "assetClass": ac, "name": disp}

    elif exch == "HKEX" or raw_symbol.endswith(".HK"):
        disp = raw_symbol[:-3] if raw_symbol.endswith(".HK") else raw_symbol
        prov = raw_symbol if raw_symbol.endswith(".HK") else f"{raw_symbol}.HK"
        return {"symbol": disp, "exchange": "HKEX", "providerSymbol": prov, "currency": "HKD", "timezone": "Asia/Hong_Kong", "country": "Hong Kong", "assetClass": ac, "name": disp}

    elif exch == "ASX" or raw_symbol.endswith(".AX"):
        disp = raw_symbol[:-3] if raw_symbol.endswith(".AX") else raw_symbol
        prov = raw_symbol if raw_symbol.endswith(".AX") else f"{raw_symbol}.AX"
        return {"symbol": disp, "exchange": "ASX", "providerSymbol": prov, "currency": "AUD", "timezone": "Australia/Sydney", "country": "Australia", "assetClass": ac, "name": disp}

    tz = "America/Chicago" if exch in ("CME", "CBOT") else ("America/New_York" if exch in ("NASDAQ", "NYSE", "AMEX", "COMEX", "NYMEX") else "UTC")
    curr = "USD"
    cntry = "United States" if exch in ("NASDAQ", "NYSE", "AMEX", "CME", "CBOT", "COMEX", "NYMEX") else "Global"

    return {
        "symbol": raw_symbol,
        "exchange": exch,
        "providerSymbol": raw_symbol,
        "currency": curr,
        "timezone": tz,
        "country": cntry,
        "assetClass": ac,
        "name": raw_symbol
    }


TIMEFRAME_MAP = {
    "1m": ("7d", "1m"),
    "5m": ("7d", "5m"),
    "15m": ("60d", "15m"),
    "30m": ("60d", "30m"),
    "1h": ("730d", "1h"),
    "1D": ("3y", "1d"),
    "1W": ("5y", "1wk"),
    "1M": ("max", "1mo"),
}


class MarketDataProvider:
    """Abstracted Market Data Provider with candle validation & caching."""

    @staticmethod
    def validate_candles(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validates, cleans, and normalizes OHLC DataFrame into sorted JSON candles.

        Rules:
        - open, high, low, close, volume must exist and be numeric
        - high >= max(open, close, low)
        - low <= min(open, close, high)
        - Chronological order, no duplicates or NaNs
        """
        if df is None or df.empty:
            return []

        required_cols = {"Open", "High", "Low", "Close"}
        if not required_cols.issubset(set(df.columns)):
            return []

        clean_df = df.copy().dropna(subset=["Open", "High", "Low", "Close"])
        if clean_df.empty:
            return []

        # Remove duplicate index timestamps
        clean_df = clean_df[~clean_df.index.duplicated(keep="last")]
        clean_df = clean_df.sort_index()

        candles: List[Dict[str, Any]] = []
        seen_times = set()

        for idx, row in clean_df.iterrows():
            try:
                op = float(row["Open"])
                hi = float(row["High"])
                lo = float(row["Low"])
                cl = float(row["Close"])
                vol = int(row["Volume"]) if "Volume" in row and np.isfinite(row["Volume"]) else 0
            except (ValueError, TypeError):
                continue

            if not (np.isfinite(op) and np.isfinite(hi) and np.isfinite(lo) and np.isfinite(cl)):
                continue

            # Strict candle integrity checks
            if hi < max(op, cl, lo) or lo > min(op, cl, hi):
                continue

            # Timestamp normalization (seconds Unix timestamp)
            if isinstance(idx, pd.Timestamp):
                ts = int(idx.timestamp())
                time_str = idx.strftime("%Y-%m-%d")
            else:
                try:
                    p_ts = pd.to_datetime(idx)
                    ts = int(p_ts.timestamp())
                    time_str = p_ts.strftime("%Y-%m-%d")
                except Exception:
                    continue

            if ts in seen_times:
                continue
            seen_times.add(ts)

            candles.append({
                "time": ts,
                "time_str": time_str,
                "open": round(op, 2),
                "high": round(hi, 2),
                "low": round(lo, 2),
                "close": round(cl, 2),
                "volume": vol
            })

        return candles

    @classmethod
    def get_historical_ohlc(
        cls,
        symbol: str,
        exchange: str = "NSE",
        timeframe: str = "1D",
        country: str = "",
        asset_class: str = "EQUITY",
        force: bool = False
    ) -> Dict[str, Any]:
        """Fetch normalized OHLC dataset for global symbol, exchange and timeframe."""
        res_info = resolve_symbol(symbol, exchange, asset_class, country)
        prov_symbol = res_info["providerSymbol"]
        display_symbol = res_info["symbol"]
        tf = timeframe if timeframe in TIMEFRAME_MAP else "1D"

        cache_key = (prov_symbol, res_info["exchange"], tf)
        now = time.time()
        ttl = CACHE_TTL_INTRADAY if tf in ("1m", "5m", "15m", "30m", "1h") else CACHE_TTL_DAILY

        if not force and cache_key in _OHLC_CACHE:
            cached_time, cached_candles = _OHLC_CACHE[cache_key]
            if now - cached_time < ttl:
                return {
                    "symbol": display_symbol,
                    "exchange": res_info["exchange"],
                    "providerSymbol": prov_symbol,
                    "timeframe": tf,
                    "currency": res_info.get("currency", "USD"),
                    "timezone": res_info.get("timezone", "UTC"),
                    "country": res_info.get("country", "Global"),
                    "assetClass": res_info.get("assetClass", "EQUITY"),
                    "name": res_info.get("name", display_symbol),
                    "cached": True,
                    "candles": cached_candles
                }

        period, interval = TIMEFRAME_MAP[tf]
        req_start = datetime.now(tz=timezone.utc).isoformat()

        try:
            ticker = yf.Ticker(prov_symbol)
            df = ticker.history(period=period, interval=interval, auto_adjust=True)
            if df is None or df.empty:
                raise ValueError(f"No OHLC data returned for {prov_symbol}")
            
            candles = cls.validate_candles(df)
            if not candles:
                raise ValueError(f"No valid candles after validation for {prov_symbol}")

            _OHLC_CACHE[cache_key] = (now, candles)
            return {
                "symbol": display_symbol,
                "exchange": res_info["exchange"],
                "providerSymbol": prov_symbol,
                "timeframe": tf,
                "currency": res_info.get("currency", "USD"),
                "timezone": res_info.get("timezone", "UTC"),
                "country": res_info.get("country", "Global"),
                "assetClass": res_info.get("assetClass", "EQUITY"),
                "name": res_info.get("name", display_symbol),
                "cached": False,
                "candles": candles
            }

        except Exception as exc:
            err_msg = str(exc)
            logger.error(
                f"MarketDataError | symbol={display_symbol} resolvedSymbol={prov_symbol} "
                f"exchange={res_info['exchange']} timeframe={tf} provider=yfinance "
                f"time={req_start} error={err_msg}"
            )
            
            user_msg = "Historical chart data is temporarily unavailable."
            if "intraday" in err_msg.lower() or tf in ("1m", "5m", "15m", "30m", "1h"):
                user_msg = f"NSE intraday data for '{tf}' is unavailable. Daily data is loaded."

            return {
                "symbol": display_symbol,
                "exchange": res_info["exchange"],
                "providerSymbol": prov_symbol,
                "timeframe": tf,
                "error": True,
                "message": user_msg,
                "candles": []
            }
