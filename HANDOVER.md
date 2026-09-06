# Project Handover Document — Aaroquant AI Trading Dashboard

This document provides complete context, architecture details, git specifications, and operational instructions for **Claude** (or any succeeding AI pair programmer / engineer) to seamlessly resume work on this repository.

---

## 1. Git Repository & Deployment Details

- **GitHub Repository**: [https://github.com/krishnacvukkala/vcp-scanner](https://github.com/krishnacvukkala/vcp-scanner)
- **Remote URL**: `https://github.com/krishnacvukkala/vcp-scanner.git`
- **Default Branch**: `main` (tracking `origin/main`)
- **Authentication**: macOS Keychain (`credential.helper=osxkeychain`) under user `krishnacvukkala`.
- **Working Tree**: Clean. All active code, documentation, and assets are pushed to `main`.
- **Large File Handling (`.gitignore`)**:
  - The local workspace contains ~3 GB of raw workshop media files (`.mkv`, `.mp3`, `vcp workshop.pdf`, and `day1_frames/`, `day2_frames/`).
  - **CRITICAL**: Never remove `.gitignore` exclusions for `*.mkv`, `*.mp3`, `*.pdf`, `*.zip`, or frame directories. Google Drive CloudStorage indexing and GitHub 100MB file limits will reject or freeze git operations if these are tracked.

---

## 2. Project Overview & Identity

- **Name**: **Aaroquant — AI Trading & Risk Management Dashboard (VCP Swing Trades)**
- **Core Methodology**: Volatility Contraction Pattern (VCP) swing trading strategy based on workshop materials (Mark Minervini / David Ryan / Stan Weinstein Stage 2 models).
- **Branding**: All references to the strategy in user-facing views are branded as **Aaroquant Swing Trades**.
- **Architecture**:
  - **Backend**: Lightweight local Flask server (`gatewaydashboard/app.py`) bound to `127.0.0.1:8765`.
  - **Frontend**: High-performance, single-page application (`gatewaydashboard/static/index.html`) using Vanilla HTML5, modern CSS3 (glassmorphism, curated dark/light palettes), and Vanilla JavaScript with Lightweight Charts and TradingView widgets.
  - **Data Feeds**: Multi-market Yahoo Finance pipeline (`yfinance`) with exchange-aware ticker resolution, disk caching, and parallel fundamental analysis.

---

## 3. Directory & File Structure

```text
.
├── gatewaydashboard/
│   ├── app.py              # Flask API server (http://127.0.0.1:8765)
│   ├── vcp_core.py         # VCP contraction math, pivot calculation, & verdict engine
│   ├── scanner.py          # Multi-market scanner & parallel fundamentals evaluation
│   ├── instruments.py      # Global instrument catalog (160+ tickers across India, US, UK, EU, JP)
│   ├── data.py             # Yahoo Finance market data loader, price cache, & ticker mapping
│   ├── fundamentals.py     # Income statements, key financial ratios, & 12h disk cache
│   ├── market_data.py      # Real-time OHLCV indicator generation & TradingView feeds
│   ├── config.py           # Parameters, risk limits, & source/user provenance
│   ├── universe.csv        # Starter universe of equities
│   ├── requirements.txt    # Python dependencies
│   └── static/
│       └── index.html      # Complete dashboard UI (all 7 views, charts, and Help Guide)
├── STRATEGY_MASTER.md      # Comprehensive strategy reference & rules derived from workshop
├── SOURCE_KNOWLEDGE_MAP.md # Mathematical definitions and rule matrices
├── SOURCE_FILE_INVENTORY.md# Source audit documentation
├── README.md               # Repository landing page and quickstart
└── HANDOVER.md             # This document
```

---

## 4. Key Systems & Recent Enhancements

### A. Global Multi-Market Support
- Supports global tickers across **India (NSE)**, **United States (NYSE/NASDAQ)**, **United Kingdom (LSE)**, **Germany (XETRA)**, **Japan (TSE)**, **Hong Kong (HKEX)**, **Australia (ASX)**, and **Canada (TSX)**.
- `instruments.find_instrument()` automatically resolves exchange suffixes (e.g. `AAPL` without `.NS`, `SAP.DE`, `SHEL.L`, `7203.T`, `RELIANCE.NS`).
- Displays numbers in local scale: **₹ Crores** for India, **$B / $M** for US, **£B** for UK, **€B** for Europe.

### B. Strategy Verdicts & Categorization
- **🟢 Valid Setup (Buy Trigger)**: Passed all technical gates (Stage 2 uptrend, contracting volume, tightening waves) and fundamental checks.
- **🟡 Watch Near Pivot**: High-quality bases within 3–5% of breakout pivot point.
- **🟣 Target Hit (Completed)**: Tracks closed winners where price reached Take Profit 1 (2R) or Take Profit 2 (3R).
- **🔴 Stop Loss Hit**: Automatically categorizes trades where price dropped below Stop Loss.
- **🔵 Base Forming**: Stocks in sideways resting/consolidation phase.

### C. "Trades For Today" Interactive Tabs & Filtering
- Contains 3 dedicated tabs:
  1. `Active Setups` (Valid Setup & Watch Near Pivot)
  2. `🔴 Stop Loss Hit` (Disciplined risk management audit)
  3. `🏆 Target Hit` (Completed winning trades)
- Search bar and Verdict filter dropdown allow real-time filtering without page reloads.

### D. High-Speed Market Scan ("Run Scan Now")
- **Parallel Fundamentals**: Evaluates 20+ candidate stocks concurrently using `concurrent.futures.ThreadPoolExecutor(max_workers=8)` in `scanner.py`.
- **Disk Caching**: Fundamentals cached to `.cache/fundamentals/*.pkl` with a 12-hour TTL.
- **Socket Timeout**: Added `timeout=12` in `yf.download()` to prevent hanging network calls.
- **Interactive UI**: Button displays live rotating spinner (`Scanning...`), disables to prevent duplicate triggers, and shows toast notifications (`toast-info`, `toast-success`).
- **Performance**: Full 164-stock global scan reduced from **5–6+ minutes** down to **~10–20 seconds**; cached scans return in **<0.5 seconds**.

### E. In-Dashboard "📚 Help & Guide" Menu
- Dedicated 7th navigation item in the sidebar (`#view-help-guide`).
- Features a 9-section plain-English guide covering:
  1. The 5-Step Workflow (`01 SCAN → 02 ANALYZE → 03 RESEARCH → 04 RISK → 05 PLAN`)
  2. Dashboard Overview & KPI Cards
  3. Trades For Today & Filter Usage
  4. Candlestick Charts & Technical Overlays (MA50, MA200, Volume, Pivot, SL, TP)
  5. Fundamental Health & Key Financials
  6. Risk Manager & Position Sizing (1% account risk, 2:1 R:R minimum)
  7. Color Code Guide (Green, Amber, Red, Blue, Purple, Gray)
  8. Full Trading Glossary (20+ terms including detailed explanation of "Base Forming")
  9. Global Markets Reference Table

---

## 5. How to Run and Verify

```bash
# 1. Navigate to gatewaydashboard
cd gatewaydashboard

# 2. Run the application
python app.py

# 3. Access in browser
# Open http://127.0.0.1:8765
```

### API Endpoints
- `GET /` — Serves `static/index.html`
- `GET /api/scan?cached=1` — Returns latest scan from memory/disk cache (instant)
- `GET /api/scan?fundamentals=1&force=1` — Forces fresh market scan and updates cache
- `GET /api/stock/<symbol>` — Full technical and fundamental scan for a single symbol
- `GET /api/market-data/ohlc?symbol=X&exchange=Y&timeframe=1D` — Historical candlestick data
- `GET /api/market-data/instruments` — Instrument list by country/exchange
- `GET /api/settings` — System parameters and provenance rules

---

## 6. Conventions & Guidelines for Future Edits

1. **Preserve Color Coding & Visual Hierarchy**:
   - Green: `#16a34a` / `#15803d` / `#22c55e` (Setups, Targets, Wins)
   - Amber: `#d97706` / `#b45309` (Watch Near Pivot)
   - Red: `#dc2626` / `#b91c1c` (Stop Loss, Losses, Danger)
   - Blue: `#2563eb` / `#1d4ed8` / `#3b82f6` (Base Forming, Entry, Accents)
   - Purple: `#7c3aed` / `#6d28d9` (Completed Targets)
2. **Never Return Raw `NaN` in JSON**:
   - `SafeJSONProvider` in `app.py` automatically scrubs `NaN` and `Infinity` into `None` / `null` to prevent browser JSON parse failures. Keep this intact.
3. **Respect Single-User Loopback**:
   - The server binds strictly to `127.0.0.1:8765`. Do not expose it to `0.0.0.0` or public tunnels without adding authentication.
4. **Git Operations**:
   - When checking status, prefer `git status -uno` or configure `git config status.showUntrackedFiles no` to prevent git from scanning large untracked video frame directories on Google Drive FileProvider.
