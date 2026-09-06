"""Market data layer — yfinance downloads with an on-disk cache.

Nothing in this module interprets prices. It hands back OHLCV frames and an
explicit record of which symbols could not be fetched and why, because
STRATEGY_MASTER.md §25 requires missing data to be labelled DATA_UNAVAILABLE
rather than silently dropped or filled in.

A note on adjustment: history is pulled with auto_adjust=True, so closes are
adjusted for splits and dividends. Split adjustment is not optional here — an
unadjusted 1:10 split looks exactly like a 90% contraction to a pattern
detector. The side effect is that pivot and stop levels can sit a little below
the raw prices you would read off an unadjusted TradingView chart on a stock
that has paid dividends. Treat the levels as structural, and re-read the exact
price off your own chart before placing an order.
"""

from __future__ import annotations

import csv
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

import config

PROJECT_DIR = Path(__file__).resolve().parent
CACHE_PATH = PROJECT_DIR / config.CACHE_DIR
OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def to_yahoo(symbol: str, exchange: str | None = None) -> str:
    """Symbol -> Yahoo provider ticker. Uses exchange-aware resolution."""
    symbol = (symbol or "").strip().upper()
    try:
        import instruments
        inst = instruments.find_instrument(symbol, exchange or "")
        if inst and inst.get("providerSymbol"):
            return inst["providerSymbol"]
    except Exception:
        pass
    # Not in catalog: apply exchange-aware suffix logic
    # Symbols that already have a suffix or are futures/crypto are used as-is
    if "." in symbol or "=" in symbol or "^" in symbol or "-" in symbol:
        return symbol
    # Default: NSE suffix (universe.csv is NSE-only)
    return symbol + config.YF_SUFFIX


def from_yahoo(ticker: str) -> str:
    """Yahoo ticker -> Display symbol."""
    t = ticker.upper()
    try:
        import instruments
        for item in instruments.INSTRUMENT_CATALOG:
            if item["providerSymbol"].upper() == t:
                return item["symbol"]
    except Exception:
        pass
    s = config.YF_SUFFIX.upper()
    return t[:-len(s)] if t.endswith(s) else t


def load_universe(path: str | Path | None = None) -> list[dict]:
    """Read universe.csv. Blank lines and lines starting with # are skipped."""
    path = Path(path) if path else PROJECT_DIR / "universe.csv"
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for raw in csv.reader(fh):
            if not raw or not raw[0].strip() or raw[0].lstrip().startswith("#"):
                continue
            if raw[0].strip().lower() == "symbol":       # header
                continue
            rows.append({
                "symbol": raw[0].strip().upper(),
                "name": raw[1].strip() if len(raw) > 1 else "",
                "note": raw[2].strip() if len(raw) > 2 else "",
            })
    if config.MAX_TICKERS:
        rows = rows[: config.MAX_TICKERS]
    return rows


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _cache_file(symbol: str) -> Path:
    return CACHE_PATH / f"{symbol}.csv"


def _cache_age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(tz=timezone.utc) - mtime).total_seconds() / 3600.0


def _read_cache(symbol: str, ignore_ttl: bool = False) -> pd.DataFrame | None:
    path = _cache_file(symbol)
    age = _cache_age_hours(path)
    if age is None:
        return None
    if not ignore_ttl and age > config.CACHE_TTL_HOURS:
        return None
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
    except Exception:
        return None
    return _tidy(df) if _looks_usable(df) else None


def _write_cache(symbol: str, df: pd.DataFrame) -> None:
    # Both the mkdir and the write have to be inside the guard. On a
    # read-only filesystem (Vercel serves the deployment read-only; only
    # /tmp is writable) mkdir raises OSError, and an unguarded one here used
    # to turn every successful download into a 500 on the deployed app.
    try:
        CACHE_PATH.mkdir(parents=True, exist_ok=True)
        df.to_csv(_cache_file(symbol))
    except OSError:
        pass        # a cache write failure must never fail a scan


def _looks_usable(df: pd.DataFrame | None) -> bool:
    if df is None or df.empty:
        return False
    if not set(OHLCV_COLUMNS).issubset(df.columns):
        return False
    return df["Close"].notna().sum() >= 30


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Single-ticker frame -> OHLCV only, sorted, tz-naive, NaN closes dropped."""
    if isinstance(df.columns, pd.MultiIndex):
        # Whichever level holds Open/High/Low/Close/Volume is the one we want.
        for level in range(df.columns.nlevels):
            names = set(df.columns.get_level_values(level))
            if {"Close", "Volume"}.issubset(names):
                df = df.copy()
                df.columns = df.columns.get_level_values(level)
                break
        else:
            df = df.copy()
            df.columns = ["|".join(map(str, c)) for c in df.columns]

    keep = [c for c in OHLCV_COLUMNS if c in df.columns]
    df = df.loc[:, keep].copy()

    idx = pd.to_datetime(df.index, errors="coerce")
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert(None)
    df.index = idx
    df = df[df.index.notna()]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df.dropna(subset=["Close"]) if "Close" in df.columns else df


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def _download_batch(symbols: list[str]) -> dict[str, pd.DataFrame]:
    """Fetch a batch of symbols. Never raises — failures come back as gaps."""
    import yfinance as yf

    tickers = [to_yahoo(s) for s in symbols]
    out: dict[str, pd.DataFrame] = {}
    try:
        raw = yf.download(
            tickers=" ".join(tickers),
            period=config.HISTORY_PERIOD,
            interval="1d",
            auto_adjust=True,       # see the module docstring
            actions=False,
            progress=False,
            group_by="ticker",
            threads=True,
            timeout=12,
        )
    except Exception:
        return out
    if raw is None or getattr(raw, "empty", True):
        return out

    if len(tickers) == 1:
        out[from_yahoo(tickers[0])] = _tidy(raw)
        return out

    for ticker in tickers:
        try:
            sub = raw[ticker]
        except (KeyError, IndexError, TypeError):
            continue
        out[from_yahoo(ticker)] = _tidy(sub)
    return out


def fetch_history(symbols, force: bool = False, progress=None):
    """Fetch daily OHLCV for many symbols.

    Returns (frames, notes) where notes[symbol] explains, in the vocabulary of
    STRATEGY_MASTER.md §25, why a symbol is absent or degraded:
    DATA_UNAVAILABLE or STALE_DATA. A symbol never appears in both.
    """
    frames: dict[str, pd.DataFrame] = {}
    notes: dict[str, str] = {}
    todo: list[str] = []

    for symbol in symbols:
        symbol = symbol.strip().upper()
        if not symbol:
            continue
        if not force:
            cached = _read_cache(symbol)
            if cached is not None:
                frames[symbol] = cached
                continue
        todo.append(symbol)

    for start in range(0, len(todo), config.BATCH_SIZE):
        batch = todo[start:start + config.BATCH_SIZE]
        if progress:
            progress(min(start + len(batch), len(todo)), len(todo))
        got = _download_batch(batch)
        for symbol in batch:
            df = got.get(symbol)
            if _looks_usable(df):
                frames[symbol] = df
                _write_cache(symbol, df)
                continue
            stale = _read_cache(symbol, ignore_ttl=True)
            if stale is not None:
                age = _cache_age_hours(_cache_file(symbol)) or 0
                frames[symbol] = stale
                notes[symbol] = (
                    f"STALE_DATA: Yahoo returned nothing for {to_yahoo(symbol)}; "
                    f"scanned against a cached copy {age:.0f}h old."
                )
            else:
                notes[symbol] = (
                    f"DATA_UNAVAILABLE: no usable daily history for "
                    f"{to_yahoo(symbol)}. Check the symbol exists on Yahoo "
                    f"Finance, or remove it from universe.csv."
                )
        if start + config.BATCH_SIZE < len(todo):
            time.sleep(config.REQUEST_PAUSE_SEC)

    return frames, notes


# ---------------------------------------------------------------------------
# Derived series
# ---------------------------------------------------------------------------

def weekly_closes(df: pd.DataFrame) -> pd.Series:
    """Friday-anchored weekly closes.

    The Chartink pre-screen's 52-week-high condition is defined on *weekly*
    closes, not daily highs (STRATEGY_MASTER.md §9 condition 3), so this is the
    series that condition must be evaluated against.
    """
    return df["Close"].resample("W-FRI").last().dropna()


def clear_cache() -> int:
    """Delete every cached price file. Returns how many were removed."""
    if not CACHE_PATH.exists():
        return 0
    removed = 0
    for path in CACHE_PATH.glob("*.csv"):
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return removed
