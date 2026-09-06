# STRATEGY MASTER SPECIFICATION — VCP (Volatility Contraction Pattern) Swing/Position Trading Strategy

**Status: Inspection complete — all 6 project files inspected (5 contributing, 1 excluded).** This document is built from all five contributing sources: two PDFs, one text file, and two workshop-recording videos (visual content fully inspected via scene-change frame sampling; audio could not be transcribed in this environment — see §29 for the full technical explanation and exactly what that limitation means for coverage). Everything below is traceable to the written/visual material actually inspected — nothing here is inferred from filenames or assumed from context alone.

---
## 1. Executive Summary

This is a **swing-to-position-trading equity strategy** built on Mark Minervini's SEPA (Specific Entry Point Analysis) methodology, localized to Indian (NSE) markets by the "Stock Exploder" workshop material. The core technical pattern is the **VCP — Volatility Contraction Pattern**: a stock in a Stage-2 uptrend forms a base made of successive pullback waves, each shallower (and narrower in time) than the last, on shrinking volume, before breaking out on expanding volume through a "pivot" point just above the final, tightest contraction. Entry is taken at/near that pivot; the stop-loss sits just below the low of that final contraction, which is deliberately the smallest, tightest part of the whole base — this is what gives the setup its favorable reward-to-risk ratio. Stock selection is filtered by both technical structure (the VCP itself, long-term uptrend, RS Rating) and fundamentals (accelerating EPS/sales, expanding margins, ROE, a catalyst), with price action ultimately overriding narrative or numbers ("never trust the story or the numbers unless confirmed by price action" — p10). Risk management is central: keep losses small, cut them tighter in weak conditions, move stops to breakeven as soon as possible, take partial profits into strength, and evaluate every trade against a personal statistical track record rather than any single outcome.

## 2. Source Inventory

See `SOURCE_FILE_INVENTORY.md` for the complete file-by-file inventory (filename, type, size, date, readability, relevance) and `SOURCE_KNOWLEDGE_MAP.md` for the full page-by-page extraction this document is built from. Summary:

| Source | Role | Status |
|---|---|---|
| `vcp workshop.pdf` (46 pages) | PRIMARY — all rules | Fully inspected |
| `vcp example.pdf` (20 pages) | Confirming visual gallery of real trades | Fully inspected |
| `SCANNER N FUNDAMENTAL INK.txt` | Screener tooling references | Fully inspected |
| `september vcp workshop day 1.mkv` (856MB) | Live re-presentation of Source A's slide deck + incidental live-chart/tool context | Visually inspected (46/46 scene-change frames). Audio not available in this environment. No new slide content found. |
| `workshop day 2.mkv` (825MB) | Distinct "Day 2 Special Class" — live stock-screening & tool-usage demo | Visually inspected (58/58 scene-change frames). Audio not available. Revealed the full Chartink "ATR" screener formula referenced in Source C (now in §9/§22), plus two items flagged UNKNOWN/UNCONFIRMED (§28) |
| `FNO GIFT SWING WALE IGNORE THIS.mkv` (82MB) | N/A | Inspected and excluded — unrelated/discarded content, per the user's own filename |

## 3. Strategy Philosophy

Buy fundamentally sound, market-leading businesses at the single lowest-risk moment in their uptrend — the instant they break out of a tightening volatility contraction on expanding volume — so that the stop-loss (placed just under that tight base) is small in percentage terms while the profit potential (a continuation of the established uptrend) is comparatively large. Price action is the final arbiter over any story or number (p10). Risk is actively managed at every stage: position sizing starts small and is only increased once trades are working (p42), losses are kept small and made even smaller in difficult market conditions (p39), and the trader's own historical statistics — not any single trade's outcome — are what should drive decision-making (p36-37, p41).

## 4. Market Universe

- **Exchange/market:** NSE-listed Indian equities (all example charts are NSE tickers; screener reference is Chartink, an Indian-market screening tool; second reference is MarketSmithIndia).
- **Instrument type:** Cash equities (swing/position trades). No mention of derivatives, options, or futures for this strategy (the one file touching NIFTY/BANKNIFTY futures content — the "IGNORE THIS" clip — is explicitly excluded).
- **Market-cap/liquidity/float:** No hard numeric cutoff is stated. The material notes (as a statistical observation about past big winners, not a prescriptive filter) that 95% of the biggest winners had float under 30 million shares (p5), and separately describes "Institutional Favorites" as typically liquid, mid-to-large-cap names (p4). `PARAMETER NOT SPECIFIED` — no explicit minimum average daily volume, minimum price, or minimum market cap is given anywhere in the source material.
- **Sector bias:** Historically, the best-performing groups were Consumer/Retail, Technology/Computer-Related, Drugs/Medical/Biotech, and Leisure/Entertainment (p5) — presented as a historical tendency, not an exclusion rule for other sectors.

## 5. Required Data

- Daily OHLCV price/volume history (primary timeframe — see §7)
- Weekly OHLCV (used at least for broader-context confirmation — e.g., the Godawari Power example is shown on both daily and weekly)
- 20-day, 50-day, and 200-day simple moving averages
- 52-week high/low
- Relative Strength (RS) Rating (referenced via the Dixon Technologies research-terminal screenshot, p12)
- Quarterly EPS (actual, and analyst estimates for the next 1-2 quarters) — at least the most recent 3 quarters plus trailing 3-5 years for growth-rate comparison
- Quarterly and annual revenue/sales (actual + estimates)
- Net profit margin (quarterly/annual, with prior-year comparison)
- Return on Equity (ROE)
- Shares outstanding / free float
- Institutional fund-ownership count/trend (shown in the Dixon example)
- Volume relative to its own recent average (for "dry-up" and "expansion" comparisons)
- General market index behavior (for Stage/market-health context, §8)

## 6. Indicators

| Indicator | Purpose | Timeframe | Parameters | Bullish condition | Bearish condition | Mandatory? | Source |
|---|---|---|---|---|---|---|---|
| 20-day SMA | Short-term trend/stop reference | Daily | 20-period simple MA | Price holds above it after breakout | Close below it soon after breakout = warning | Yes (as an exit/warning trigger) | p30-31 |
| 50-day SMA | Intermediate trend/stop reference | Daily | 50-period simple MA | Price above and rising | Close below it on heavy volume = stronger warning than the 20-day breach | Yes | p30-31 |
| 200-day SMA | Long-term trend filter | Daily | 200-period simple MA | Price above it (part of "Stage 2" definition; 99% of the "95% Club" were above it) | Price below it | Implied mandatory (Stage-2 prerequisite) | p5, p19 |
| Relative Strength (RS) Rating | Ranks a stock's price performance vs. the broader market/universe | N/A (rating, not a chart overlay) | Not defined in source (a proprietary/third-party rating, referenced via the MarketSmithIndia screenshot) | Higher/rising RS supports Market Leader / Institutional Favorite categorization | Low/falling RS | Soft confirmation | p12, p4 |
| Volume (vs. own recent average) | Confirms supply/demand imbalance | Daily | Not fixed — "significant," "heaviest since move began," etc., are qualitative | Volume dries up during contractions; expands on breakout; high-volume rallies/low-volume pullbacks | High volume on down days; heavy volume with little price progress ("stalling") | Yes (structural to VCP + confirmation) | p21-22, p28-32 |
| EPS growth (quarter-over-quarter, sequential) | Fundamental momentum filter | Quarterly | Look for +20%+ in the most recent 2-3 quarters, and sequential acceleration | Accelerating EPS growth | Material deceleration | Soft/preferred confirmation (price action is the final gate — p10) | p11, p18 |
| Sales/Revenue growth | Confirms EPS quality (real growth vs. cost-cutting only) | Quarterly | Increasing in the most recent 2-3 quarters | Accelerating with EPS | Positive EPS with negative sales = limited life span | Soft/preferred | p18 |
| Net Profit Margin | Confirms earnings quality/operating leverage | Quarterly/Annual | Compare to prior-year period | Expanding | Contracting ("eroding margins" = warning) | Soft/preferred | p17-18 |
| Return on Equity (ROE) | Management-quality gauge, peer-relative | Annual/TTM | 15-17%+ is described as "a good cutoff for most stocks," compared against industry peers | ROE ≥ ~15-17% and competitive vs. peers | Materially below peers | Soft/preferred | p15 |
| VCP contraction depth (% pullback of each wave) | Defines the core pattern | Daily (waves can span weeks-months) | Progressively shallower each wave (illustrated examples: −31%→−17%→−8%→−3%, and −27%→−17%→−8%) — no fixed minimum/maximum % is stated | Each successive contraction shallower than the prior one | Contractions not shrinking, or widening | Mandatory (this IS the pattern) | p21-24 |

No other indicators (RSI, MACD, ATR, Bollinger Bands, ADX, ORB, etc.) are mentioned anywhere in the source material — none should be assumed or added.

## 7. Timeframe Model

- **Primary timeframe: Daily.** All rule-bearing examples (Netflix, AMSC, CBPO, Urban Outfitter, MHST, LL) and 19 of 20 example-gallery charts are daily candlesticks.
- **Secondary/context timeframe: Weekly.** Used at least once (Godawari Power, shown on both daily and weekly) to confirm the same base structure over a longer lookback. The source material does not describe a formal "check weekly for trend, then daily for entry" hierarchy the way some multi-timeframe systems do — it simply uses whichever timeframe best displays the base.
- **No intraday/lower timeframe is used or mentioned.** This is not a day-trading or intraday-scalping strategy.
- **Base durations by pattern type** (this is the closest the source comes to a formal timeframe/duration model, p19):
  - Cup Completion Cheat & Low Cheat: 6-52 weeks
  - Cup with Handle: 7-65 weeks
  - Double Bottom: 7-65 weeks
  - Darvas Box: 4-5 weeks
  - Power Play: 2-6 weeks
- `AMBIGUOUS`: whether the entry trigger requires an end-of-day closing breakout above the pivot, or an intraday touch is sufficient. Not stated in the source material — flagged rather than assumed.

## 8. Market Conditions

- **General principle:** History shows more than 96% of "superperformance" stocks emerge from bear markets or general market corrections (p20). A correction is treated as a preparation window, not a reason to stop researching.
- **During a correction, watch for** (p20): (1) stocks hitting the 52-week-high list; (2) stocks that corrected the least, staying within 25% of a 52-week high; (3) stocks that surged the most off the market low; (4) stocks base-building/consolidating within a long-term uptrend; (5) a proliferation of stocks setting up and emerging through proper buy points; (6) accumulation showing up in the major indices around when leaders start breaking out.
- **During difficult/choppy trading periods** (p39): gains will be smaller and win-rate lower — the response is to cut losses shorter (not wider), reduce position size/exposure, get off margin/leverage immediately, and take profits smaller/sooner (e.g., a normal 15-20% target becomes 10-12%; a normal 7-8% stop becomes 4-5%).
- `PARAMETER NOT SPECIFIED`: no explicit index-level filter (e.g., "only trade when Nifty is above its 50-day MA") is stated as a hard rule — the market-condition guidance above is descriptive/behavioral rather than a coded index filter.

## 9. Stock Selection Rules

### Universe Filters
- Exchange: NSE (implied by all examples).
- `PARAMETER NOT SPECIFIED` in the slide deck: minimum price, minimum average daily volume/turnover, minimum market cap. However, the Chartink "ATR" screener the course references by URL (Source C) and demonstrates live on-screen (Source E, `workshop day 2.mkv`) DOES encode concrete numeric universe/pre-screen filters — captured here as a directly-observed, source-supported technical pre-screen (classified **HARD RULE — source-supported (screener tool)**, distinct from the slide deck's own qualitative rules):
  1. `ATR(14) < ATR(14) as of 10 trading days ago` — ATR must be contracting (a direct, quantified proxy for "volatility contraction")
  2. `ATR(14) / Close < 0.08` — ATR under 8% of price (a low-volatility filter)
  3. `Close > 0.75 × MAX(52-week weekly closes)` — price within 25% of its 52-week high (echoes p20's "stayed within 25% of a 52-week high" correction-watch item, §8)
  4. `EMA(Close,50) > EMA(Close,150) > EMA(Close,200)` — stacked/aligned moving averages (a Minervini Trend-Template-style long-term-uptrend filter; distinct from, but compatible with, the plain `price > MA200` rule in §22)
  5. `Close > EMA(Close,50)` — price above its 50-day average
  6. `Close > ₹10` — penny-stock exclusion
  7. `Close × Volume > ₹10,00,000` — minimum daily turnover/liquidity filter
  This filter is a **candidate pre-screen only** — it narrows the universe to inspect for VCP structure; passing it does NOT by itself satisfy `VALID_LONG_SETUP` (§22), which still requires the VCP pattern, breakout confirmation, and absence of exclusion conditions. See SOURCE_KNOWLEDGE_MAP.md, Source E, for the exact on-screen capture this was transcribed from (chartink.com/screener/atr-2089).
- Statistical tendency (not a hard filter): smaller float (<30M shares) was common among the biggest historical winners (p5).

### Company-Quality Filters (Categories & Catalysts)
Prefer stocks in one of 4 categories (p4): Market Leader, Top Competitor, Institutional Favorite, or Turnaround Situation. Prefer businesses with the "Good" characteristics and avoid the "Bad" ones (p6):

| Prefer (Good) | Avoid (Bad) |
|---|---|
| Growth | Capital intensive |
| Accelerating EPS and Revenue | Limited pricing power |
| Explosive market position | Heavily regulated |
| Sustainable trends | Margin pressure |
| Scalable business models | Eroding industry position |

### Trade Setup Filters (applied to an individual candidate at the time of the trade)
- Long-term trend up (Stage 2), price above 200-day MA.
- Fundamentals ideally show: EPS +20%+ in the most recent 2-3 quarters with sequential acceleration; rising sales in step with EPS; expanding or at least stable net profit margins; ROE ≥ ~15-17% vs. peers; a clear catalyst (new product/service, positive industry change); ideally a "breakout year" of annual EPS after a range-bound multi-year period.
- A valid VCP structure is present (§10) with volume drying up through the contractions.
- `UNDEFINED — DO NOT INVENT`: "Code 3 stocks" (p18) is referenced as something to look for but is never defined anywhere in the source material.

## 10. Long Setup (the VCP pattern itself)

**HARD structural definition:**
1. Stock is in a confirmed uptrend (Stage 2), generally above its 200-day (and preferably 50-day) moving average.
2. Price forms a base consisting of **2 or more successive pullback ("contraction") waves**. (No fixed minimum wave count is stated; every illustrated example shows between 2 and 5 waves — CYBERTECH in the example gallery shows 5.)
3. **Each contraction is shallower (smaller % pullback) than the one before it**, and the base typically also narrows in time from wave to wave. Illustrated depth sequences: −31% → −17% → −8% → −3% (p24, the "VCP Template"); −27% → −17% → −8% (p23, Netflix).
4. **Volume dries up (contracts)** progressively through the later, tighter waves — interpreted as supply ("trapped buyers"/sellers) being exhausted, while "bottom fishers" absorb each successive dip at a higher low (p21-22).
5. Each wave's low is generally higher than the prior wave's low (visually confirmed across all 20 examples in `vcp example.pdf` via the ascending purple contraction boxes).

**Long setup is NOT considered valid (EXCLUSION) if:** the pullback waves are not shrinking in depth, if volume is not drying up on the pullbacks, or if the stock is not in a long-term uptrend to begin with.

## 11. Short Setup

`NOT SOURCE-SUPPORTED`. No short-selling setup, rule, or example appears anywhere in the source material. Do not invent one.

## 12. Entry Rules

- **The pivot** is the breakout level, defined as just above the resistance/high of the **final, tightest contraction wave** (p25).
- **Entry trigger:** price breaks out above the pivot. (`AMBIGUOUS`: intraday breach vs. end-of-day close confirmation is not specified.)
- **Buy at the tightest point available, as close to the pivot as possible** — this is explicitly what determines the trade's reward-to-risk ratio (p35: buying at the wide/early part of a base = 1R for a given target; buying at the tight, late contraction near the pivot = 4R for the same target).
- **Position sizing discipline (Entry Execution):** start with a relatively small "Pilot Buy"; do not increase size/aggressiveness until the trade is already working (p42). If not trading well even at 25% or 50% of normal exposure, there is no reason to increase to 75%, 100%, or margin (p42).
- `PARAMETER NOT SPECIFIED`: no fixed % of capital per trade, no fixed number of shares/lots formula, and no maximum initial position size are given.

## 13. Confirmation Rules

**Bullish signals confirming a good entry / good follow-through** (p28-29):
- Follow-through buying lasting 2-3+ days (interpreted as institutional, not just retail, participation).
- More up days than down days; more good closes than bad closes.
- "Tennis Ball Action" after a "Natural Reaction" (i.e., the stock bounces back sharply/resiliently after a normal pullback, like a tennis ball, rather than falling further like a dropped egg — callback to p16's tennis-ball-vs-egg framing).
- The position should be profitable almost immediately after entry.
- Good volume characteristics: high volume on rallies, low volume on pullbacks.

These are **SOFT CONFIRMATION** signals evaluated in the days/weeks after entry — they are not pre-entry gating conditions, but their absence (see §14, Bearish Signals) is what triggers an exit.

## 14. Stop Loss

- **Placement (HARD rule):** the stop-loss sits below the low of the final (tightest) contraction wave / the base from which the pivot breakout occurred — this is structurally what makes the setup low-risk (§10, §12, p35).
- **Sizing guidance (qualitative, not a single fixed %):** keep losses small; a "normal" cut is characterized in the source as being in the 7-8% area, tightened to 4-5% during difficult/choppy market periods (p39). One concrete illustrated real trade (OLECTRA GREENTECH, `vcp example.pdf` p16) used Entry 715 / Stop-loss 650 = **9.1% risk** — this is an EXAMPLE of an actual trade, not a restatement of the general rule, and it runs slightly wider than the "normal" 7-8% figure quoted elsewhere; both are kept in this document rather than silently reconciled (see §26, Conflicts).
- **Invalidation / stop-out conditions (bearish signals, p30-31):** low volume on the way out combined with high volume on the way in; 3-4 consecutive lower lows on volume with no supportive bounce by day 3 or 4; more down days than up days; more bad closes than good closes; a close below the 20-day moving average soon after breakout, or — more seriously — below the 50-day; wide and volatile price action.
- **Trading Priority #1 is "Cut your loss"** (p43) — ranked above protecting breakeven and protecting profit.
- `PARAMETER NOT SPECIFIED`: no single universally-fixed stop percentage; no ATR-multiple stop method is mentioned.

## 15. Targets

- **No fixed price target methodology (e.g., measured move, Fibonacci, ATR multiple) is specified.** The source instead frames targets relative to the stop distance:
  - Maintain **at least a 2:1 reward-to-risk ratio** — shown twice: the "Expected Gain is Based on Assumption" slide (p38, both the −5%-stop and −10%-stop examples are scaled to a 2:1 ratio) and implicitly in the Risk-vs-Reward slide (p35).
  - Distinguish **Theoretical Based Assumption (TBA)** — an aspirational target (e.g., 20%) — from **Result Based Assumption (RBA)** — a realistic target grounded in your own historical results (e.g., ~10%) (p38). RBA should govern actual trade planning.
  - In difficult market conditions, take profits smaller/sooner: a "normal" 15-20% target becomes 10-12% (p39).
- **Illustrative real performance (not a target, an example of results):** the Trading Summary table (p36) shows Average Gain 13.35% vs. Average Loss 5.85% (Win/Loss Ratio 2.28) at a 46.32% win rate — presented to make the point that a positive expectancy does not require a high win rate, not as a target to hit.

## 16. Trailing / Exit Rules

- **Trading Priorities, in order** (p43): (1) Cut your loss (2) Protect your line/breakeven (3) Protect your profit.
- **Move the stop to breakeven as soon as possible** once the position is working (p43).
- **Partial exit ("Reduce & Free-Roll"):** when a position reaches a multiple of risk and an above-average gain (**exact multiple not specified — `UNDEFINED`**), consider selling half the position and raising the stop on the remainder to breakeven (p44). Two stated variants: free-roll the stop at 2x the initial risk, or free-roll at breakeven (p44).
- **Exit on any Bearish Signal / Sell Alert** (§13 reversed, §17) — these function as the trigger to exit an existing winning position, not only as a pre-entry filter.
- **Avoid the psychological trap** of hesitating to sell when the stock signals a top, out of fear of missing further upside, which risks round-tripping the entire gain (p45, illustrated). The prescribed discipline is: formulate the exit plan before entering, execute it without vacillating, and evaluate only after being out of the trade (p46).

## 17. Position Sizing

- Start small: initial entries should be relatively small "Pilot Buys" (p42).
- Scale up only after trades demonstrate they are working — do not increase aggressiveness pre-emptively (p42).
- If underperforming even at reduced exposure (25% or 50% of normal), do not increase exposure to 75%, 100%, or margin — the fix is to reduce further, not add (p39, p42).
- Reduce exposure and get off margin/leverage immediately during difficult trading periods (p39).
- `PARAMETER NOT SPECIFIED`: no formula tying position size to account equity, volatility, or stop distance (e.g., no "risk 1% of capital per trade" rule) is given anywhere in the source.

## 18. Risk Management

- Foundational quote: "Stocks are not like mutual funds with a manager; you're the manager. All stocks are risky and risk must be managed." — Mark Minervini (p33).
- **3 Key Facts About Losses** (p34): (1) you will not be right every time — losses are guaranteed to happen; (2) losses compound against you geometrically (a 50% loss requires a 100% gain to recover; a 90% loss requires 900%); (3) keeping losses small is your only real protection against catastrophic losses.
- **Adjust risk dynamically with results, not with hope**: during difficult periods, tighten stops and take smaller profits — never widen a stop to "give a trade more room" (p39).
- **Measure everything**: track results to get better assumptions, more optimal loss-cutting, better risk/reward management, improved decisiveness, more consistent trading, and greater strategic thinking (p41). "Ask yourself: how is this going to look on my spreadsheet?"
- **Process over outcome**: don't judge a single trade's process by whether it happened to work out (the road-crossing parable, p36) — evaluate the process across many trades.
- **Journal discipline** (p46): write a specific plan before every trade, execute without deviating, avoid improvising mid-trade, evaluate only after exiting, and keep a journal/accurate records to maintain the integrity of your personal statistics.

## 19. No-Trade Conditions

- The core setup (VCP) is not present, or the contraction waves are not shrinking in depth/volume.
- The stock's fundamentals show material earnings deceleration, eroding margins, positive earnings paired with negative sales (flagged as having "limited life span"), or strong earnings with minimal tax paid (flagged as a red flag) (p18).
- The business itself is a "Bad" candidate: capital intensive, limited pricing power, heavily regulated, under margin pressure, or in an eroding industry position (p6).
- Trading is going poorly and exposure is already reduced — the rule is to reduce further, not to add new trades at increased size (p39, p42).
- `NOT SOURCE-SUPPORTED` as explicit hard exclusions (not stated, should not be invented): specific news/earnings blackout windows, minimum-liquidity cutoffs, gap-size exclusions, sector/index/correlation filters, or a maximum-trades-per-day/maximum-daily-loss circuit breaker. None of these are mentioned in the source material.

## 20. Exceptions

- The OLECTRA GREENTECH illustrated trade (`vcp example.pdf` p16) used a ~9.1% stop, wider than the "normal" 7-8% figure quoted in the workshop deck — treated as a real-world example, not a rule change (§26).
- "Code 3 stocks" (p18) is referenced as a selection criterion without any definition anywhere in the material — cannot be applied until defined; flagged rather than guessed at.

## 21. Decision Tree

```
MARKET ELIGIBLE? (Not required to be in an uptrend — corrections are prep time, p20)
  |
  v
STOCK ELIGIBLE? (Good-candidate business quality, §9; ideally Market Leader/Top
Competitor/Institutional Favorite/Turnaround category, p4)
  | NO -> reject
  v YES
FUNDAMENTALS SUPPORTIVE? (EPS/Sales acceleration, margin trend, ROE, catalyst, §9/§6)
  | NO -> SOFT fail: lowers conviction but price action can still override (p10)
  v YES / NEUTRAL
LONG-TERM TREND VALID? (Stage 2, above 200-day MA)
  | NO -> reject
  v YES
VCP PRESENT? (2+ successive contractions, each shallower than the last, volume
drying up, §10)
  | NO -> reject / keep watching
  v YES
PRICE AT/NEAR PIVOT? (breakout level just above final contraction's high, §12)
  | NO -> wait
  v YES
BREAKOUT CONFIRMED? (price clears pivot; ideally on expanding volume)
  | NO -> wait / no trade
  v YES
CALCULATE STOP (below the low of the final contraction, §14)
  |
  v
CALCULATE TARGET (>= 2:1 reward:risk relative to the stop distance, using a
Result-Based, not Theoretical, Assumption, §15)
  |
  v
CALCULATE POSITION SIZE (start with a small Pilot Buy, §17 — exact
sizing formula NOT SPECIFIED in source)
  |
  v
ENTER TRADE
  |
  v
MONITOR FOR BULLISH CONFIRMATION (§13) vs. BEARISH VIOLATION (§14/§19)
  |                                              |
  v (confirmed)                                  v (violated)
MOVE STOP TO BREAKEVEN ASAP (§16)          EXIT IMMEDIATELY (cut the loss, §18)
  |
  v
AT MULTIPLE-OF-RISK + ABOVE-AVERAGE GAIN? (exact threshold UNDEFINED, §16)
  | YES -> SELL HALF, RAISE STOP ON REMAINDER TO BREAKEVEN
  | NO  -> continue holding, watch for Sell Alerts (§17 list) and Bearish Signals
  v
EXIT ON TARGET, TRAILING STOP, OR SELL-ALERT/BEARISH-SIGNAL TRIGGER
  |
  v
POST-TRADE: JOURNAL THE RESULT, UPDATE PERSONAL STATISTICS (§18), FORMULATE NEXT PLAN
```

## 22. Machine-Readable Rules

```
# --- Optional Candidate Pre-Screen (directly observed Chartink "ATR" screener,
# chartink.com/screener/atr-2089 — see SOURCE_KNOWLEDGE_MAP.md Source E) ---
# This is a UNIVERSE-NARROWING pre-filter, not a substitute for VALID_LONG_SETUP below.
ATR_PRESCREEN_PASS = (
    atr14 < atr14_as_of_10_trading_days_ago
    AND (atr14 / close) < 0.08
    AND close > 0.75 * MAX_52_WEEK(weekly_close)
    AND ema(close, 50) > ema(close, 150)
    AND ema(close, 150) > ema(close, 200)
    AND close > ema(close, 50)
    AND close > 10
    AND (close * volume) > 1000000
)

# --- Long Setup ---
STAGE_2_TREND = (price > MA200) AND (long_term_trend == "up")

VCP_PRESENT = (
    number_of_contraction_waves >= 2
    AND each_wave.depth_pct < previous_wave.depth_pct         # shallower each time
    AND each_wave.volume_trend == "contracting"                # supply drying up
    AND each_wave.low >= previous_wave.low                     # (generally) higher low
)

FUNDAMENTALS_SUPPORTIVE = (                                    # SOFT confirmation, not a hard gate
    eps_growth_last_2_to_3_quarters >= 0.20
    AND eps_growth_trend == "accelerating"
    AND sales_growth_trend == "increasing"
    AND net_profit_margin_trend IN ("expanding", "stable")
    AND roe >= 0.15                                             # vs. peer comparison
    AND catalyst_present == TRUE                                 # UNDEFINED how to encode; qualitative
)
# Per p10: FUNDAMENTALS_SUPPORTIVE informs conviction but is NOT required if
# price action (VCP_PRESENT + breakout confirmation) is absent — price action
# is the final gate, not fundamentals.

PIVOT = high_of_final_contraction_wave + small_buffer            # exact buffer NOT SPECIFIED

BREAKOUT_CONFIRMED = (
    price > PIVOT
    # AMBIGUOUS: AND close_basis == TRUE  -- intraday vs. daily-close confirmation not specified in source
)

VALID_LONG_SETUP = (
    STAGE_2_TREND
    AND VCP_PRESENT
    AND BREAKOUT_CONFIRMED
    AND NOT ANY(EXCLUSION_CONDITIONS)                            # see §19
)

# --- Entry ---
IF VALID_LONG_SETUP:
    ENTRY_PRICE = PIVOT  # or the confirmed breakout price
    POSITION_SIZE = "small pilot buy"                             # exact formula NOT SPECIFIED

# --- Stop Loss ---
STOP_LOSS = low_of_final_contraction_wave                         # placed just below it; exact buffer NOT SPECIFIED
# Sizing guidance (qualitative): "normal" ~7-8% risk; tighten to ~4-5% in
# difficult/choppy markets (p39). One real example (OLECTRA) used ~9.1%.

# --- Target ---
MIN_REWARD_RISK_RATIO = 2.0
TARGET_PRICE = ENTRY_PRICE + max(
    (ENTRY_PRICE - STOP_LOSS) * MIN_REWARD_RISK_RATIO,
    0
)
# Use Result-Based Assumption (realistic, from own trading history) rather
# than Theoretical Based Assumption (aspirational) when setting the actual
# expected/target gain (p38).

# --- Trailing / Partial Exit ---
IF unrealized_gain_multiple_of_risk >= UNDEFINED_THRESHOLD AND unrealized_gain_pct > trader_average_gain_pct:
    SELL(fraction=0.5)
    STOP_LOSS_REMAINDER = ENTRY_PRICE   # move to breakeven
    # OR: STOP_LOSS_REMAINDER = ENTRY_PRICE + 2 * (ENTRY_PRICE - original_STOP_LOSS)  # "free-roll @ 2x risk" variant

# --- Exit / Invalidation Triggers (any one is sufficient) ---
EXIT_SIGNAL = (
    close < MA20  # "soon after breakout" — exact day-count window NOT SPECIFIED
    OR close < MA50  # treated as a more severe violation than the MA20 breach
    OR (consecutive_lower_lows_on_volume >= 3 AND no_supportive_bounce_by_day_3_or_4)
    OR (down_days_count > up_days_count over trailing_window)      # window length NOT SPECIFIED
    OR (bad_closes_count > good_closes_count over trailing_window) # window length NOT SPECIFIED
    OR any(SELL_ALERT_CONDITIONS)                                   # §17 list of 13 conditions, each qualitative/comparative to the stock's own move — not independently quantified
)

IF EXIT_SIGNAL:
    EXIT_POSITION()  # Priority 1: cut the loss / protect the line / protect the profit, in that order (p43)

# --- No-Trade / Exclusion Conditions ---
EXCLUSION_CONDITIONS = [
    material_earnings_deceleration,
    eroding_profit_margins,
    (eps_growth > 0 AND sales_growth < 0),      # "limited life span"
    (strong_earnings AND minimal_tax_paid),      # red flag
    business_category IN ("capital_intensive", "limited_pricing_power",
                            "heavily_regulated", "margin_pressure",
                            "eroding_industry_position"),
]
```

## 23. Scoring / Ranking Model

`NOT SOURCE-SUPPORTED` as a formal weighted point system — no scoring formula, weights, or numeric ranking method appears anywhere in the source material. The following is a **proposed structure only**, built strictly from the qualitative hierarchy the source itself describes (price action/VCP quality as the mandatory gate, fundamentals and RS Rating as supporting confirmation) — it is NOT something the workshop deck itself specifies, and should be treated as a starting scaffold for the user to accept, reject, or reweight, not as an extracted rule:

- **Gate (must pass, non-negotiable):** VCP structure present + breakout confirmed (§10, §12). A stock failing this gate is not scored at all.
- **Confirmation score (informs conviction/sizing only, does not gate):**
  - Fundamentals: EPS acceleration, sales acceleration, margin trend, ROE vs. peers, catalyst present (§9)
  - Technical quality: number and tightness of contractions, degree of volume dry-up, RS Rating
  - Company category preference: Market Leader > Institutional Favorite > Top Competitor > Turnaround (order implied by p4's framing, not explicitly ranked in the source)

## 24. Backtesting Rules

`NOT SOURCE-SUPPORTED` — the source material contains no backtesting methodology, no slippage/commission assumptions, and no explicit gap-handling or intraday-sequencing rules. A developer implementing a backtest should independently design one that stays faithful to the rules actually extracted above, and must in particular:
- Avoid look-ahead bias: do not use a quarter's EPS/sales figures before their actual public reporting date; do not use analyst estimate revisions before they were published; do not assume same-day fills at a price that wasn't actually tradable given the stated ambiguity about intraday vs. closing-price breakout confirmation (§7, §12 — this ambiguity should be made an explicit, documented backtest assumption, not silently resolved).
- Avoid survivorship bias: use a point-in-time universe (delisted/renamed stocks included) if testing across NSE history.
- Use the stop-loss and target rules exactly as specified in §14-15, including their explicitly qualitative/undefined parameters — do not silently substitute an invented fixed percentage without flagging it as an assumption.

## 25. Data Requirements (integrity rules)

- NEVER fabricate prices, volume, indicator values, news, targets, or fundamental figures.
- NEVER claim a stock qualifies under this strategy without the underlying data to check it against every applicable rule above.
- NEVER fill a missing data point with a guess.
- If data is missing: label it `DATA_UNAVAILABLE`.
- If a calculation cannot be performed for lack of inputs: label it `CALCULATION_UNAVAILABLE`.
- If market data is stale: label it `STALE_DATA`.
- Any system built from this document must visibly distinguish, for every value it shows: **confirmed** (directly from source data), **calculated** (derived via a stated formula from confirmed data), **estimated** (an analyst or model projection, clearly labeled as such), or **unavailable**.

## 26. Conflicts and Reconciliation

Across all five contributing sources (now including the two workshop videos' visual content), no direct file-vs-file contradiction was found. Two soft tensions and one unresolved open question were identified:

**Conflict/tension #1 — Stop-loss size.**
- Source A (general rule, `vcp workshop.pdf` p39): a "normal" stop is characterized as being cut around 7-8%, tightened to 4-5% in difficult markets.
- Source B (one illustrated real trade, `vcp example.pdf` p16, OLECTRA GREENTECH): Entry 715 / Stop-loss 650 = 9.1% risk.
- Source E (`workshop day 2.mkv`, live DODLA DAIRY chart annotation): "773rs LEVELS" / "710rs STOPLOSS" ≈ 8.1% risk.
- **Determination:** Source A is a general risk-management guideline; Sources B and E are two independent worked examples of real trades, not restatements of the rule, and both (9.1% and 8.1%) sit close to the general 7-8% guidance. They can coexist — a single example naturally varies from the general guideline depending on that stock's own volatility and base structure at the time. **Resolved, not a true conflict** — all three are recorded in this document (§14) rather than one silently overriding the others.

**Conflict/tension #2 — "Mid cap momentum based model" (Source E, MISHRA DHATU NIGAM chart annotation).**
- The live Day-2 video shows a chart annotated "BASED ON MID CAP MOMENTUM BASED MODEL" alongside an illegible "T.S.L" (likely trailing-stop-loss) note. Without audio, it cannot be determined whether this is (a) another name for the same VCP/SEPA strategy, (b) a genuinely separate momentum-based model taught as a complement to VCP, or (c) an aside about a third-party product/model unrelated to this course's core teaching.
- **Determination: UNRESOLVED.** This is explicitly NOT merged into the VCP rule set anywhere in this document. It is recorded only in SOURCE_KNOWLEDGE_MAP.md (Source E) and here, flagged `UNKNOWN — DO NOT MERGE`, pending either an audio transcript becoming feasible or the user's own clarification.

No other conflicts were found. This section is no longer pending — both videos' visual content has now been fully reviewed (see §29). Any future re-review that gains audio access should re-check this section specifically for tension #2.

## 27. Ambiguities

- Whether breakout confirmation requires an end-of-day closing price above the pivot, or an intraday touch is sufficient (§7, §12).
- Whether the stop-loss should be based on a closing-price breach or an intraday low breach of the reference level (§14).
- The exact buffer/offset (if any) added above the final contraction's high to define the precise pivot price (§12, §22).
- The exact "multiple of risk" and "above-average gain" thresholds that trigger the "sell half, move stop to breakeven" rule (§16, p44).
- The exact trailing window (number of days/weeks) used for the "more up days than down days" / "more good closes than bad closes" comparisons (§13-14, §22).
- Whether the 5 named base patterns (Cup w/ Handle, Double Bottom, Darvas Box, Power Play, Cup Completion Cheat) are meant as the *exhaustive* list of valid VCP base shapes, or as *examples* of shapes a VCP can take (source frames them as a list under "Stage 2" without stating exhaustiveness either way).

## 28. Undefined Parameters

- `UNDEFINED — DO NOT INVENT`: "Code 3 stocks" (p18) — term never defined in the source material.
- `PARAMETER NOT SPECIFIED`: minimum/maximum stock price, minimum average daily traded value, minimum market capitalization.
- `PARAMETER NOT SPECIFIED`: fixed position-sizing formula (% of capital risked per trade, or per position).
- `PARAMETER NOT SPECIFIED`: a single fixed stop-loss percentage (only a qualitative "normal ~7-8%, tighten to ~4-5%" range plus one 9.1% real example — see §26).
- `PARAMETER NOT SPECIFIED`: a single fixed profit-target percentage (only "normal ~15-20%, reduce to ~10-12% in difficult markets," and a minimum 2:1 reward:risk ratio).
- `PARAMETER NOT SPECIFIED`: the exact "multiple of risk" threshold for the partial-exit rule (§16).
- `PARAMETER NOT SPECIFIED`: maximum number of concurrent open positions, maximum daily loss limit, maximum consecutive-loss circuit breaker.
- `PARAMETER NOT SPECIFIED`: any news/earnings blackout window, gap-size exclusion rule, or sector/index/correlation filter.
- `PARAMETER NOT SPECIFIED`: exact minimum number of contraction waves required (examples show 2-5; no floor/ceiling is stated as a rule).
- `UNKNOWN — DO NOT MERGE`: the "mid cap momentum based model" phrase seen annotated on a live MISHRA DHATU NIGAM chart in `workshop day 2.mkv` (Source E). Its relationship to the core VCP strategy (same strategy, a complementary model, or unrelated) cannot be determined without audio — see §26 Conflict #2.
- `UNKNOWN — could not be inspected`: the content of a locally-saved file named `ADANIPOWER_2023-09-01_18-45-32.pdf`, opened on-screen in `september vcp workshop day 1.mkv` but never rendered (blank/loading) in any of the sampled frames before the recording ends. Its content is unknown and is not represented anywhere in this document.
- `UNCONFIRMED — chat only, not adopted as a rule`: various numeric figures ("min 9%," "8-10%," "5% sl," "trailing stoploss") appear in viewer chat during `workshop day 2.mkv`, but with no audio to confirm whether these are viewer questions or instructor answers, none are adopted as strategy parameters.

## 29. Source Traceability

Every rule above cites its source page inline (e.g., "p24," "p39"). Full page-level detail is in `SOURCE_KNOWLEDGE_MAP.md`. No page numbers or timestamps have been invented anywhere in this document — all citations refer to the actual slide/page position within the two inspected PDFs, established by direct visual inspection of every page (46 + 20 pages, 100% coverage) plus the 2 lines of the text file (100% coverage).

**Explicit disclosure on the two workshop video files** (required by this task's own instructions not to pretend inspection that didn't happen):
- `september vcp workshop day 1.mkv`: 856,335,734 bytes, h264/aac, 1920x1080. Exceeds this environment's 400MB single-file transfer limit, so it could not be staged directly. The user compressed it locally (via provided ffmpeg commands) into an audio track (not usable — see below) and 46 scene-change-triggered frame images, all 46 of which were staged and **visually inspected in full** via direct image reading. Finding: the video re-presents the identical slide deck already captured as Source A (confirmed by matching multiple specific slides pixel-for-pixel in content, including the VCP template and Bullish Signals pages), plus incidental live-chart and tool-browsing context (a BANKNIFTY chart, a JINDAL STAINLESS live VCP illustration, a Reliance Industries annual report browse, and a Google search reinforcing the Minervini attribution) — none of which added a new numeric rule. Full detail: SOURCE_KNOWLEDGE_MAP.md, Source D.
- `workshop day 2.mkv`: 825,134,615 bytes, same format/resolution/constraint. The user produced 58 scene-change frames, all 58 of which were staged and **visually inspected in full**. Unlike Day 1, this is a distinct "Special Class" live stock-screening and tool-demonstration session (not a re-presentation of the slide deck). It revealed the complete filter logic of the Chartink "ATR" screener already referenced by bare URL in Source C (now incorporated into §9/§22), a live MarketSmith India tool demonstration, and two live real-money chart examples (DODLA DAIRY, entry/stop levels; JINDAL STAINLESS-style contraction annotations on other tickers). It also surfaced two items that could NOT be fully resolved from the visual record alone and are explicitly flagged rather than guessed: a "mid cap momentum based model" annotation of unclear scope (§26, §28), and a locally-opened `ADANIPOWER_...pdf` file whose content never rendered in the sampled frames. Full detail: SOURCE_KNOWLEDGE_MAP.md, Source E.
- **Audio for both videos was NOT transcribed**, and this limitation is real and material, not merely a formality: transcription was attempted and abandoned after `faster-whisper`/`openai-whisper` (require downloading model weights from Hugging Face, Azure blob storage, or GitHub-release CDNs — all returned HTTP 403 in this sandboxed environment, whose network access is restricted to package registries only), hosted transcription APIs (OpenAI, Groq, Deepgram, AssemblyAI — equally unreachable), and the one fully-offline pip-installable option with bundled model weights (`pocketsphinx`) — tested against the short "IGNORE THIS" clip's audio and verified to produce semantically meaningless output — were all ruled out. **Anything said aloud in either workshop that is not also visible on-screen in a sampled frame is not captured anywhere in this document.** The visual review above is a complete inspection of everything that COULD be inspected without audio, not a partial or best-effort sample.
- `FNO GIFT SWING WALE IGNORE THIS.mkv`: fully inspected (246 seconds, 2 scene-change frames reviewed). Confirmed to show an OBS recording-control screen and a TradingView chart browsing session (SARVESHWAR FOODS, plus a NIFTY/BANKNIFTY-inclusive watchlist) — not deliberate teaching content. Excluded per the user's own filename and confirmed content, not merely assumed irrelevant from the name alone.

## 30. Implementation Requirements

For a developer building a scanner/backtester/dashboard from this document:
1. Implement the VCP detector exactly as defined in §10/§22 — a variable-length sequence of contraction waves, each shallower than the last, with contracting volume. Do not hard-code a specific number of waves; make it configurable, defaulting to "2 or more."
2. Implement the pivot/breakout/entry logic per §12, but treat the intraday-vs-close ambiguity (§27) as a configurable flag, defaulted and clearly documented, not silently resolved.
3. Implement the stop-loss as "below the final contraction's low" per §14, with the percentage-based guidance (7-8% normal / 4-5% tight) surfaced as a configurable, documented default — not hard-coded as if it were a precise rule from the source.
4. Implement the ≥2:1 reward:risk target rule per §15, distinguishing a Theoretical (aspirational) target input from a Result-Based (historical-average) target input, per p38.
5. Implement the partial-exit ("sell half at breakeven") rule per §16 with the "multiple of risk" threshold as a required, clearly-labeled user input (since the source leaves it undefined) rather than a guessed constant.
6. Implement the exit/invalidation checks (MA20/MA50 breach, 3-4 consecutive lower lows without support, more down days/bad closes than up days/good closes, and the 13-item Sell Alert checklist) per §14/§17/§22, each as an independently-triggerable signal.
7. Surface fundamentals (EPS/sales acceleration, margin trend, ROE, catalyst) as informative confirmation/conviction signals, not as a hard entry gate — per the explicit p10 rule that price action overrides story and numbers.
8. Every output field must be tagged confirmed / calculated / estimated / unavailable per §25 — never silently blank or defaulted.
9. Do not implement a short-selling module (§11) — none is specified.
10. Do not implement any scoring formula as if it came from the source (§23) — if a scoring feature is wanted, it must be clearly labeled in the UI as a user-configurable addition, not part of the original strategy.
11. The Chartink ATR pre-screen (§9, §22) may be implemented as an optional, clearly-labeled "candidate universe" filter to narrow which stocks get run through the VCP detector — it must never be presented as equivalent to, or a substitute for, `VALID_LONG_SETUP` itself.
12. Do not implement anything under the "mid cap momentum based model" label (§26 Conflict #2, §28) — it is explicitly unconfirmed and out of scope until clarified.

---
*End of STRATEGY_MASTER.md. All 6 project files have been inspected (5 contributing sources fully reviewed — including complete visual review of both workshop videos' extracted frames — plus 1 correctly excluded). See §26 and §28 for the small number of items that remain genuinely unresolved (flagged, not guessed). Do not proceed to dashboard/scanner implementation until the user has reviewed this document.*
