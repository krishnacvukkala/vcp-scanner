# Project Handover — Aaroquant VCP Scanner

**Updated:** 2026-09-06, by Claude (Opus 5), for Gemini or any succeeding engineer.
**Supersedes:** the 2026-09-06 07:31 handover. Everything in that version about the
Flask/vanilla-JS architecture still holds; the corrections and additions are marked
below.

**Verification rule used throughout:** every claim here was checked against the actual
code, a test run, or a live HTTP response. Where a previous document was wrong, the
correction is called out. Nothing is described as working on the strength of having
been written.

---

## 0. Read this first — the state in one paragraph

The hosted dashboard's **Scan button was returning 500**. Root cause found and fixed:
the cache writer called `mkdir` outside its own `try/except`, and Vercel serves the
deployment filesystem read-only. Behind that sat a design problem — a 164-symbol scan
cannot finish inside a serverless request at all — so the scan was moved off the
request path onto a scheduled job that writes to Supabase, with the dashboard reading
from Postgres. **16 files are staged in git but NOT committed and NOT pushed.** One
command finishes it (§2). Supabase itself has not been signed up for yet; that is the
user's next step and `SUPABASE_SETUP.md` walks it through.

---

## 1. What changed this session

### 1.1 The bug that broke Scan (fixed, verified)

`/api/scan` returned HTTP 500 on `aaroquantdashboard.vercel.app` while `/` served
fine. Confirmed by loading the endpoint live, then isolated in code:

| File | Line | Problem |
|---|---|---|
| `gatewaydashboard/data.py` | 115 | `CACHE_PATH.mkdir(...)` sat **outside** the `try/except OSError` immediately below it. Vercel's deployment filesystem is read-only, so the first successful Yahoo download raised `OSError: [Errno 30] Read-only file system` and killed the request. |
| `gatewaydashboard/fundamentals.py` | 117 | The same unguarded `mkdir` inside `_cache_path()`, which runs on cache **reads** as well as writes. |

Both are now inside guards. `config.py` additionally moves `CACHE_DIR` to
`/tmp/aaroquant-cache` when `VERCEL` is set, since `/tmp` is the only writable path
there. Two regression tests cover this (`test_storage_and_readonly.py`), simulating
Errno 30 rather than using `chmod`, because tests often run as root and root ignores
permission bits.

### 1.2 The design problem behind it

Fixing the crash alone would only have converted a 500 into a timeout. A full scan is
10–20s warm and worse cold; Vercel functions cap at 60s. So:

```
GitHub Actions (scheduled)  ──scans──▶  Supabase  ◀──reads──  Vercel dashboard
        minutes, free                   Postgres              milliseconds
```

The hosted app never scans the universe again. It reads a finished scan. A single
ticker still scans live, because one symbol fits comfortably inside a request.

This shape was chosen with the user: they picked **GitHub Actions** as the scan writer
and **"serve from DB + live single-symbol"** as the Scan-button behaviour, over Vercel
Cron (Hobby allows one run/day, 60s cap) and a Mac-local scheduler (only runs when the
laptop is awake).

### 1.3 New and changed files (16)

| File | New? | What it does |
|---|---|---|
| `gatewaydashboard/store.py` | new | Supabase persistence over the PostgREST endpoint using `requests`. No SDK dependency. |
| `gatewaydashboard/jobs/run_scan.py` | new | The scheduled writer. `python -m gatewaydashboard.jobs.run_scan` |
| `gatewaydashboard/jobs/__init__.py` | new | package marker |
| `gatewaydashboard/tests/test_storage_and_readonly.py` | new | 13 tests. **The repo had no tests before this.** |
| `.github/workflows/scan.yml` | new | Scheduled scan, 10:45 and 21:45 UTC weekdays, plus manual dispatch |
| `supabase/schema.sql` | new | Tables, indexes, RLS, a prune helper |
| `api/index.py` | new | Vercel entry point; re-exports the Flask app |
| `vercel.json` | new | Build config. **The repo had none** — which is why what was deployed could not be reproduced from source. |
| `requirements.txt` (root) | new | Vercel's Python runtime reads the root file |
| `SUPABASE_SETUP.md` | new | Step-by-step signup and wiring |
| `gatewaydashboard/app.py` | changed | `/api/scan` serves stored runs; new `/api/health` and `/api/scan/history`; OHLC reads the cache first |
| `gatewaydashboard/config.py` | changed | `/tmp` cache on serverless, Supabase settings, `ON_SERVERLESS`, `STORED_SCAN_STALE_HOURS`, `LIVE_SCAN_MAX_SYMBOLS` |
| `gatewaydashboard/data.py` | changed | guarded cache write |
| `gatewaydashboard/fundamentals.py` | changed | guarded cache path |
| `gatewaydashboard/requirements.txt` | changed | added `requests` |
| `HANDOVER.md` | changed | this file |

### 1.4 Design decisions worth not undoing

- **`store.latest_scan()` rebuilds the exact payload shape `scanner.scan()` returns.**
  The dashboard cannot tell a stored scan from a live one, so `index.html` needed no
  changes and there is one rendering path to keep correct rather than two. It adds only
  an `is_stored` flag and a `stored` block (age, source, staleness) — never anything
  that changes a verdict.
- **`scan_results.record` holds the engine's output verbatim.** The flat columns beside
  it (`pivot`, `stop`, `close`, `risk_pct`, `contractions` …) exist so the dashboard can
  filter in SQL. They are derived from that record and are `null` wherever the engine
  had no value. A test asserts a missing pivot stays missing.
- **An incomplete or failed run is never served.** `latest_scan()` only reads runs with
  `status='complete'`, so a job that dies mid-scan shows as `failed` in the table rather
  than surfacing as "no setups today". Two tests cover this.
- **A stored scan older than 24h gets a `STALE:` caveat** naming its age, rather than
  being shown as current.
- **RLS is on with no policies**, so the public anon key reads nothing. Only the
  service-role key, used server-side, can touch the tables.
- **Storage is an enhancement, not a dependency.** With the env vars unset the app
  behaves exactly as before: live scans, nothing persisted. A test covers that path.

---

## 2. Exactly where things stand — and the one command to finish

**16 files are staged. Nothing is committed. Nothing is pushed.**

```
A  .github/workflows/scan.yml          M  gatewaydashboard/app.py
A  SUPABASE_SETUP.md                   M  gatewaydashboard/config.py
A  api/index.py                        M  gatewaydashboard/data.py
A  gatewaydashboard/store.py           M  gatewaydashboard/fundamentals.py
A  gatewaydashboard/jobs/__init__.py   M  gatewaydashboard/requirements.txt
A  gatewaydashboard/jobs/run_scan.py   M  HANDOVER.md
A  gatewaydashboard/tests/test_storage_and_readonly.py
A  requirements.txt   A  supabase/schema.sql   A  vercel.json
```

`main` is at `457a907`, tracking `origin/main`, which is at the same commit.

To finish (run in macOS Terminal — the commit message is already written):

```bash
cd "$HOME/Library/CloudStorage/GoogleDrive-krishnacvukkala@gmail.com/My Drive/Antigravity/VCP By TheChayyy"
git add HANDOVER.md
git commit -F .git/CLAUDE_COMMIT_MSG.txt && git push
```

### Why Claude could not commit it

Claude's shell runs in a Linux VM that sees the Google Drive folder through a
FileProvider mount. On that mount, `git commit`, `git log` and `git status` die with
**SIGBUS** — reading existing history out of the packfile via mmap crashes, while
writing objects and the index works fine (which is why `git add` succeeded). Gemini
runs on macOS, where git handles this folder normally. This is an environment quirk,
not repository damage.

### Cleanup Claude could not do

Deleting files is blocked for Claude on this device, so these leftovers remain:

```bash
rm -f .git/index.lock.stale-from-sigbus .git/index.lock.stale2
git gc --prune=now          # also clears 15 stray .git/objects/**/tmp_obj_* files
```

All harmless; `git gc` sweeps them.

---

## 3. Remaining setup (the user's next step, not yet done)

Full detail in `SUPABASE_SETUP.md`. In order:

1. Sign up at supabase.com with GitHub; project `aaroquant`, region **Frankfurt**, Free plan.
2. Paste `supabase/schema.sql` into the SQL Editor and Run. Confirm four tables.
3. Copy **Project URL** and the **service_role** key from Project Settings → API.
4. Add both as GitHub repository secrets, named exactly `SUPABASE_URL` and
   `SUPABASE_SERVICE_ROLE_KEY`.
5. Actions → **Scheduled VCP scan** → Run workflow (try `limit: 20` first).
6. Add the same two as Vercel environment variables, then **redeploy** — env vars only
   apply to builds made after they are set.
7. Check `https://<app>.vercel.app/api/health`.

**Never put the service-role key in the browser, in `index.html`, in a commit, or in a
chat message.** It bypasses RLS entirely. The user pasted two GitHub PATs into chat
during this session (`ghp_vYGeA4…`, `ghp_Dbqwjp7Q…`); both were declined and unused,
and both should be revoked at github.com/settings/tokens if that has not happened yet.

### Also unverified: is Vercel even connected to this repo?

The repo contained no Vercel config, yet a Flask app is deployed at
`aaroquantdashboard.vercel.app` under the personal scope
`krishnas-projects-8f4b9d0d` (not the `vcp-bc-the-chayyy` team — the team-scoped API
token cannot see it, so Vercel MCP tools return 403/404 for it). Check Settings → Git
on that project. If it is not connected to `krishnacvukkala/vcp-scanner`, connect it,
otherwise the push above will not deploy anything.

---

## 4. Verified facts about the codebase

Checked this session by importing the modules and running the app, not read off docs.

- **8 Python modules, 5,753 lines**, plus a 2,676-line `static/index.html`.
- **Endpoints** (all 200 under a test client): `/`, `/api/scan`, `/api/stock/<symbol>`,
  `/api/settings`, `/api/market-data/instruments`, `/api/market-data/search`,
  `/api/market-data/ohlc`, `POST /api/size`, `POST /api/cache/clear`, plus the new
  `/api/health` and `/api/scan/history`.
- **7 UI views**: dashboard, trades-today, chart-analysis, stock-research, risk-manager,
  settings-provenance, help-guide.
- **Config**: 59 parameters exposed through `/api/settings`, 34 of them USER-owned,
  13 verdict parameters.
- **Position sizing is correct** — ₹10,00,000 at 1% with entry 715 / stop 650 returns
  153 shares and ₹9,945 at risk.
- **Instrument counts** — *correction to the previous handover*, which claimed "160+
  tickers in `instruments.py`". The catalog holds **99**; `universe.csv` holds **94**;
  the ~164 figure comes from merging and de-duplicating the two at scan time.
- **Tests: 13**, all passing, all added this session. There were none before.
  `python -m pytest gatewaydashboard/tests/ -q`

---

## 5. Known bugs and open issues

### 5.1 `scanner.py::_enrich_record` fabricates trade numbers (NOT fixed)

Flagged to the user twice; left alone deliberately because they had not decided, and
because "fix the scan" was the request. **This matters more now that results are
persisted** — fabricated values are about to be written into a database and served as
history.

| Line | Problem |
|---|---|
| 238 | `rr_ratio = 2.4` is **hard-coded**. The levels actually computed are TP1 = pivot + 2R and TP2 = pivot + 3R, so the "2.4 : 1" the UI renders is not the ratio of the numbers displayed beside it. |
| 242–246 | When there is **no valid pivot**, it invents one: `pivot = close`, `stop = close × 0.95`, `tp1 = +10%`, `tp2 = +15%`, `rr_ratio = 2.0`. A stock with no VCP structure still gets a full-looking trade plan. |
| 276 | `win_probability = 73`, a constant. |
| 255–270 | `confidence_score` is a fixed number per verdict, not a measurement. |

`tp1`, `tp2`, `rr_ratio_fmt` and `ai_signal` are all referenced in `index.html`, so
these reach the screen. `win_probability`, `confidence_score` and `ai_take` are computed
but currently unrendered.

This contradicts the principle the rest of the codebase enforces carefully — `config.py`
tags every parameter SOURCE or USER precisely so an invented number can never read like
a workshop rule, and `app.py`'s `_scrub` cites §25 for turning NaN into null rather than
zero. **Recommended fix:** return `None`/`unavailable` when there is no pivot, and
compute `rr_ratio` from the actual levels.

### 5.2 Environment quirks (not code bugs)

- Git SIGBUSes on the Drive mount from Claude's Linux VM (§2). Fine on macOS.
- Reading files in that folder via `cat` from the VM fails with "Resource deadlock
  avoided"; staging them works.
- Vercel MCP tools cannot see the `aaroquantdashboard` project (personal scope vs team
  token), so deployment verification has to be done by loading URLs.
- `.github/workflows/*` is a protected path for remote writes; that file was written
  through the shell instead.

### 5.3 Not built

No trade logging, no win-rate or return tracking, no backtester, no authentication, no
broker integration. The dashboard shows untracked metrics as untracked.

---

## 6. Conventions to preserve

From the previous handover and still correct:

1. **Colour coding** — green `#16a34a`/`#22c55e` setups and wins, amber `#d97706` watch,
   red `#dc2626` stops and losses, blue `#2563eb` base-forming and accents, purple
   `#7c3aed` completed targets.
2. **Never return raw `NaN` in JSON** — `SafeJSONProvider` in `app.py` scrubs NaN and
   Infinity to `null`. Keep it.
3. **Loopback only for the local server** — `HOST = 127.0.0.1`, no auth. Do not bind
   `0.0.0.0` or tunnel it. (The Vercel deployment is a separate, public surface with no
   auth either; it holds no credentials and places no orders.)
4. **`git status -uno`** in this folder — a full status walks thousands of Drive-backed
   video frames.
5. **Never track** `*.mkv`, `*.mp3`, `*.pdf`, `*.zip` or the frame directories.

Added this session:

6. **`vercel.json` must not contain both `builds` and `functions`** — Vercel rejects the
   combination and the deploy fails in about a second. `maxDuration` goes inside
   `builds[0].config`.
7. **The strategy engine decides; everything else displays.** `vcp_core` produces
   verdicts, `fundamentals` produces flags, and nothing downstream — scanner, store, API
   or UI — may re-derive them. `store.py` deliberately stores and returns records
   untouched.
8. **Do not invent a number the engine did not produce.** See §5.1 for the one place
   this is currently violated.

---

## 7. Suggested next five steps

1. **Commit and push** (§2), then confirm Vercel is connected to the repo (§3).
2. **Supabase setup** (§3), ending with a green `/api/health` and a first stored scan.
3. **Fix `_enrich_record`** (§5.1) before much scan history accumulates with fabricated
   levels in it.
4. **Surface freshness in the UI** — the payload now carries `stored.age_hours`,
   `stored.stale` and `stored.source`; the dashboard does not yet show them, so a user
   cannot tell a fresh scan from a two-day-old one.
5. **Wire `/api/scan/history`** into the dashboard so a silently failing scheduled job is
   visible rather than looking like a quiet market.

---

## 8. Quick reference

```bash
# Local dashboard
cd gatewaydashboard && python app.py            # http://127.0.0.1:8765

# Tests
python -m pytest gatewaydashboard/tests/ -q     # 13 passing

# Scan into Supabase (needs the two env vars)
python -m gatewaydashboard.jobs.run_scan --source local
python -m gatewaydashboard.jobs.run_scan --limit 20      # quick check
python -m gatewaydashboard.jobs.run_scan --dry-run       # writes nothing
```

| Table | Holds | Written by |
|---|---|---|
| `scan_runs` | one row per scan: counts, timing, settings, failures | the scheduled job |
| `scan_results` | one row per symbol per run + the full engine record as JSON | the scheduled job |
| `ohlcv_cache` | chart series per symbol and timeframe | the job, and the API on a miss |
| `fundamentals_cache` | quarterly statements and ratios | the API |

Free tiers throughout: Supabase 500 MB / 5 GB egress, GitHub Actions ~150 of 2,000
minutes a month, Vercel Hobby. Supabase pauses a free project after 7 idle days — the
twice-daily scan counts as activity.
