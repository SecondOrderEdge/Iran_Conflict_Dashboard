# Iran Conflict Escalation Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SecondOrderEdge/Iran_Conflict_Dashboard/blob/main/conflict_escalation_dashboard_ml_pdf_v5.ipynb)
[![GitHub Stars](https://img.shields.io/github/stars/SecondOrderEdge/Iran_Conflict_Dashboard?style=social)](https://github.com/SecondOrderEdge/Iran_Conflict_Dashboard/stargazers)

A **quantitative geopolitical risk dashboard** that combines financial market signals, news analytics (GDELT), OSINT-verified conflict events, and optional ground-truth event data (ACLED) to produce probabilistic assessments of Iran-Israel conflict escalation — along with actionable portfolio regime guidance.

> **Disclaimer:** This tool is for informational and research purposes only. Nothing here constitutes financial, investment, legal, or professional advice. See the full [Disclaimer](#disclaimer) section before use.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start (Google Colab)](#quick-start-google-colab)
- [Local Installation](#local-installation)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
  - [Data Sources](#data-sources)
  - [Signal Construction](#signal-construction)
  - [Escalation Model](#escalation-model)
  - [Iran Conflict Escalation Index (ICEI)](#iran-conflict-escalation-index-icei)
  - [Duration Model](#duration-model)
  - [Portfolio Regimes](#portfolio-regimes)
- [Signal Reference](#signal-reference)
- [Market Tickers](#market-tickers)
- [Output Files](#output-files)
- [Example Output](#example-output)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Overview

The Iran Conflict Escalation Dashboard monitors **17 financial market instruments** (including a physical tanker-equity Hormuz basket), up to **4 GDELT news query streams** (with automatic RSS fallback), and a **GitHub-hosted OSINT attack-wave database** to generate a daily composite escalation score. A **hybrid heuristic + Random Forest ML layer** converts that score into three mutually exclusive probability states:

| State | Description |
|---|---|
| **Escalation** | Active conflict intensification likely |
| **Stabilization** | No dominant directional signal |
| **De-escalation** | Active conflict reduction or negotiation underway |

A parallel **duration model** estimates the most probable conflict timeline if escalation occurs:

| Scenario | Timeframe |
|---|---|
| Short conventional war | 2–4 weeks |
| Extended conflict | 1–3 months |
| Long proxy / hybrid conflict | 6m+ |

Both outputs are combined to generate a **portfolio regime recommendation** — a plain-language description of risk posture adjustments appropriate to each state.

---

## Key Features

- **Zero-cost by default** — Market data via `yfinance`, news data via the free GDELT API, OSINT data from a public GitHub database. No paid subscriptions required.
- **GDELT integration** — Queries conflict volume and sentiment tone across Iran/Israel, Strait of Hormuz, proxy attacks, and ceasefire/negotiation signals.
- **RSS fallback** — If GDELT rate-limits, the model automatically falls back to Google News RSS feeds via `feedparser` so news signals are never completely dark.
- **OSINT event layer** — Pulls a GitHub-hosted database of OSINT-verified Iran-Israel operations, contributing munitions-use and air-defense failure signals to the model.
- **Optional ACLED support** — Plug in ACLED credentials for ground-truth conflict event counts that feed directly into the model.
- **Hybrid ML + heuristic model** — A `scikit-learn` Random Forest classifier is trained on OSINT-verified operation days and its escalation probability is blended with the weighted heuristic score.
- **Temporal ML holdout** — The Random Forest enforces a strict 60-day train/test split and reports holdout ROC-AUC separately, so overfitting on thin event history is visible rather than hidden.
- **Empirical weight optimization** — Market signal weights are derived from logistic regression on OSINT ground truth, replacing circular heuristic weighting.
- **Causal / confirming signal taxonomy** — Signals are tagged as `causal` (drive the escalation score and regime trigger) or `confirming` (market-return based, shown as a separate corroboration layer). This breaks the XLE → overweight XLE circular reference.
- **20-signal composite model** — Weighted, z-scored, and normalized across market, crypto, news, event, and physical-market dimensions.
- **Physical Hormuz signals** — Tanker-equity basket (FRO / STNG / DHT) and Brent-WTI spread added as forward-looking physical market proxies for Strait of Hormuz stress, supplementing GDELT tone signals.
- **Sub-sector regime guidance** — Regime recommendations broken to sub-sector level (upstream E&P, midstream, refining, defense primes, defense services) rather than generic ETF direction.
- **OSINT lead/lag validation** — Cross-correlation of OSINT operation days vs. market escalation score at lags −5 to +5 days, confirming whether the event layer leads or lags the market.
- **Iran Conflict Escalation Index (ICEI)** — A 0–100 index mapped from the raw escalation score, with bootstrap confidence intervals from the last 30 trading days.
- **Backtest validation** — ROC-AUC computed on the full market signal layer vs. OSINT-verified operation days (non-circular).
- **Model confidence score** — Tracks the fraction of live signals contributing to the current run; displayed in the dashboard output.
- **Data availability dashboard** — Real-time layer status (Live / Partial / Down) for market, news, and event data sources.
- **Crypto risk-off signal** — Bitcoin price action added as an additional cross-asset risk indicator.
- **Softmax probability outputs** — Smooth probability distributions rather than hard threshold triggers.
- **Automated PDF report** — ReportLab-generated multi-page report with charts, probability tables, and portfolio guidance.
- **CSV exports** — Full historical timeseries, latest-day snapshot, ICEI history, and data availability summary for downstream analysis.
- **Interactive charts** — Plotly-based visualizations for exploration in Colab/Jupyter.
- **Colab-native** — Designed to run top-to-bottom in Google Colab with no local setup required.
- **Exponential backoff** — Robust HTTP retry logic for GDELT queries in shared runtime environments.

---

## Quick Start (Google Colab)

The fastest way to run this dashboard is directly in Google Colab — no installation required.

1. Click the badge at the top of this README:

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SecondOrderEdge/Iran_Conflict_Dashboard/blob/main/conflict_escalation_dashboard_ml_pdf_v5.ipynb)

2. In the Colab menu, select **Runtime → Run all** (or press `Ctrl+F9`).

3. The notebook will:
   - Install all required packages
   - Pull live market data from Yahoo Finance
   - Query the GDELT API for news signals (with RSS fallback)
   - Pull the OSINT attack-wave database from GitHub
   - Run the conflict escalation model
   - Generate the ICEI with bootstrap confidence intervals
   - Generate and save a PDF report + CSV exports

4. Download output files from the Colab file browser (left sidebar → Files icon).

> **ACLED (optional):** If you want ground-truth conflict event data, set your ACLED credentials before running Section 7. See [Configuration](#configuration).

---

## Local Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/SecondOrderEdge/Iran_Conflict_Dashboard.git
cd Iran_Conflict_Dashboard

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch Jupyter
jupyter notebook conflict_escalation_dashboard_ml_pdf_v5.ipynb
```

---

## Configuration

All parameters are set in **Section 3** of the notebook. Key variables:

| Variable | Default | Description |
|---|---|---|
| `LOOKBACK_DAYS` | `90` | Days of market history to display |
| `WARMUP_DAYS` | `60` | Pre-calculation buffer for rolling indicators |
| `NEWS_LOOKBACK_DAYS` | `30` | Days of GDELT news history |
| `N_BOOTSTRAP` | `500` | Bootstrap resamples for ICEI confidence intervals |
| `VALIDATION_START` | `2024-01-01` | Start date for backtest / weight-optimization window |
| `ENABLE_GDELT` | `True` | Enable/disable GDELT news signals |
| `ENABLE_OSINT` | `True` | Enable/disable GitHub-hosted OSINT event database |
| `ENABLE_WEIGHT_OPTIMIZATION` | `True` | Derive market signal weights via logistic regression on OSINT ground truth |
| `ENABLE_ACLED` | `False` | Enable/disable ACLED conflict event data |
| `ACLED_EMAIL` | `""` | ACLED API email (env: `ACLED_EMAIL`) |
| `ACLED_PASSWORD` | `""` | ACLED API password (env: `ACLED_PASSWORD`) |

### ACLED Credentials (Optional)

[ACLED](https://acleddata.com/) provides free access to conflict event data for researchers. To use it:

1. Register for a free account at [acleddata.com](https://acleddata.com/register/)
2. Set `ENABLE_ACLED = True` in Section 3
3. Provide credentials via environment variables (recommended) or directly in the config cell:

```python
# Option A: Environment variables (recommended)
import os
os.environ["ACLED_EMAIL"] = "your_email@example.com"
os.environ["ACLED_PASSWORD"] = "your_acled_api_key"

# Option B: Direct assignment (do NOT commit credentials to git)
ACLED_EMAIL = "your_email@example.com"
ACLED_PASSWORD = "your_acled_api_key"
```

> **Security note:** Never hard-code credentials in a notebook you plan to commit or share publicly.

### GDELT

GDELT is fully open and requires no credentials. The dashboard queries GDELT v2 Doc API via HTTPS. Query strings are configured in the `GDELT_QUERY_SET` dictionary in Section 3 and can be customized. If GDELT is rate-limited, the model automatically falls back to RSS-derived signals via `feedparser`.

### OSINT Database

The OSINT layer pulls a public SQLite database of OSINT-verified Iran-Israel operations from GitHub (`OSINT_DB_URL` in Section 3). No credentials required. Set `ENABLE_OSINT = False` to skip this layer.

---

## How It Works

### Data Sources

```
┌──────────────┬──────────────────────────────┬─────────────┬──────────────┐
│ Yahoo Finance│ News (GDELT v2 → RSS fallback)│ OSINT DB    │ ACLED        │
│ (yfinance)   │                              │ (GitHub)    │ (optional)   │
│              │ GDELT rate-limited?           │             │              │
│ 14 tickers   │ └─ yes → feedparser RSS      │ Munitions & │ Ground-truth │
│ 90-day OHLC  │ └─ no  → GDELT + RSS merge   │ intercept   │ event counts │
└──────┬───────┴──────────────┬───────────────┴──────┬──────┴──────┬───────┘
       │                      │                      │             │
       └──────────────────────┴──────────────────────┴─────────────┘
                              │
                     build_indicator_table()
                              │
                     build_signal_table()   ← 18 normalized signals
                              │
              ┌───────────────┴───────────────┐
              │  Heuristic weighted score     │
              │  + Random Forest ML blend     │
              │  (trained on OSINT ground     │
              │   truth, non-circular)        │
              └───────────────┬───────────────┘
                              │
                    softmax → [p_deesc, p_stab, p_esc]
                              │
              ┌───────────────┴───────────────┐
              │  ICEI (0–100 index)           │
              │  + portfolio regime           │
              │  + duration model             │
              └───────────────────────────────┘
```

### Signal Construction

The `build_signal_table()` function converts raw indicators into **20 normalized signals**, each clipped to the range `[-1, +1]` via rolling z-scores. Signals are tagged as **causal** (drive the escalation score) or **confirming** (market-return based; shown as a corroboration layer only):

1. **Market level signals** *(causal)* — Brent crude, natural gas, and VIX vs. a 60-day rolling baseline
2. **News volume signals** *(causal)* — GDELT / RSS article count z-scores
3. **News tone signals** *(causal)* — GDELT / RSS sentiment scores, inverted (more negative = more escalation)
4. **Physical Hormuz signals** *(causal)* — Tanker-equity basket (FRO/STNG/DHT 5-day return) and Brent-WTI spread, both z-scored; these lead GDELT tone by 1–3 days because tanker equities trade on forward fixture expectations
5. **OSINT event signals** *(causal)* — Munitions-use count and air-defense failure rate from the OSINT database, z-scored
6. **Relative performance signals** *(confirming)* — Energy and defense sectors vs. S&P 500; displayed separately and excluded from regime trigger to avoid circularity
7. **Crypto / credit / bond stress signals** *(confirming)* — BTC, HYG, TLT; lagging cross-asset risk-off indicators

### Escalation Model

```
signal_table (18 signals × weights)
     ↓
availability-weighted sum → 3-day rolling mean
     ↓
escalation_score  ∈  [-1, +1]
     ↓
Heuristic: softmax over anchors [-0.45, 0.0, +0.45]
     +
ML layer: Random Forest trained on OSINT-verified operation days
     ↓
blended [p_deescalation, p_stabilization, p_escalation]  (sum = 1.0)
     +
model_confidence = live_signal_weight / total_weight
```

Market signal weights are optionally derived from logistic regression on OSINT ground truth (`ENABLE_WEIGHT_OPTIMIZATION = True`). The Random Forest is trained on 8 market features (including `tanker_stress`) with a strict 60-day temporal holdout — holdout ROC-AUC is printed and included in the PDF, making overfitting on thin event history visible. If fewer than 30 training days are available, the RF is skipped entirely rather than fitting noise.

### Iran Conflict Escalation Index (ICEI)

The ICEI maps the raw escalation score to a **0–100 scale** with three component budgets:

| Component | Budget |
|---|---|
| OSINT / Events | 47.1% |
| Negative Sentiment | 23.5% |
| Market / Active Conflict | 29.4% |

A **500-sample bootstrap** (configurable via `N_BOOTSTRAP`) over the last 30 trading days produces confidence intervals around the current ICEI reading. The ICEI history is exported to `escalation_index_history.csv` and charted in `escalation_index_chart.png`.

### Duration Model

Three competing duration scenarios each receive a score from a linear combination of signals:

| Scenario | Key Drivers |
|---|---|
| Short war (2–4w) | Low proxy activity, low Hormuz stress, falling oil and VIX |
| Extended conflict (1–3m) | High escalation score, Hormuz disruption, oil shock |
| Long proxy / hybrid (6m+) | High proxy news, Iran instability, failed ceasefire signals |

Softmax is applied across the three scores to produce a probability vector.

### Portfolio Regimes

The regime is determined by the latest escalation score and escalation probability:

| Regime | Trigger | Guidance |
|---|---|---|
| **Escalation** | `p_escalation > 0.50` AND `escalation_score > 0.20` | Overweight upstream E&P (XOP) and defense primes (LMT/RTX/NOC); underweight refining (margin squeeze risk); midstream neutral; reduce fragile cyclicals; hold cash or liquid hedges |
| **De-escalation** | `p_deescalation > 0.50` AND `escalation_score < -0.20` | Reduce upstream E&P tactically; overweight refining (crack-spread normalisation); add midstream on weakness; rotate into oversold cyclicals in tranches |
| **Stabilization** | All other conditions | Stay balanced; avoid headline chasing; keep hedges lighter but intact; favor quality and liquidity |

The sub-sector breakdown is generated per-run in the PDF report and notebook output. Key distinctions: **upstream E&P (XOP)** moves on spot crude; **midstream** is infrastructure-insulated; **refining margins compress** when crude spikes without demand recovery; **defense primes** (LMT/RTX/NOC) benefit from contract backlogs but carry a 6–18 month procurement lag.

The regime trigger uses **causal signals only** (news, OSINT, VIX, commodity levels, physical Hormuz proxies). Market-return confirming signals (XLE/SPY, ITA/SPY, BTC, TLT, HYG) are displayed separately as a corroboration layer and do not gate the classification — this prevents the model from recommending overweighting XLE on the basis of XLE outperformance.

> **Important:** Regime recommendations are systematic outputs of a quantitative model, not investment advice. Market conditions are multi-causal and no model captures the full complexity of geopolitical events.

> **On output volatility:** During periods of active or rapidly evolving conflict, day-to-day outputs can be highly volatile. z-scores shift as the rolling baseline absorbs new data, the 3-day smoothing window is intentionally short, and news signals respond to media cycles as much as ground truth. The regime classification (Escalation / Stabilization / De-escalation) can flip on a single day's data. **The 90-day trend chart and multi-day ICEI trajectory are more informative than any single day's probability reading.** Treat individual snapshots as noisy inputs to a directional view, not as precise triggers.

---

## Signal Reference

Signals are tagged **causal** (drive escalation score and regime trigger) or **confirming** (market-return based; corroboration layer only — not used to trigger regime).

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `conflict_news` | 8% | causal | GDELT / RSS | Iran/Israel conflict article volume, z-scored |
| `ceasefire_signal` | 10% | causal | GDELT / RSS | Ceasefire/negotiation volume, **inverted** |
| `hormuz_news` | 8% | causal | GDELT / RSS | Strait of Hormuz disruption article volume, z-scored |
| `vol_shock` | 8% | causal | yfinance ^VIX | VIX price level, 60-day rolling z-score |
| `conflict_tone_neg` | 8% | causal | GDELT / RSS | Iran/Israel conflict tone, **inverted** |
| `proxy_news` | 8% | causal | GDELT / RSS | Proxy attack article volume, z-scored |
| `oil_shock` | 7% | causal | yfinance BZ=F | Brent crude price level, 60-day rolling z-score |
| `acled_events` | 4% | causal | ACLED | Ground-truth event count, z-scored (0 if disabled) |
| `osint_munitions` | 4% | causal | OSINT DB | OSINT-verified munitions/operations count, z-scored |
| `osint_intercept_fail` | 3% | causal | OSINT DB | OSINT air-defense failure rate, z-scored |
| `gas_shock` | 6% | causal | yfinance NG=F | Natural gas price level, 60-day rolling z-score |
| `hormuz_tone_neg` | 3% | causal | GDELT / RSS | Hormuz news tone, **inverted** (reduced from 6%; physical proxies added) |
| `tanker_stress` | 2% | causal | yfinance FRO/STNG/DHT | Equal-weight tanker-equity basket 5-day return, z-scored; leads GDELT tone by 1–3 days |
| `brent_wti_spread` | 1% | causal | yfinance BZ=F / CL=F | Brent minus WTI spread, 60-day z-score; positive = Middle East supply-risk premium building |
| `iran_instability` | 5% | causal | GDELT / RSS | Iran internal instability article volume, z-scored |
| `energy_rel` | 4% | **confirming** | yfinance XLE/SPY | XLE 5-day return minus SPY — corroboration only |
| `defense_rel` | 3% | **confirming** | yfinance ITA/SPY | ITA 5-day return minus SPY — corroboration only |
| `crypto_risk_off` | 5% | **confirming** | yfinance BTC-USD | BTC 5-day % change, **inverted** — corroboration only |
| `bond_stress` | 2% | **confirming** | yfinance TLT | TLT 5-day % change, **inverted** — corroboration only |
| `credit_stress` | 1% | **confirming** | yfinance HYG | HYG 5-day % change, **inverted** — corroboration only |

Weights sum to 1.0. Causal signal weights are renormalized to 1.0 for the escalation score; confirming weights apply only to the separate confirming composite. If `ENABLE_WEIGHT_OPTIMIZATION = True`, market-component weights are replaced by logistic-regression-derived values at runtime.

---

## Market Tickers

| Ticker | Instrument | Category |
|---|---|---|
| `BZ=F` | Brent Crude Oil Futures | Commodity |
| `CL=F` | WTI Crude Oil Futures | Commodity |
| `NG=F` | Natural Gas Futures | Commodity |
| `^VIX` | CBOE Volatility Index | Risk |
| `UUP` | Invesco DB US Dollar Bullish ETF | Currency |
| `XLE` | Energy Select Sector SPDR ETF | Equity |
| `XLI` | Industrial Select Sector SPDR ETF | Equity |
| `ITA` | iShares U.S. Aerospace & Defense ETF | Equity |
| `GLD` | SPDR Gold Shares ETF | Commodity |
| `TLT` | iShares 20+ Year Treasury Bond ETF | Fixed Income |
| `HYG` | iShares iBoxx High Yield Corporate Bond ETF | Fixed Income |
| `SPY` | SPDR S&P 500 ETF Trust | Benchmark |
| `BTC-USD` | Bitcoin | Crypto / Risk Sentiment |
| `ETH-USD` | Ethereum | Crypto / Risk Sentiment |
| `FRO` | Frontline Group — VLCC tanker operator | Physical Hormuz Proxy |
| `STNG` | Scorpio Tankers — product tanker, Hormuz-route exposed | Physical Hormuz Proxy |
| `DHT` | DHT Holdings — VLCC, Brent-route exposed | Physical Hormuz Proxy |

---

## Output Files

After a full run, the notebook produces the following artifacts in the working directory:

| File | Description |
|---|---|
| `conflict_escalation_dashboard_output.csv` | Full 90-day timeseries of all signals, probabilities, and regimes |
| `conflict_dashboard_latest.csv` | Single-row snapshot of the latest trading day |
| `escalation_index_history.csv` | ICEI (0–100) history with bootstrap confidence intervals |
| `data_availability_summary.csv` | Layer status (Live / Partial / Down) for each data source on the latest run |
| `conflict_dashboard_report.pdf` | Multi-page PDF report with sub-sector guidance, corroboration layer, all charts, tables, and narrative |
| `conflict_escalation_chart.png` | 90-day escalation score trend with 3-day moving average |
| `conflict_duration_chart.png` | Conflict duration probability curves (2–4w, 1–3m, 6m+) |
| `signal_contributions_chart.png` | Bar chart showing each signal's contribution to today's score |
| `escalation_index_chart.png` | ICEI history chart (0–100 scale with confidence bands) |
| `backtest_validation_chart.png` | Market escalation signal vs. OSINT-verified operations (ROC-AUC backtest) |
| `osint_lead_lag_chart.png` | Cross-correlation of OSINT operation days vs. market escalation score at lags −5 to +5 days |

---

## Example Output

A sample PDF report generated by the dashboard is included in this repository: [`conflict_dashboard_report (4).pdf`](./conflict_dashboard_report%20(4).pdf)

The report includes:
- Current escalation score and probability breakdown
- ICEI reading with confidence interval
- Duration scenario probabilities
- Active portfolio regime and recommended positioning
- Signal contribution bar chart
- 90-day escalation trend chart
- Full signal table with current values

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before opening a pull request.

Areas where contributions are particularly valuable:
- Additional news data source integrations
- Alternative weighting or normalization methodologies
- Backtesting framework against known escalation events
- Additional market instruments (emerging market ETFs, shipping rates, etc.)
- Scheduled / automated execution (GitHub Actions, cron)
- Unit tests for model functions

---

## Disclaimer

**THIS TOOL IS FOR INFORMATIONAL AND RESEARCH PURPOSES ONLY.**

Nothing in this repository — including the code, outputs, charts, PDF reports, or any other materials — constitutes financial advice, investment advice, trading advice, or any other professional advice of any kind.

- **Not investment advice.** The portfolio regime recommendations and asset allocation guidance produced by this model are systematic outputs of a quantitative algorithm. They do not account for your personal financial situation, risk tolerance, investment objectives, tax circumstances, or any other individual factors relevant to investment decisions.

- **No warranty of accuracy.** The model relies on third-party data sources (Yahoo Finance, GDELT, ACLED, public OSINT databases) that may be delayed, incomplete, or incorrect. The model itself is a simplification of complex geopolitical and financial dynamics and will frequently be wrong.

- **Past signals do not predict future outcomes.** Geopolitical events are inherently unpredictable. No model can reliably forecast conflict escalation or financial market reactions to geopolitical events.

- **Outputs are point-in-time and volatile.** During periods of active or rapidly evolving conflict, day-to-day model outputs — including regime classifications and probability readings — can shift substantially on a single day's data. Always interpret outputs in the context of multi-day trends rather than individual snapshots.

- **Not a substitute for professional advice.** Before making any investment decision, consult a qualified financial advisor, legal counsel, or other appropriate professional.

- **No liability.** The author(s) of this repository accept no liability for any losses, damages, or adverse outcomes arising from the use of this software or any information contained herein.

By using this software, you acknowledge that you have read and understood this disclaimer and agree that the author(s) bear no responsibility for any decisions made based on this tool's outputs.

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

*Built with [yfinance](https://github.com/ranaroussi/yfinance), [GDELT](https://www.gdeltproject.org/), [scikit-learn](https://scikit-learn.org/), [feedparser](https://feedparser.readthedocs.io/), [Plotly](https://plotly.com/), [ReportLab](https://www.reportlab.com/), and [SciPy](https://scipy.org/).*
