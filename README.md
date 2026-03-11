# Iran Conflict Escalation Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SecondOrderEdge/Iran_Conflict_Dashboard/blob/main/Iran_Conflict_Dashboard.ipynb)
[![GitHub Stars](https://img.shields.io/github/stars/SecondOrderEdge/Iran_Conflict_Dashboard?style=social)](https://github.com/SecondOrderEdge/Iran_Conflict_Dashboard/stargazers)

A **quantitative geopolitical risk dashboard** that combines financial market signals, news analytics (GDELT), and optional ground-truth conflict event data (ACLED) to produce probabilistic assessments of Iran-Israel conflict escalation — along with actionable portfolio regime guidance.

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

The Iran Conflict Escalation Dashboard monitors **12 financial market instruments** and up to **4 GDELT news query streams** to generate a daily composite escalation score. That score is converted via softmax into three mutually exclusive probability states:

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
| Long proxy / hybrid conflict | 6–24 months |

Both outputs are combined to generate a **portfolio regime recommendation** — a plain-language description of risk posture adjustments appropriate to each state.

---

## Key Features

- **Zero-cost by default** — Market data via `yfinance`, news data via the free GDELT API. No paid subscriptions required to run the baseline model.
- **GDELT integration** — Queries conflict volume and sentiment tone across Iran/Israel, Strait of Hormuz, proxy attacks, and ceasefire/negotiation signals.
- **Optional ACLED support** — Plug in ACLED credentials for ground-truth conflict event counts that feed directly into the model.
- **15-signal composite model** — Weighted, z-scored, and normalized across market and news dimensions.
- **Softmax probability outputs** — Smooth probability distributions rather than hard threshold triggers.
- **Automated PDF report** — ReportLab-generated multi-page report with charts, probability tables, and portfolio guidance.
- **CSV exports** — Full historical timeseries and latest-day snapshot for downstream analysis.
- **Interactive charts** — Plotly-based visualizations for exploration in Colab/Jupyter.
- **Colab-native** — Designed to run top-to-bottom in Google Colab with no local setup required.
- **Exponential backoff** — Robust HTTP retry logic for GDELT queries in shared runtime environments.

---

## Quick Start (Google Colab)

The fastest way to run this dashboard is directly in Google Colab — no installation required.

1. Click the badge at the top of this README:

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SecondOrderEdge/Iran_Conflict_Dashboard/blob/main/Iran_Conflict_Dashboard.ipynb)

2. In the Colab menu, select **Runtime → Run all** (or press `Ctrl+F9`).

3. The notebook will:
   - Install all required packages
   - Pull live market data from Yahoo Finance
   - Query the GDELT API for news signals
   - Run the conflict escalation model
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
jupyter notebook Iran_Conflict_Dashboard.ipynb
```

---

## Configuration

All parameters are set in **Section 3** of the notebook. Key variables:

| Variable | Default | Description |
|---|---|---|
| `LOOKBACK_DAYS` | `90` | Days of market history to pull |
| `NEWS_LOOKBACK_DAYS` | `30` | Days of GDELT news history |
| `ENABLE_GDELT` | `True` | Enable/disable GDELT news signals |
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

GDELT is fully open and requires no credentials. The dashboard queries GDELT v2 Doc API via HTTPS. Query strings are configured in the `GDELT_QUERY_SET` dictionary in Section 3 and can be customized.

---

## How It Works

### Data Sources

```
┌─────────────────────────────────────────────┐
│               DATA INGESTION                │
├──────────────┬──────────────┬───────────────┤
│  Yahoo Finance│  GDELT v2    │  ACLED        │
│  (yfinance)  │  Doc API     │  (optional)   │
│              │              │               │
│  12 tickers  │  4 query     │  Ground-truth │
│  90-day OHLC │  streams     │  event counts │
└──────┬───────┴──────┬───────┴──────┬────────┘
       │              │              │
       └──────────────┴──────────────┘
                      │
               build_indicator_table()
```

### Signal Construction

The `build_signal_table()` function converts raw indicators into **15 normalized signals**, each clipped to the range `[-1, +1]` via rolling z-scores:

1. **Market signals** — Computed from 5-day percentage changes and level changes in market prices
2. **News volume signals** — GDELT article count z-scores (higher volume = more signal)
3. **News tone signals** — GDELT sentiment scores, inverted so that more negative tone increases escalation signal
4. **Relative performance signals** — Energy and defense sectors vs. the broad S&P 500

### Escalation Model

```
signal_table (15 signals × weights) → weighted_sum → 3-day rolling mean
     ↓
escalation_score  ∈  [-1, +1]
     ↓
softmax over anchors [-0.45, 0.0, +0.45]
     ↓
[p_deescalation, p_stabilization, p_escalation]  (sum = 1.0)
```

The softmax anchor points were chosen to produce near-equal probabilities at a neutral score of 0 and to saturate at extreme scores around ±0.45. These can be adjusted in `add_escalation_probabilities()`.

### Duration Model

Three competing duration scenarios each receive a score from a linear combination of signals:

| Scenario | Key Drivers |
|---|---|
| Short war (2–4w) | Low proxy activity, low Hormuz stress, falling oil and VIX |
| Extended conflict (1–3m) | High escalation score, Hormuz disruption, oil shock |
| Long proxy / hybrid (6–24m) | High proxy news, Iran instability, failed ceasefire signals |

Softmax is applied across the three scores to produce a probability vector.

### Portfolio Regimes

The regime is determined by the latest escalation score and escalation probability:

| Regime | Trigger | Guidance |
|---|---|---|
| **Escalation** | `p_escalation > 0.50` AND `escalation_score > 0.20` | Overweight energy/defense; reduce fragile cyclicals; hold cash or liquid hedges; avoid adding duration aggressively |
| **De-escalation** | `p_deescalation > 0.50` AND `escalation_score < -0.20` | Rotate into oversold cyclicals and broad beta in tranches; reduce tactical energy overweight; add selectively to duration-sensitive assets |
| **Stabilization** | All other conditions | Stay balanced; avoid headline chasing; keep hedges lighter but intact; favor quality and liquidity |

> **Important:** Regime recommendations are systematic outputs of a quantitative model, not investment advice. Market conditions are multi-causal and no model captures the full complexity of geopolitical events.

---

## Signal Reference

| Signal | Weight | Source | Description |
|---|---|---|---|
| `oil_shock` | 12% | yfinance BZ=F | 5-day % change in Brent crude, rolling z-score |
| `conflict_news` | 10% | GDELT | Iran/Israel conflict article volume, z-scored |
| `ceasefire_signal` | 10% | GDELT | Ceasefire/negotiation volume, **inverted** (high = bearish for escalation) |
| `hormuz_news` | 10% | GDELT | Strait of Hormuz disruption article volume, z-scored |
| `vol_shock` | 8% | yfinance ^VIX | 5-day change in VIX |
| `conflict_tone_neg` | 8% | GDELT | Iran/Israel conflict tone, **inverted** (more negative tone = more escalation) |
| `proxy_news` | 8% | GDELT | Proxy attack article volume, z-scored |
| `acled_events` | 7% | ACLED | Ground-truth conflict event count, z-scored (0 if ACLED disabled) |
| `gas_shock` | 6% | yfinance NG=F | 5-day % change in natural gas futures, z-scored |
| `hormuz_tone_neg` | 6% | GDELT | Hormuz news tone, **inverted** |
| `iran_instability` | 5% | GDELT | Iran internal instability article volume, z-scored |
| `energy_rel` | 4% | yfinance XLE/SPY | XLE 5-day return minus SPY 5-day return, z-scored |
| `defense_rel` | 3% | yfinance ITA/SPY | ITA 5-day return minus SPY 5-day return, z-scored |
| `bond_stress` | 2% | yfinance TLT | 5-day % change in TLT, **inverted** (falling bonds = stress) |
| `credit_stress` | 1% | yfinance HYG | 5-day % change in HYG, **inverted** (falling HY = stress) |

Weights sum to 1.0. All signals are normalized to `[-1, +1]` before weighting.

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

---

## Output Files

After a full run, the notebook produces the following artifacts in the working directory:

| File | Description |
|---|---|
| `conflict_escalation_dashboard_output.csv` | Full 90-day timeseries of all signals, probabilities, and regimes |
| `conflict_dashboard_latest.csv` | Single-row snapshot of the latest trading day |
| `conflict_dashboard_report.pdf` | Multi-page PDF report with charts, tables, and narrative |
| `conflict_escalation_chart.png` | Static PNG of escalation probability chart |
| `conflict_duration_chart.png` | Static PNG of duration probability chart |
| `signal_contributions_chart.png` | Bar chart showing each signal's contribution to today's score |

---

## Example Output

A sample PDF report generated by the dashboard is included in this repository: [`conflict_dashboard_report (2).pdf`](./conflict_dashboard_report%20(2).pdf)

The report includes:
- Current escalation score and probability breakdown
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

- **No warranty of accuracy.** The model relies on third-party data sources (Yahoo Finance, GDELT, ACLED) that may be delayed, incomplete, or incorrect. The model itself is a simplification of complex geopolitical and financial dynamics and will frequently be wrong.

- **Past signals do not predict future outcomes.** Geopolitical events are inherently unpredictable. No model can reliably forecast conflict escalation or financial market reactions to geopolitical events.

- **Not a substitute for professional advice.** Before making any investment decision, consult a qualified financial advisor, legal counsel, or other appropriate professional.

- **No liability.** The author(s) of this repository accept no liability for any losses, damages, or adverse outcomes arising from the use of this software or any information contained herein.

By using this software, you acknowledge that you have read and understood this disclaimer and agree that the author(s) bear no responsibility for any decisions made based on this tool's outputs.

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

*Built with [yfinance](https://github.com/ranaroussi/yfinance), [GDELT](https://www.gdeltproject.org/), [Plotly](https://plotly.com/), [ReportLab](https://www.reportlab.com/), and [SciPy](https://scipy.org/).*
