"""VCP detection engine.

Section references in this file point at ../STRATEGY_MASTER.md, which is the
extracted specification this code implements. Where the specification says a
parameter is undefined, the code takes the value from config.py and the result
carries a note saying the answer depended on a choice you made — it does not
quietly present it as the workshop's rule.

Pipeline:

    stage 1   Chartink "ATR" pre-screen, seven quantified conditions  [§9]
    stage 2   Stage-2 trend check, then contraction-wave detection    [§10]
    stage 3   pivot, stop, target, reward:risk                        [§12,14,15]
    stage 4   violation and sell-alert checks on an open position      [§14,§17]
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config

# ---------------------------------------------------------------------------
# Provenance — §25 requires every displayed value to say which of these it is
# ---------------------------------------------------------------------------
CONFIRMED = "confirmed"      # straight from the data provider
CALCULATED = "calculated"     # derived from confirmed data by a stated formula
ESTIMATED = "estimated"      # a projection, e.g. an analyst estimate
UNAVAILABLE = "unavailable"  # not obtainable — never silently zero or blank


def tag(value, origin=CALCULATED, note=""):
    """Wrap a value with its provenance."""
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return {"value": None, "origin": UNAVAILABLE, "note": note or "no value"}
    if isinstance(value, (np.integer,)):
        value = int(value)
    elif isinstance(value, (np.floating,)):
        value = float(value)
    elif isinstance(value, (np.bool_,)):
        value = bool(value)
    return {"value": value, "origin": origin, "note": note}


def unavailable(reason):
    return {"value": None, "origin": UNAVAILABLE, "note": reason}


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["Close"].shift(1)
    return pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's ATR — the definition Chartink's atr(14) uses."""
    return true_range(df).ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()


def _last(series: pd.Series):
    """Last finite value of a series, or None."""
    if series is None or len(series) == 0:
        return None
    clean = series.dropna()
    return float(clean.iloc[-1]) if len(clean) else None


def indicator_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Attach every indicator the strategy needs to a copy of the OHLCV frame."""
    out = df.copy()
    close = out["Close"]
    out["ATR"] = atr(out, config.ATR_PERIOD)
    out["EMA_FAST"] = ema(close, config.EMA_FAST)
    out["EMA_MID"] = ema(close, config.EMA_MID)
    out["EMA_SLOW"] = ema(close, config.EMA_SLOW)
    out["SMA20"] = sma(close, config.SMA_SHORT)
    out["SMA50"] = sma(close, config.SMA_MID)
    out["SMA200"] = sma(close, config.SMA_LONG)
    out["VOL50"] = out["Volume"].rolling(50, min_periods=10).mean()
    out["TURNOVER"] = close * out["Volume"]
    return out


# ---------------------------------------------------------------------------
# Stage 1 — Chartink "ATR" pre-screen  [§9, §22]
# Seven conditions, all AND'ed, read verbatim off chartink.com/screener/atr-2089
# as displayed in `workshop day 2.mkv`. Passing this is not a setup: it only
# says the stock is worth checking for VCP structure.
# ---------------------------------------------------------------------------

def _cond(cid, label, passed, detail):
    return {"id": cid, "label": label, "passed": passed, "detail": detail}


def prescreen(ind: pd.DataFrame, weekly_close: pd.Series) -> dict:
    close = _last(ind["Close"])
    volume = _last(ind["Volume"])
    atr_now = _last(ind["ATR"])
    conditions = []

    atr_series = ind["ATR"].dropna()
    lookback = config.ATR_LOOKBACK_SESSIONS
    atr_then = (
        float(atr_series.iloc[-1 - lookback])
        if len(atr_series) > lookback else None
    )

    if atr_now is None or atr_then is None:
        conditions.append(_cond("atr_contracting", "ATR(14) below its level 10 sessions ago",
                                None, "not enough history to compare"))
    else:
        conditions.append(_cond(
            "atr_contracting", "ATR(14) below its level 10 sessions ago",
            atr_now < atr_then, f"{atr_now:.2f} vs {atr_then:.2f}"))

    if atr_now is None or not close:
        conditions.append(_cond("atr_ratio", "ATR(14) under 8% of price", None,
                                "ATR unavailable"))
    else:
        ratio = atr_now / close
        conditions.append(_cond(
            "atr_ratio", "ATR(14) under 8% of price",
            ratio < config.ATR_TO_CLOSE_MAX, f"{ratio * 100:.1f}%"))

    high_52w = float(weekly_close.tail(52).max()) if len(weekly_close) else None
    if high_52w is None or not close:
        conditions.append(_cond("near_high", "Within 25% of the 52-week high", None,
                                "weekly closes unavailable"))
    else:
        pct = close / high_52w
        conditions.append(_cond(
            "near_high", "Within 25% of the 52-week high",
            pct > config.PCT_OF_52W_HIGH_MIN,
            f"{pct * 100:.0f}% of {high_52w:.2f} (52w weekly-close high)"))

    e_fast, e_mid, e_slow = (_last(ind["EMA_FAST"]), _last(ind["EMA_MID"]),
                             _last(ind["EMA_SLOW"]))
    if None in (e_fast, e_mid, e_slow):
        conditions.append(_cond("ema_stack", "EMA 50 > 150 > 200", None,
                                "needs 200 sessions of history"))
    else:
        conditions.append(_cond(
            "ema_stack", "EMA 50 > 150 > 200",
            e_fast > e_mid > e_slow,
            f"{e_fast:.1f} / {e_mid:.1f} / {e_slow:.1f}"))

    if e_fast is None or not close:
        conditions.append(_cond("above_ema50", "Price above its 50-EMA", None,
                                "EMA 50 unavailable"))
    else:
        conditions.append(_cond(
            "above_ema50", "Price above its 50-EMA",
            close > e_fast, f"{close:.2f} vs {e_fast:.2f}"))

    conditions.append(_cond(
        "min_price", f"Price above Rs {config.MIN_CLOSE_INR:.0f}",
        None if close is None else close > config.MIN_CLOSE_INR,
        "close unavailable" if close is None else f"{close:.2f}"))

    turnover = None if (close is None or volume is None) else close * volume
    conditions.append(_cond(
        "min_turnover", "Daily turnover above Rs 10,00,000",
        None if turnover is None else turnover > config.MIN_TURNOVER_INR,
        "volume unavailable" if turnover is None
        else f"Rs {turnover / 100000:.1f} lakh"))

    failed = [c["id"] for c in conditions if c["passed"] is False]
    unknown = [c["id"] for c in conditions if c["passed"] is None]
    return {
        "passed": not failed and not unknown,
        "conditions": conditions,
        "failed": failed,
        "indeterminate": unknown,
        "source": "chartink.com/screener/atr-2089 (STRATEGY_MASTER.md §9)",
    }


# ---------------------------------------------------------------------------
# Stage 2a — Stage-2 trend  [§22 STAGE_2_TREND]
# ---------------------------------------------------------------------------

def stage_2_trend(ind: pd.DataFrame) -> dict:
    close, ma200 = _last(ind["Close"]), _last(ind["SMA200"])
    ma_series = ind["SMA200"].dropna()
    rising = None
    if len(ma_series) > config.TREND_SLOPE_SESSIONS:
        rising = bool(
            ma_series.iloc[-1] > ma_series.iloc[-1 - config.TREND_SLOPE_SESSIONS]
        )

    checks = [
        _cond("above_ma200", "Price above the 200-day average",
              None if (close is None or ma200 is None) else close > ma200,
              "needs 200 sessions" if ma200 is None
              else f"{close:.2f} vs {ma200:.2f}"),
        _cond("ma200_rising",
              f"200-day average higher than {config.TREND_SLOPE_SESSIONS} sessions ago",
              rising,
              "needs more history" if rising is None else
              ("rising" if rising else "flat or falling")),
    ]
    return {
        "passed": all(c["passed"] is True for c in checks),
        "checks": checks,
        "indeterminate": [c["id"] for c in checks if c["passed"] is None],
        "note": "the second check reads §22's qualitative "
                "long_term_trend == 'up' as a rising 200-day average, which is "
                "a choice made here, not a formula from the workshop",
    }


# ---------------------------------------------------------------------------
# Stage 2b — swing points and contraction waves  [§10]
# The workshop never defines how to identify a swing, so the fractal window
# (config.SWING_WINDOW) is a USER parameter. Widening it finds fewer, larger
# waves; narrowing it finds more, noisier ones.
# ---------------------------------------------------------------------------

def swing_points(df: pd.DataFrame, window: int | None = None):
    """[(positional_index, 'H'|'L', price)] for confirmed fractal swings."""
    window = window or config.SWING_WINDOW
    highs = df["High"].to_numpy(dtype=float)
    lows = df["Low"].to_numpy(dtype=float)
    points = []
    for i in range(window, len(df) - window):
        lo, hi = i - window, i + window + 1
        if highs[i] >= np.nanmax(highs[lo:hi]):
            points.append((i, "H", float(highs[i])))
        if lows[i] <= np.nanmin(lows[lo:hi]):
            points.append((i, "L", float(lows[i])))
    return points


def _alternate(points):
    """Collapse the raw fractal points into a strict H,L,H,L,... zigzag.

    A run of same-type points keeps only the most extreme one. This is a
    heuristic, not a rule from the workshop — see the note above swing_points.
    """
    seq = []
    for idx, kind, price in sorted(points, key=lambda p: p[0]):
        if seq and seq[-1][1] == kind:
            more_extreme = price >= seq[-1][2] if kind == "H" else price <= seq[-1][2]
            if more_extreme:
                seq[-1] = (idx, kind, price)
            continue
        seq.append((idx, kind, price))
    return seq


def _wave(df, i_high, high_price, i_low, low_price, provisional):
    """One high -> low contraction leg, with its own volume statistics."""
    vol = df["Volume"].iloc[i_high:i_low + 1].mean()
    return {
        "i_high": int(i_high),
        "i_low": int(i_low),
        "date_high": df.index[i_high].strftime("%Y-%m-%d"),
        "date_low": df.index[i_low].strftime("%Y-%m-%d"),
        "high": float(high_price),
        "low": float(low_price),
        "depth": float((high_price - low_price) / high_price),
        "sessions": int(i_low - i_high),
        "avg_volume": float(vol) if np.isfinite(vol) else None,
        "provisional": bool(provisional),
    }


def contraction_waves(df: pd.DataFrame, window: int | None = None) -> list[dict]:
    """Alternating high->low legs. The final leg may be unconfirmed.

    The last `window` bars cannot host a confirmed fractal low, so when the
    zigzag ends on a high the still-forming pullback is measured to the lowest
    low since that high and marked provisional. Without this the newest — and
    most interesting — contraction would be invisible until it is already over.
    """
    seq = _alternate(swing_points(df, window))
    waves = []
    for (i_a, k_a, p_a), (i_b, k_b, p_b) in zip(seq, seq[1:]):
        if k_a == "H" and k_b == "L" and p_b < p_a:
            waves.append(_wave(df, i_a, p_a, i_b, p_b, False))

    if seq and seq[-1][1] == "H":
        i_high, _, high_price = seq[-1]
        tail = df["Low"].iloc[i_high + 1:]
        if len(tail.dropna()):
            i_low = i_high + 1 + int(np.nanargmin(tail.to_numpy(dtype=float)))
            low_price = float(df["Low"].iloc[i_low])
            if low_price < high_price:
                waves.append(_wave(df, i_high, high_price, i_low, low_price, True))
    return waves


def _shrinking_run(waves: list[dict]) -> list[dict]:
    """Longest run ending at the newest wave whose depths shrink throughout.

    Walks backwards from the last leg while each earlier leg is deeper, which
    is §10 rule 3 read literally. A deep leg further back that breaks the
    sequence ends the base rather than being folded into it.
    """
    run = [waves[-1]]
    for wave in reversed(waves[:-1]):
        if wave["depth"] > run[0]["depth"]:
            run.insert(0, wave)
        else:
            break
    return run


# ---------------------------------------------------------------------------
# Stage 2c — the five §10 rules applied to the wave sequence
# ---------------------------------------------------------------------------

def detect_vcp(df: pd.DataFrame, window: int | None = None) -> dict:
    base = df.tail(config.BASE_MAX_SESSIONS)
    all_waves = contraction_waves(base, window)
    waves = [w for w in all_waves if w["depth"] >= config.MIN_DEPTH_PCT]
    dropped = len(all_waves) - len(waves)

    if not waves:
        return {
            "present": False,
            "waves": [],
            "checks": [],
            "reason": f"no pullback of at least {config.MIN_DEPTH_PCT * 100:.0f}% "
                      f"in the last {len(base)} sessions",
            "shallow_waves_ignored": dropped,
        }

    run = _shrinking_run(waves) if config.DEPTH_MUST_SHRINK else list(waves)
    run = run[-config.MAX_CONTRACTIONS:]
    depths = [w["depth"] for w in run]
    lows = [w["low"] for w in run]

    checks = [
        _cond("contraction_count",
              f"At least {config.MIN_CONTRACTIONS} contractions",
              len(run) >= config.MIN_CONTRACTIONS,
              f"{len(run)}: " + " -> ".join(f"{d * 100:.1f}%" for d in depths)),
        _cond("depth_shrinks", "Each contraction shallower than the one before",
              all(b < a for a, b in zip(depths, depths[1:])),
              " -> ".join(f"{d * 100:.1f}%" for d in depths)),
        _cond("higher_lows",
              "Each pullback low at or above the previous one "
              f"(within {config.HIGHER_LOW_TOLERANCE * 100:.0f}%)",
              all(b >= a * (1 - config.HIGHER_LOW_TOLERANCE)
                  for a, b in zip(lows, lows[1:])),
              " -> ".join(f"{v:.2f}" for v in lows)),
    ]

    v_first, v_last = run[0]["avg_volume"], run[-1]["avg_volume"]
    ratio = (v_last / v_first) if (v_first and v_last) else None
    if config.VOLUME_DRYUP_REQUIRED:
        checks.append(_cond(
            "volume_dryup", "Volume drier in the last contraction than the first",
            None if ratio is None else ratio <= config.VOLUME_DRYUP_RATIO_MAX,
            "volume unavailable" if ratio is None
            else f"{ratio:.2f}x the first wave's average"))

    span = run[-1]["i_low"] - run[0]["i_high"]
    checks.append(_cond(
        "base_duration",
        f"Base lasts {config.BASE_MIN_SESSIONS}-{config.BASE_MAX_SESSIONS} sessions",
        config.BASE_MIN_SESSIONS <= span <= config.BASE_MAX_SESSIONS,
        f"{span} sessions (~{span / 5:.0f} weeks) from {run[0]['date_high']}"))

    failed = [c["id"] for c in checks if c["passed"] is False]
    unknown = [c["id"] for c in checks if c["passed"] is None]
    final = run[-1]
    return {
        "present": not failed and not unknown,
        "waves": run,
        "checks": checks,
        "failed": failed,
        "indeterminate": unknown,
        "shallow_waves_ignored": dropped,
        "final_wave": final,
        "base_high": float(max(w["high"] for w in run)),
        "base_low": float(min(w["low"] for w in run)),
        "base_sessions": int(span),
        "tightness_pct": float(final["depth"] * 100),
        "volume_ratio": ratio,
        "provisional_final_wave": final["provisional"],
        "source": "STRATEGY_MASTER.md §10 rules 1-5",
    }


# ---------------------------------------------------------------------------
# Stage 3 — pivot, stop, target, reward:risk  [§12, §14, §15, §27]
# The pivot is the final contraction's high (§12). The buffer above it and the
# buffer below the stop are both USER values because §27 records that neither
# "just above" nor "just below" is quantified in the workshop.
# ---------------------------------------------------------------------------

def _bands():
    if config.DIFFICULT_MARKET:
        return config.TIGHT_RISK_BAND, config.TIGHT_TARGET_BAND, "difficult"
    return config.NORMAL_RISK_BAND, config.NORMAL_TARGET_BAND, "normal"


def trade_plan(df: pd.DataFrame, ind: pd.DataFrame, vcp: dict) -> dict:
    if not vcp.get("waves"):
        return {"available": False,
                "reason": "CALCULATION_UNAVAILABLE: no contraction wave to price"}

    final = vcp["final_wave"]
    risk_band, target_band, regime = _bands()

    pivot = final["high"] * (1 + config.PIVOT_BUFFER_PCT)
    stop = final["low"] * (1 - config.STOP_BUFFER_PCT)
    close = _last(ind["Close"])
    risk = pivot - stop
    if risk <= 0:
        return {"available": False,
                "reason": "CALCULATION_UNAVAILABLE: stop is not below the pivot"}

    risk_pct = risk / pivot
    target = pivot + config.MIN_REWARD_RISK * risk
    band_target_lo = pivot * (1 + target_band[0])
    band_target_hi = pivot * (1 + target_band[1])

    plan = {
        "available": True,
        "regime": regime,
        "pivot": tag(pivot, CALCULATED,
                     "final contraction high"
                     + (f" + {config.PIVOT_BUFFER_PCT * 100:.2f}% buffer"
                        if config.PIVOT_BUFFER_PCT else " (no buffer added)")),
        "stop": tag(stop, CALCULATED,
                    "final contraction low"
                    + (f" - {config.STOP_BUFFER_PCT * 100:.2f}% buffer"
                       if config.STOP_BUFFER_PCT else " (no buffer subtracted)")),
        "risk_per_share": tag(risk, CALCULATED, "pivot - stop"),
        "risk_pct": tag(risk_pct * 100, CALCULATED, "as % of the pivot"),
    }

    plan["target"] = tag(
        target, CALCULATED,
        f"pivot + {config.MIN_REWARD_RISK:g}x risk — §15 requires at least "
        f"{config.MIN_REWARD_RISK:g}:1")
    plan["target_band"] = tag(
        [band_target_lo, band_target_hi], CALCULATED,
        f"p39's {regime} target range of "
        f"{target_band[0] * 100:.0f}-{target_band[1] * 100:.0f}% above the pivot")
    plan["reward_risk"] = tag(config.MIN_REWARD_RISK, CALCULATED,
                              "by construction — the target is defined from the risk")

    notes = []
    if risk_pct < risk_band[0]:
        notes.append(
            f"risk is {risk_pct * 100:.1f}%, tighter than p39's {regime} "
            f"{risk_band[0] * 100:.0f}-{risk_band[1] * 100:.0f}% guidance — a "
            "tight base, but check the stop is not inside the day's noise")
    elif risk_pct > risk_band[1]:
        notes.append(
            f"risk is {risk_pct * 100:.1f}%, wider than p39's {regime} "
            f"{risk_band[0] * 100:.0f}-{risk_band[1] * 100:.0f}% guidance. §28 "
            "records that the workshop sets no hard maximum (its own OLECTRA "
            "example ran 9.1%), so this is a judgement call, not a rejection")
    if config.MAX_RISK_PCT_HARD and risk_pct > config.MAX_RISK_PCT_HARD:
        notes.append(
            f"exceeds MAX_RISK_PCT_HARD ({config.MAX_RISK_PCT_HARD * 100:.1f}%), "
            "a ceiling you set — not a workshop rule")
    if target > band_target_hi:
        notes.append(
            f"a {config.MIN_REWARD_RISK:g}:1 payoff needs "
            f"{(target / pivot - 1) * 100:.1f}% of upside, more than p39's "
            f"{regime} {target_band[1] * 100:.0f}% ceiling. §26 notes this "
            "tension between the 2:1 rule and the stated target range; the "
            "dashboard shows both rather than choosing for you")
    plan["notes"] = notes

    if config.PARTIAL_EXIT_R_MULTIPLE is None:
        plan["partial_exit"] = unavailable(
            "§16's sell-half-and-move-to-breakeven rule needs a risk multiple "
            "that the workshop never states (§28). Set "
            "PARTIAL_EXIT_R_MULTIPLE in config.py to switch it on as your rule")
    else:
        r = config.PARTIAL_EXIT_R_MULTIPLE
        plan["partial_exit"] = tag(
            pivot + r * risk, CALCULATED,
            f"sell half at {r:g}x risk and move the stop to breakeven — "
            f"{r:g} is a number you chose, not one from the workshop")

    # Where is price now, relative to the pivot? Only sessions after the final
    # contraction low can count as a breakout from that contraction.
    after = ind.loc[final["date_low"]:].iloc[1:]
    ref = after["Close"] if config.BREAKOUT_ON_CLOSE else after["High"]
    crossed = ref[ref > pivot]
    breakout_date = crossed.index[0] if len(crossed) else None

    plan["last_close"] = tag(close, CONFIRMED,
                             f"session of {ind.index[-1].strftime('%Y-%m-%d')}")
    plan["distance_to_pivot_pct"] = tag(
        None if close is None else (pivot / close - 1) * 100, CALCULATED,
        "positive means price is still below the pivot")

    if breakout_date is not None:
        age = len(ind.loc[breakout_date:]) - 1
        vol = float(ind.loc[breakout_date, "Volume"])
        vol50 = ind.loc[breakout_date, "VOL50"]
        vol_ratio = (vol / float(vol50)) if pd.notna(vol50) and vol50 else None
        plan["breakout"] = {
            "date": breakout_date.strftime("%Y-%m-%d"),
            "age_sessions": int(age),
            "basis": "daily close above the pivot" if config.BREAKOUT_ON_CLOSE
                     else "intraday high above the pivot",
            "volume_ratio": tag(
                vol_ratio, CALCULATED,
                "breakout volume / 50-session average. §10 and §13 require "
                "expanding volume but never quantify it, so the "
                f"{config.BREAKOUT_VOLUME_RATIO_MIN:g}x threshold this is "
                "compared against is yours"),
            "volume_expanding": None if vol_ratio is None
                                else vol_ratio >= config.BREAKOUT_VOLUME_RATIO_MIN,
        }
        if close is not None and close >= pivot * 1.15:
            status = "target2_hit"
        elif close is not None and close >= pivot * 1.08:
            status = "target1_hit"
        elif age <= config.BREAKOUT_WATCH_SESSIONS:
            status = "breakout"
        else:
            status = "extended"
    else:
        plan["breakout"] = None
        if close is not None and close >= pivot * 1.15:
            status = "target2_hit"
        elif close is not None and close >= pivot * 1.08:
            status = "target1_hit"
        elif close is not None and close < stop:
            status = "broken"
        elif close is not None and close >= pivot * (1 - config.NEAR_PIVOT_PCT):
            status = "at_pivot"
        else:
            status = "forming"

    plan["status"] = status
    if vcp["base_high"] > pivot * (1 + 1e-9):
        plan["overhead_supply"] = tag(
            vcp["base_high"], CALCULATED,
            f"an earlier high inside the base sits at {vcp['base_high']:.2f}, "
            f"above the {pivot:.2f} pivot. §12 defines the pivot as the final "
            "contraction's high, so it is left there — but sellers may wait at "
            "the older level")
    return plan


# ---------------------------------------------------------------------------
# Stage 4 — exit / invalidation triggers  [§14 p30-31, §22]
# §22 lists five computable triggers plus `any(SELL_ALERT_CONDITIONS)` — a set
# of 13 conditions the source itself describes as qualitative and comparative to
# the stock's own move. Those 13 are deliberately NOT implemented; they come
# back as a checklist to read off the chart. Quantifying them here would be
# inventing rules and passing them off as the workshop's.
# ---------------------------------------------------------------------------

def _trailing_lower_low_run(df: pd.DataFrame) -> int:
    """How many consecutive lower lows the series ends on."""
    lows = df["Low"].to_numpy(dtype=float)
    run = 0
    for i in range(len(lows) - 1, 0, -1):
        if lows[i] < lows[i - 1]:
            run += 1
        else:
            break
    return run


def exit_signals(ind: pd.DataFrame, plan: dict | None = None) -> dict:
    close = _last(ind["Close"])
    ma20, ma50 = _last(ind["SMA20"]), _last(ind["SMA50"])
    triggers = []

    age = (plan or {}).get("breakout", {}) or {}
    age = age.get("age_sessions")
    fresh = age is not None and age <= config.BREAKOUT_WATCH_SESSIONS

    triggers.append(_cond(
        "close_below_ma20",
        "Close below the 20-day average soon after breakout",
        None if (close is None or ma20 is None) else close < ma20,
        ("needs 20 sessions" if ma20 is None else f"{close:.2f} vs {ma20:.2f}")
        + (f"; {age} sessions since breakout, inside the "
           f"{config.BREAKOUT_WATCH_SESSIONS}-session window you set" if fresh
           else f"; {age} sessions since breakout, past that window"
           if age is not None else "; no breakout yet, so §14 reads this as "
           "context rather than a trigger")))

    triggers.append(_cond(
        "close_below_ma50",
        "Close below the 50-day average (the more serious violation)",
        None if (close is None or ma50 is None) else close < ma50,
        "needs 50 sessions" if ma50 is None else f"{close:.2f} vs {ma50:.2f}"))

    run = _trailing_lower_low_run(ind)
    run_vol = None
    if run:
        vol = ind["Volume"].iloc[-run:].mean()
        vol50 = _last(ind["VOL50"])
        run_vol = (float(vol) / vol50) if vol50 else None
    on_volume = (run_vol is not None
                 and run_vol >= config.LOWER_LOW_VOLUME_RATIO)
    triggers.append(_cond(
        "lower_lows_on_volume",
        f"{config.CONSEC_LOWER_LOWS}+ consecutive lower lows on volume, "
        f"no bounce by day {config.NO_SUPPORT_BY_DAY}",
        run >= config.CONSEC_LOWER_LOWS and on_volume,
        f"{run} consecutive lower lows"
        + (f" averaging {run_vol:.2f}x the 50-session volume" if run_vol
           else "; volume average unavailable")
        + (f". A run this long is itself the absence of a bounce by day "
           f"{config.NO_SUPPORT_BY_DAY}"
           if run >= config.NO_SUPPORT_BY_DAY else "")))

    window = ind.tail(config.UPDOWN_WINDOW_SESSIONS + 1)
    change = window["Close"].diff().dropna()
    up, down = int((change > 0).sum()), int((change < 0).sum())
    triggers.append(_cond(
        "more_down_than_up_days",
        f"More down days than up days in the last "
        f"{config.UPDOWN_WINDOW_SESSIONS} sessions",
        None if not len(change) else down > up,
        "no history" if not len(change) else f"{down} down vs {up} up"))

    span = (window["High"] - window["Low"]).replace(0, np.nan)
    position = (window["Close"] - window["Low"]) / span
    good = int((position >= config.GOOD_CLOSE_RANGE_POS).sum())
    bad = int((position < config.GOOD_CLOSE_RANGE_POS).sum())
    triggers.append(_cond(
        "more_bad_than_good_closes",
        f"More closes in the bottom {config.GOOD_CLOSE_RANGE_POS * 100:.0f}% of "
        "the daily range than the top",
        None if not (good + bad) else bad > good,
        "no history" if not (good + bad) else
        f"{bad} weak vs {good} strong closes (a weak close finishes below "
        f"{config.GOOD_CLOSE_RANGE_POS * 100:.0f}% of the day's range — that "
        "definition is yours, §14 does not give one)"))

    stop = ((plan or {}).get("stop") or {}).get("value")
    if stop is not None:
        triggers.insert(0, _cond(
            "below_stop", "Close below the stop under the final contraction low",
            None if close is None else close < stop,
            "close unavailable" if close is None else
            f"{close:.2f} vs {stop:.2f} — §14 calls this the one HARD rule and "
            "p43 ranks cutting the loss above every other priority"))

    atr_now = _last(ind["ATR"])
    atr_ref = None
    atr_series = ind["ATR"].dropna()
    if len(atr_series) > config.UPDOWN_WINDOW_SESSIONS:
        atr_ref = float(atr_series.iloc[-1 - config.UPDOWN_WINDOW_SESSIONS])

    fired = [t["id"] for t in triggers if t["passed"] is True]
    return {
        "any_fired": bool(fired),
        "fired": fired,
        "triggers": triggers,
        "volatility": tag(
            None if not (atr_now and atr_ref) else atr_now / atr_ref, CALCULATED,
            f"ATR now vs {config.UPDOWN_WINDOW_SESSIONS} sessions ago. §14 lists "
            "\"wide and volatile price action\" as bearish but sets no "
            "threshold, so this is reported without a verdict"),
        "qualitative": [
            {"label": "The 13 sell-alert conditions",
             "why_not_computed": "§22 records that the source's 13 sell alerts "
                                 "are qualitative and measured against the "
                                 "stock's own move, with no independent "
                                 "quantification. Read them off your chart"},
            {"label": "Low volume on the way out, high volume on the way in",
             "why_not_computed": "p30-31 states the pairing but defines neither "
                                 "leg, so any formula here would be invented"},
        ],
        "source": "STRATEGY_MASTER.md §14 (p30-31), §22 exit triggers",
    }


# ---------------------------------------------------------------------------
# Position sizing  [§17]
# §17 is explicit: "no formula tying position size to account equity,
# volatility, or stop distance is given anywhere in the source." So this
# function refuses to default the risk budget — the caller must pass one, and
# the result says out loud that the number came from you.
# ---------------------------------------------------------------------------

def position_size(capital, risk_budget_pct, entry, stop) -> dict:
    if not all(isinstance(x, (int, float)) for x in
               (capital, risk_budget_pct, entry, stop)):
        return {"available": False,
                "reason": "capital, risk budget, entry and stop are all required"}
    risk_per_share = entry - stop
    if risk_per_share <= 0 or capital <= 0 or risk_budget_pct <= 0:
        return {"available": False,
                "reason": "entry must be above the stop and both inputs positive"}
    budget = capital * risk_budget_pct
    shares = int(budget // risk_per_share)
    return {
        "available": True,
        "shares": tag(shares, CALCULATED,
                      f"(capital x {risk_budget_pct * 100:.2f}%) / "
                      f"Rs {risk_per_share:.2f} risk per share"),
        "capital_at_risk": tag(shares * risk_per_share, CALCULATED, "if stopped out"),
        "position_value": tag(shares * entry, CALCULATED, "at the entry price"),
        "exposure_pct": tag(shares * entry / capital * 100, CALCULATED,
                            "share of capital committed"),
        "note": "§17 gives no sizing formula — the risk budget above is yours, "
                "not the workshop's. What §17 does say: start with small pilot "
                "buys, scale up only after the trade proves itself, and cut "
                "exposure further rather than adding when results are poor.",
    }


# ---------------------------------------------------------------------------
# One stock, all four stages  [§22 VALID_LONG_SETUP]
# Note what is NOT in the gate: the Chartink pre-screen. §22 is explicit that it
# narrows the universe and is "not a substitute for VALID_LONG_SETUP". Whether a
# failing pre-screen hides a stock from the dashboard is config.PRESCREEN_REQUIRED,
# a USER switch — it never changes the verdict below.
# ---------------------------------------------------------------------------

# The USER-owned parameters that can move the verdict. Surfaced with every
# result so a "no setup" answer can be told apart from "no setup at these
# settings".
VERDICT_PARAMS = (
    "SWING_WINDOW", "MIN_DEPTH_PCT", "MIN_CONTRACTIONS", "MAX_CONTRACTIONS",
    "BASE_MIN_SESSIONS", "BASE_MAX_SESSIONS", "HIGHER_LOW_TOLERANCE",
    "VOLUME_DRYUP_RATIO_MAX", "TREND_SLOPE_SESSIONS", "PIVOT_BUFFER_PCT",
    "STOP_BUFFER_PCT", "BREAKOUT_ON_CLOSE", "NEAR_PIVOT_PCT",
)


def verdict_parameters() -> list[dict]:
    out = []
    for name in VERDICT_PARAMS:
        origin, note = config.provenance_of(name)
        out.append({"name": name, "value": getattr(config, name, None),
                    "origin": origin, "note": note})
    return out


def _verdict(gates: list[dict], trend_ok, vcp_ok, excluded: list, status: str = None):
    """(valid, verdict) from the four §22 gates."""
    if status in ("target1_hit", "target2_hit"):
        return False, "target_hit"
    if all(g["passed"] is True for g in gates):
        return True, "valid_setup"
    if excluded and vcp_ok:
        return False, "excluded"        # structure is there, §19 says no
    if trend_ok and vcp_ok:
        return False, "watch"           # structure is there, pivot not cleared
    if vcp_ok:
        return False, "structure_only"  # base, but not a Stage-2 uptrend
    return False, "no_setup"


def evaluate(df: pd.DataFrame, weekly: pd.Series | None = None,
             exclusions: list | None = None) -> dict:
    """Four-stage assessment of one stock. Returns one JSON-able record."""
    ind = indicator_frame(df)
    if weekly is None:
        weekly = df["Close"].resample("W-FRI").last().dropna()

    pre = prescreen(ind, weekly)
    trend = stage_2_trend(ind)
    vcp = detect_vcp(df)
    plan = trade_plan(df, ind, vcp)
    exits = exit_signals(ind, plan if plan.get("available") else None)

    breakout = bool(plan.get("available") and plan.get("breakout"))
    excluded = list(exclusions or [])
    breakout_detail = "not yet" if not breakout else (
        f"{plan['breakout']['basis']}, "
        f"{plan['breakout']['age_sessions']} sessions ago")

    gates = [
        _cond("stage_2_trend", "Stage-2 uptrend (§22)", trend["passed"],
              "; ".join(c["detail"] for c in trend["checks"])),
        _cond("vcp_present", "VCP structure present (§10)", vcp["present"],
              vcp.get("reason") or
              f"{len(vcp.get('waves', []))} contractions, "
              f"tightest {vcp.get('tightness_pct', 0):.1f}%"),
        _cond("breakout_confirmed", "Breakout above the pivot (§12)", breakout,
              breakout_detail),
        _cond("no_exclusions", "No §19 exclusion condition", not excluded,
              "none found" if not excluded else "; ".join(map(str, excluded))),
    ]
    valid, verdict = _verdict(gates, trend["passed"], vcp["present"], excluded, plan.get("status"))

    last = ind.index[-1]
    atr_now, close = _last(ind["ATR"]), _last(ind["Close"])
    return {
        "as_of": last.strftime("%Y-%m-%d"),
        "sessions": int(len(ind)),
        "close": tag(close, CONFIRMED, f"adjusted close, {last:%Y-%m-%d}"),
        "atr_pct": tag(None if not (atr_now and close) else atr_now / close * 100,
                       CALCULATED, "ATR(14) as a % of price"),
        "verdict": verdict,
        "valid_long_setup": valid,
        "gates": gates,
        "prescreen": pre,
        "trend": trend,
        "vcp": vcp,
        "plan": plan,
        "exits": exits,
        "status": plan.get("status", "no_vcp"),
        "verdict_parameters": verdict_parameters(),
        "no_short_setup": "§11: the workshop covers no short setup. Nothing "
                          "here should be read as a short signal.",
    }


def apply_exclusions(record: dict, exclusions: list | None) -> dict:
    """Fold §19 exclusions into a record that was already priced.

    Fundamentals cost a network call each, so the scanner only looks them up
    for stocks whose price action already qualifies (p10's ordering: price
    first, numbers second). This re-closes the §22 gate afterwards instead of
    recomputing the whole record.
    """
    excluded = list(exclusions or [])
    for gate in record.get("gates", []):
        if gate["id"] == "no_exclusions":
            gate["passed"] = not excluded
            gate["detail"] = ("none found" if not excluded
                              else "; ".join(map(str, excluded)))
    record["valid_long_setup"], record["verdict"] = _verdict(
        record.get("gates", []),
        record.get("trend", {}).get("passed"),
        record.get("vcp", {}).get("present"),
        excluded,
        record.get("plan", {}).get("status"),
    )
    return record
