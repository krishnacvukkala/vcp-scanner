# Aaroquant — AI Trading & Risk Management Dashboard (VCP Swing Trades)

A modern, institutional-grade AI Trading & Risk Management platform and Volatility Contraction Pattern (VCP) scanner for global markets (India NSE/BSE, US NYSE/NASDAQ, UK LSE, Germany XETRA, Japan TSE, and more).

## 🚀 Key Features

- **Global Multi-Market Scanner**: Real-time screening across 160+ equities, ETFs, and indices with local currency and number formatting (₹ Crores, $ Billions, £ Billions, € Billions, ¥ Billions).
- **Aaroquant Swing Trading Strategy**: Automated detection of Stage 2 uptrending stocks contracting into tight bases before high-probability breakouts.
- **Verdict Classification**:
  - 🟢 **Valid Setup (Buy Trigger)**: Confirmed technical & fundamental contraction ready for execution.
  - 🟡 **Watch Near Pivot**: High-quality bases within 3–5% of breakout resistance.
  - 🟣 **Target Hit**: Automatically tracked successful profit target completions.
  - 🔴 **Stop Loss Hit**: Disciplined risk management review and audit.
  - 🔵 **Base Forming**: Early accumulation monitoring for watchlist development.
- **Trades For Today**: Filterable, searchable interactive trade tables with categorical tabs and instant drill-downs.
- **Interactive Chart & Overlays**: Lightweight Charts candlestick engine with MA50, MA200, Volume histograms, and dynamic price level lines (Pivot, Stop Loss, Target 1, Target 2).
- **Fundamental Health & Key Financials**: Real quarterly revenue, net profit, EPS growth, P/E ratios, Return on Equity (ROE), 52-week ranges, and AI syntheses.
- **Position Sizing & Risk Calculator**: Dynamic 1% account risk calculator enforcing minimum 2:1 Risk:Reward setups.
- **In-Dashboard Help & Guide**: Complete plain-English 9-section documentation and glossary built right into the platform.

## 🛠️ Architecture

```text
├── gatewaydashboard/
│   ├── app.py              # FastAPI / web application server
│   ├── vcp_core.py         # VCP pattern detection & mathematical algorithms
│   ├── scanner.py          # Multi-threaded market scanner & verdict generator
│   ├── instruments.py      # Multi-country exchange & ticker resolver
│   ├── data.py             # Yahoo Finance market data feeds & cache
│   ├── fundamentals.py     # Fundamental data extractor & financial statement parser
│   ├── market_data.py      # Real-time quotes & technical indicator engine
│   ├── config.py           # System settings, risk limits & default thresholds
│   ├── universe.csv        # Global stock universe
│   ├── requirements.txt    # Python dependencies
│   └── static/
│       └── index.html      # High-performance single-page frontend (HTML5/Vanilla CSS/JS)
├── STRATEGY_MASTER.md      # Deep-dive strategy manual & workshop knowledge base
├── SOURCE_KNOWLEDGE_MAP.md # Mathematical definitions and rule matrices
└── SOURCE_FILE_INVENTORY.md# Source audit documentation
```

## 🏁 Quickstart

### 1. Install Dependencies
```bash
cd gatewaydashboard
pip install -r requirements.txt
```

### 2. Run the Dashboard
```bash
python app.py
```
Open [http://127.0.0.1:8765](http://127.0.0.1:8765) in your web browser.
