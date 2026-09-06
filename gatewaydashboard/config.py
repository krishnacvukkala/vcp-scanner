"""Gateway Dashboard — configuration.

Every tunable here carries a tag saying where the number came from:

    SOURCE  the value is stated in, or was directly read off, the workshop
            material. The bracketed reference points at ../STRATEGY_MASTER.md
            and the underlying slide (e.g. "§9, p39").

    USER    the workshop material does not specify this value. It is a decision
            you own. Change it freely — every result the dashboard shows that
            depended on a USER value is labelled as such.

That split is the whole point of this file. STRATEGY_MASTER.md flags around a
dozen parameters as PARAMETER NOT SPECIFIED or UNDEFINED — DO NOT INVENT.
Quietly hard-coding a plausible guess, so that it later reads like a rule from
the workshop, is the specific failure this project is built to avoid.
"""

# ---------------------------------------------------------------------------
# Data provider
# ---------------------------------------------------------------------------
YF_SUFFIX = ".NS"              # USER  NSE cash listings are ".NS" on Yahoo
HISTORY_PERIOD = "3y"          # USER  needs >=200 sessions for EMA200 + 52w high
CACHE_DIR = ".cache"           # USER  relative to the project folder
CACHE_TTL_HOURS = 6            # USER  re-download nothing inside this window
BATCH_SIZE = 40                # USER  tickers per yfinance multi-download call
REQUEST_PAUSE_SEC = 0.7        # USER  pause between batches; Yahoo rate-limits
MAX_TICKERS = 0                # USER  0 = no cap; set e.g. 50 for a quick run

# ---------------------------------------------------------------------------
# Stage 1 — Chartink "ATR" pre-screen
# All seven conditions below were read verbatim off the screener shown on
# screen in `workshop day 2.mkv` (chartink.com/screener/atr-2089, "Tight
# Stocks"). They narrow the universe; they do NOT constitute a valid setup.
# [STRATEGY_MASTER.md §9, §22]
# ---------------------------------------------------------------------------
ATR_PERIOD = 14                # SOURCE  §9 condition 1-2
ATR_LOOKBACK_SESSIONS = 10     # SOURCE  §9 condition 1 ("10 days ago")
ATR_TO_CLOSE_MAX = 0.08        # SOURCE  §9 condition 2
PCT_OF_52W_HIGH_MIN = 0.75     # SOURCE  §9 condition 3 (within 25% of 52w high)
EMA_FAST = 50                  # SOURCE  §9 condition 4-5
EMA_MID = 150                  # SOURCE  §9 condition 4
EMA_SLOW = 200                 # SOURCE  §9 condition 4
MIN_CLOSE_INR = 10.0           # SOURCE  §9 condition 6 (penny-stock exclusion)
MIN_TURNOVER_INR = 1_000_000.0  # SOURCE  §9 condition 7 (close x volume)
PRESCREEN_REQUIRED = False     # USER    §9 calls it a pre-screen, not a gate

# ---------------------------------------------------------------------------
# Stage 2 — trend and VCP structure  [§10, §22]
# ---------------------------------------------------------------------------
SMA_LONG = 200                 # SOURCE  §22 STAGE_2_TREND: price > MA200
SMA_MID = 50                   # SOURCE  §6, §14
SMA_SHORT = 20                 # SOURCE  §6, §14
TREND_SLOPE_SESSIONS = 20      # USER    "long_term_trend == up" left qualitative
                               #         in §22; read as a rising MA200 over
                               #         this many sessions

MIN_CONTRACTIONS = 2           # SOURCE  §10 rule 2 ("2 or more")
MAX_CONTRACTIONS = 6           # USER    §28: no ceiling stated; examples show
                               #         2-5 (CYBERTECH is the 5)
BASE_MAX_SESSIONS = 325        # USER    ~65 weeks, the longest base duration
                               #         named on p19; caps how far back a base
                               #         may start
BASE_MIN_SESSIONS = 20         # USER    ~4 weeks, the shortest (Darvas Box, p19)
SWING_WINDOW = 5               # USER    half-width for fractal swing detection;
                               #         no swing definition given in source
DEPTH_MUST_SHRINK = True       # SOURCE  §10 rule 3 (each wave shallower)
HIGHER_LOW_TOLERANCE = 0.02    # USER    §10 rule 5 says lows are "generally"
                               #         higher — this is how much slack that
                               #         word is given
VOLUME_DRYUP_REQUIRED = True   # SOURCE  §10 rule 4
VOLUME_DRYUP_RATIO_MAX = 1.00  # USER    final-wave avg volume / first-wave avg
                               #         volume must be below this
MIN_DEPTH_PCT = 0.03           # USER    ignore noise wiggles below this depth;
                               #         §28 states no floor is specified

# ---------------------------------------------------------------------------
# Stage 3 — entry, stop, target  [§12, §14, §15, §27]
# ---------------------------------------------------------------------------
PIVOT_BUFFER_PCT = 0.0         # USER    §27: the exact buffer above the final
                               #         contraction's high is not specified
BREAKOUT_ON_CLOSE = True       # USER    §27 ambiguity made explicit: True =
                               #         daily close must clear the pivot,
                               #         False = an intraday touch counts
STOP_BUFFER_PCT = 0.0          # USER    §22: "just below" is not quantified
NEAR_PIVOT_PCT = 0.02          # USER    how close below the pivot counts as
                               #         "at the pivot" on the dashboard; a
                               #         display band, not a rule
BREAKOUT_VOLUME_RATIO_MIN = 1.5  # USER  breakout volume / 50-session average
                               #         that counts as "expanding". §10 and
                               #         §13 require expanding volume but never
                               #         quantify it, so this only annotates
MIN_REWARD_RISK = 2.0          # SOURCE  §15, p38

# p39 gives two regimes rather than one number. DIFFICULT_MARKET picks which
# pair is used for the "is this risk normal?" and "is this target sane?"
# annotations. Neither band blocks a trade — they annotate it.
NORMAL_RISK_BAND = (0.07, 0.08)    # SOURCE  §14, p39 "normal" cut
TIGHT_RISK_BAND = (0.04, 0.05)     # SOURCE  §14, p39 difficult periods
NORMAL_TARGET_BAND = (0.15, 0.20)  # SOURCE  §15, p39
TIGHT_TARGET_BAND = (0.10, 0.12)   # SOURCE  §15, p39
DIFFICULT_MARKET = False           # USER    you assess the regime, p39 does not
                                   #         define a test for it
MAX_RISK_PCT_HARD = 0.0            # USER    0 = disabled. §28 records that no
                                   #         hard maximum risk exists in the
                                   #         source; the OLECTRA example ran 9.1%

PARTIAL_EXIT_R_MULTIPLE = None     # USER    §16/§28: the "multiple of risk" that
                                   #         triggers sell-half-and-move-to-
                                   #         breakeven is UNDEFINED in the
                                   #         source. None = the rule stays off
                                   #         and the dashboard says so. Set a
                                   #         number (p44 mentions a 2x free-roll
                                   #         variant) to switch it on as yours.

# ---------------------------------------------------------------------------
# Stage 4 — exit and violation checks  [§14, §17, §22]
# ---------------------------------------------------------------------------
CONSEC_LOWER_LOWS = 3          # SOURCE  §14, p30 ("3-4 consecutive lower lows")
NO_SUPPORT_BY_DAY = 4          # SOURCE  §14, p30
BREAKOUT_WATCH_SESSIONS = 15   # USER    §27: "soon after breakout" has no
                               #         defined window
UPDOWN_WINDOW_SESSIONS = 10    # USER    §27: the trailing window for "more up
                               #         days than down days" is not specified
GOOD_CLOSE_RANGE_POS = 0.5     # USER    §14 counts "bad closes" vs "good
                               #         closes" without defining either. This
                               #         reads a good close as one finishing
                               #         above this fraction of the session's
                               #         high-low range.
LOWER_LOW_VOLUME_RATIO = 1.0   # USER    §14 says lower lows "on volume"; this
                               #         is how much of the 50-session average
                               #         volume the run must average to count

# ---------------------------------------------------------------------------
# Fundamentals — SOFT confirmation only, never an entry gate
# p10 is explicit: "Never trust the story. Never trust the numbers. Unless
# confirmed by price action." Nothing below can reject a setup; it only moves a
# conviction note.  [§9, §6]
# ---------------------------------------------------------------------------
FUNDAMENTALS_ENABLED = True     # USER   costs one extra yfinance call per stock
FUND_EPS_GROWTH_MIN = 0.20      # SOURCE §9, p18 ("+20%+ in recent 2-3 quarters")
FUND_QUARTERS = 3               # SOURCE §9, p11 ("most recent 3 quarters")
FUND_ROE_MIN = 0.15             # SOURCE §6, p15 ("15-17%+ is a good cutoff")
FUND_GROWTH_BASIS = "yoy"       # USER   "yoy" compares a quarter with the same
                                #        quarter a year earlier, "qoq" with the
                                #        quarter before it. p18 says "+20%+ in
                                #        recent quarters" without saying which.
FUND_MARGIN_TOLERANCE = 0.005   # USER   net-margin move within +/-50bps counts
                                #        as "stable"; §22 names the categories
                                #        expanding/stable/eroding but defines no
                                #        boundary between them
FUND_DECELERATION_DROP = 0.25   # USER   §19's "material earnings deceleration"
                                #        is unquantified. This is how much EPS
                                #        growth must fall, in percentage points,
                                #        between quarters to count as material
FUND_MIN_TAX_RATE = 0.10        # USER   §19 flags "strong earnings with minimal
                                #        tax paid" without defining minimal;
                                #        this is the effective-rate floor
FUND_EXCLUSIONS_GATE = False    # USER   §22 puts the §19 exclusions inside
                                #        VALID_LONG_SETUP, so by default a
                                #        confirmed exclusion blocks a setup. The
                                #        exclusions are SOURCE but the four
                                #        thresholds above are not — set this
                                #        False to demote them to warnings.

# ---------------------------------------------------------------------------
# Local server
# ---------------------------------------------------------------------------
HOST = "127.0.0.1"   # loopback only. This app has no authentication or access
                     # control of any kind — do not change this to 0.0.0.0 or
                     # bind it to a public interface.
PORT = 8765


# ---------------------------------------------------------------------------
# Provenance table
# ---------------------------------------------------------------------------
# Rather than maintain a second copy of the SOURCE / USER tags above (which
# would drift the moment someone edits a comment), the table is parsed out of
# this file's own comments at import time. The comments are the single source of
# truth; the dashboard reads this table to badge every number it displays.

def _parse_provenance():
    """Read the `# SOURCE ...` / `# USER ...` tag off each assignment above."""
    import re
    from pathlib import Path

    table = {}
    try:
        lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    except (OSError, NameError):        # frozen or exec'd without a real file
        return table

    assign = re.compile(r"^([A-Z][A-Z0-9_]*)\s*=.*?#\s*(SOURCE|USER)\s*(.*)$")
    trailing = re.compile(r"^\s+#\s{2,}(.*)$")
    current = None
    for line in lines:
        m = assign.match(line)
        if m:
            name, origin, note = m.group(1), m.group(2), m.group(3).strip()
            table[name] = {"origin": origin, "note": note}
            current = name
            continue
        cont = trailing.match(line)
        if cont and current:
            table[current]["note"] = (
                table[current]["note"] + " " + cont.group(1).strip()
            ).strip()
        elif not line.strip().startswith("#"):
            current = None
    return table


PARAM_PROVENANCE = _parse_provenance()


def provenance_of(name):
    """('SOURCE'|'USER'|'UNKNOWN', note) for a config constant."""
    entry = PARAM_PROVENANCE.get(name)
    if not entry:
        return ("UNKNOWN", "not tagged in config.py")
    return (entry["origin"], entry["note"])


def user_set_params():
    """Every parameter you own rather than inherited from the workshop."""
    return {
        name: {"value": globals().get(name), **meta}
        for name, meta in sorted(PARAM_PROVENANCE.items())
        if meta["origin"] == "USER"
    }
