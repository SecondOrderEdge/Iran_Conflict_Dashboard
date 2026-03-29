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
- [Scheduled Execution (GitHub Actions)](#scheduled-execution-github-actions)
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
- [Understanding the Output](#understanding-the-output)
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
- **35-signal composite model** — Weighted, z-scored, and normalized across market, news, event, and physical-market dimensions. Explicitly covers the tripartite Iran-Israel-US conflict with dedicated signals for US strikes, American casualties, Israeli airstrikes, Hezbollah operations, CENTCOM force posture, Israeli Shekel, crude oil volatility, and Wikipedia edit velocity.
- **Physical Hormuz signals** — Tanker-equity basket (FRO / STNG / DHT) and Brent-WTI spread added as forward-looking physical market proxies for Strait of Hormuz stress, supplementing GDELT tone signals.
- **Sub-sector regime guidance** — Regime recommendations broken to sub-sector level (upstream E&P, midstream, refining, defense primes, defense services) rather than generic ETF direction.
- **OSINT lead/lag validation** — Cross-correlation of OSINT operation days vs. market escalation score at lags −10 to +10 days. Result is typically near-coincident (lag=0 ± a few days); supports use as a real-time monitoring framework rather than a standalone timing signal.
- **Iran Conflict Escalation Index (ICEI)** — A 0–100 index mapped from the raw escalation score, with bootstrap confidence intervals from the last 30 trading days. Interpretive range guide in the PDF: 0–30 low pressure, 30–50 below-neutral, 50–70 mixed/stabilization, 70+ elevated escalation.
- **Walk-forward out-of-sample backtest** — A rolling evaluation where the model is tested on held-out 1-month windows it never trained on, giving a true out-of-sample AUC separate from the in-sample weight-optimization AUC. Both AUCs are reported in the validation metrics table.
- **Backtest validation** — ROC-AUC computed on the full market signal layer vs. OSINT-verified operation days (non-circular).
- **Signal Coverage** — Tracks the fraction of core signal families currently returning live data; displayed in the dashboard output as "Signal Coverage" (data availability, not forecast certainty).
- **Regime-change alerting** — The GitHub Actions daily run detects when the regime flips (e.g. Stabilization → Escalation) or when ICEI crosses key thresholds (30 / 70), and posts an alert comment to a pinned GitHub issue. Subscribe to the issue to receive email notifications.
- **Data availability dashboard** — Real-time layer status (Live / Partial / Down) for market, news, and event data sources.
- **Crypto risk-off signal** — Bitcoin price action added as an additional cross-asset risk indicator.
- **Softmax probability outputs** — Smooth probability distributions rather than hard threshold triggers.
- **Automated PDF report** — ReportLab-generated multi-page report with charts, probability tables, sub-sector guidance, regime change triggers, and ICEI interpretive range guide.
- **Regime Change Triggers** — The PDF includes a model-native table of conditions that would argue for a regime reassessment (e.g. sustained ICEI above 70, P(Escalation) exceeding P(Stabilization) for consecutive runs). Thresholds are directional guides, not calibrated confidence bounds.
- **CSV exports** — Full historical timeseries, latest-day snapshot, ICEI history, and data availability summary for downstream analysis.
- **Interactive charts** — Plotly-based visualizations for exploration in Colab/Jupyter.
- **Google Drive persistence** — All outputs (PDF, CSVs, charts) are written to a `IranDashboard/` folder in your Google Drive so they survive Colab runtime disconnects. Uses the same Google auth as BigQuery — no extra credentials required. Controlled by `USE_DRIVE` in Section 2b.
- **Colab-native** — Designed to run top-to-bottom in Google Colab with no local setup required.
- **Exponential backoff** — Robust HTTP retry logic for GDELT queries in shared runtime environments.

---

## Scheduled Execution (GitHub Actions)

A `.github/workflows/daily_run.yml` workflow runs the dashboard automatically **twice daily — 08:00 and 15:30 CST (14:00 and 21:30 UTC) — every day** and saves outputs as downloadable GitHub Actions artifacts (retained for 30 days). It can also be triggered manually from the **Actions** tab at any time.

To change the schedule, edit the `cron:` lines near the top of the workflow file. Times are in UTC; CST = UTC−6, CDT (summer) = UTC−5.

### What it does

- Executes the notebook headlessly via [papermill](https://papermill.readthedocs.io/)
- Falls back to GDELT REST API + RSS if no BigQuery credentials are configured
- Uploads the PDF report, CSVs, and charts as a run artifact
- Commits a lightweight `latest/` snapshot (latest-day CSV + chart) back to the repo

### Are my secrets safe in a public repo?

**Yes.** Your API keys, email password, and GCP credentials are stored in GitHub's encrypted secrets vault — they are never written to any file in the repository. The workflow YAML only references them by name (e.g. `${{ secrets.ANTHROPIC_API_KEY }}`); GitHub substitutes the real value at runtime and automatically masks it in all log output. Even if someone forks your public repo, they get the code but not your secrets. As long as you never paste a real key directly into a `.yml` file or notebook cell, nothing sensitive is exposed.

### Setup (5 minutes)

1. **Fork this repository** to your own GitHub account (click **Fork** in the top-right corner of the repo page). This gives you your own copy where you can configure secrets and the workflow will run under your account.
2. Go to your fork → **Settings → Secrets and variables → Actions → New repository secret**
3. Add the following secrets:

**Required for email digest:**

| Secret | Value | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Claude generates the plain-English briefing |
| `MAIL_USERNAME` | `you@gmail.com` | Sender address (Gmail recommended) |
| `MAIL_PASSWORD` | 16-char app password | Gmail: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2FA) |
| `MAIL_TO` | `you@gmail.com,colleague@firm.com` | Comma-separated distribution list — everyone here gets every daily email |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server (default: Gmail) |
| `MAIL_PORT` | `465` | SMTP port (default: 465 SSL) |

**Optional — for BigQuery GDELT (higher signal quality):**

| Secret | Value | Purpose |
|---|---|---|
| `GCP_SERVICE_ACCOUNT_KEY` | JSON contents of a GCP service account key | Enables BigQuery GDELT |
| `GCP_PROJECT_ID` | Your GCP project ID | Required alongside the key above |

> **Creating a service account key:** In the GCP Console, go to **IAM & Admin → Service Accounts → Create Service Account**, grant it the `BigQuery Job User` and `BigQuery Data Viewer` roles on the `gdelt-bq` project, then create a JSON key. Paste the full JSON as the `GCP_SERVICE_ACCOUNT_KEY` secret.

4. Push any change to `main` (or trigger manually from the Actions tab) — the workflow will run, generate a Claude summary, and email the distribution list.

**What the daily email contains:**
- A 250–350 word plain-English analyst briefing written by Claude, interpreting the regime, ICEI reading, probability split, and positioning implications
- A key metrics table (Regime, ICEI, P(Escalation), Escalation Score, Signal Coverage)
- Subject line is prefixed `⚠️ ALERT —` on regime-change days
- A link to the full PDF report and chart artifacts in GitHub Actions

**Distribution list management:** Edit the `MAIL_TO` secret to add or remove addresses. No code changes needed — just comma-separate the addresses.

### Running locally with papermill

```bash
pip install papermill ipykernel
python -m ipykernel install --user --name python3

# Without BigQuery (REST API fallback):
papermill conflict_escalation_dashboard_ml_pdf_v5.ipynb output.ipynb \
  -p USE_DRIVE False -p OUTPUT_DIR outputs/ \
  -p ENABLE_BIGQUERY False

# With BigQuery (service account via env var):
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
papermill conflict_escalation_dashboard_ml_pdf_v5.ipynb output.ipynb \
  -p USE_DRIVE False -p OUTPUT_DIR outputs/ \
  -p ENABLE_BIGQUERY True -p GCP_PROJECT_ID your-project-id
```

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

4. **First run:** Two Google sign-in popups will appear — one for Google Drive (Section 2b) and one for BigQuery (Section 5). Click through both with the same Google account. After that, outputs are saved automatically to **My Drive → IranDashboard/**.

> **Tip:** Because outputs persist to Google Drive, you do not need to download files immediately. They will be waiting for you in your Drive after any runtime disconnect.

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
| `USE_DRIVE` | `True` | Persist all outputs to Google Drive (survives Colab disconnects). Set `False` to write to the local Colab filesystem instead. |
| `DRIVE_FOLDER` | `IranDashboard` | Folder name inside **My Drive** where all outputs are saved. Created automatically on first run. |
| `LOOKBACK_DAYS` | `90` | Days of market history to display |
| `WARMUP_DAYS` | `120` | Pre-calculation buffer for rolling indicators. Set to 120 to support 120-day level signals. |
| `NEWS_LOOKBACK_DAYS` | `30` | Days of GDELT news history |
| `N_BOOTSTRAP` | `500` | Bootstrap resamples for ICEI confidence intervals |
| `VALIDATION_START` | `2024-01-01` | Start date for backtest / weight-optimization window |
| `ENABLE_GDELT` | `True` | Enable/disable GDELT v2 REST API (used only if BigQuery is off or fails) |
| `ENABLE_BIGQUERY` | `True` | Use BigQuery for GDELT instead of the rate-limited REST API (recommended) |
| `GCP_PROJECT_ID` | `""` | **Your own** Google Cloud project ID (required when `ENABLE_BIGQUERY = True`). Each user must supply their own — see GDELT setup below. |
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

The dashboard supports two GDELT access modes. **Each user must choose one — there are no shared credentials.**

---

#### Option A — BigQuery (recommended)

BigQuery gives direct SQL access to the full GDELT dataset with no rate limits. **Every user needs their own free Google Cloud project.** The repository owner's project cannot be shared — each person brings their own.

> **Why your own project?** The GDELT dataset is fully public. You are not paying to access the data — you are only paying for the compute to run the query. That cost is effectively zero for this notebook (well within Google's 1 TB/month free tier). There is no way to share this across users without exposing billing credentials, so each user sets up their own in ~10 minutes.

**One-time setup per user:**

1. Go to [console.cloud.google.com](https://console.cloud.google.com/) and sign in with any Google account
2. Click the project dropdown → **New Project** → name it anything (e.g. `gdelt-dashboard`) → **Create**
3. Go to **APIs & Services → Enable APIs & Services** → search `BigQuery API` → **Enable**
4. In Section 3 of the notebook, set:
   ```python
   ENABLE_BIGQUERY = True
   GCP_PROJECT_ID  = "your-project-id"   # ← replace with YOUR project ID, not the repo owner's
   ```
5. Run the notebook — a Google sign-in popup appears in Colab on the first run. Click through once and you're done.

> **Important:** `GCP_PROJECT_ID` must be **your own project ID**. Using someone else's project ID will fail with a permissions error. Your project ID is visible in the GCP Console header after you create it.

---

#### Option B — REST API + RSS fallback (no credentials required)

If you do not want to set up a GCP project, set `ENABLE_BIGQUERY = False` in Section 3. The notebook will query the free GDELT v2 REST API instead. This API is rate-limited and shared public infrastructure — it will frequently return empty responses during busy periods, falling back automatically to RSS-derived signals. Signal quality will be lower and less reliable than Option A.

```python
ENABLE_BIGQUERY = False   # no GCP account needed
ENABLE_GDELT    = True    # use REST API with RSS fallback
```

### OSINT Database

The OSINT layer pulls a public SQLite database of OSINT-verified Iran-Israel operations from GitHub (`OSINT_DB_URL` in Section 3). No credentials required. Set `ENABLE_OSINT = False` to skip this layer.

---

## How It Works

### Data Sources

```
┌──────────────┬──────────────────────────────────┬─────────────┬──────────────┐
│ Yahoo Finance│ News (priority order)             │ OSINT DB    │ ACLED        │
│ (yfinance)   │ 1. BigQuery GKG (recommended)    │ (GitHub)    │ (optional)   │
│              │ 2. GDELT v2 REST API (fallback)  │             │              │
│ 17 tickers   │ 3. RSS via feedparser (fallback) │ Munitions & │ Ground-truth │
│ 90-day OHLC  │                                  │ intercept   │ event counts │
└──────┬───────┴──────────────┬───────────────────┴──────┬──────┴──────┬───────┘
       │                      │                      │             │
       └──────────────────────┴──────────────────────┴─────────────┘
                              │
                     build_indicator_table()
                              │
                     build_signal_table()   ← 26 normalized signals
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

The `build_signal_table()` function converts raw indicators into **26 normalized signals**, each clipped to the range `[-1, +1]` via rolling z-scores. Signals are tagged as **causal** (drive the escalation score) or **confirming** (market-return based; shown as a corroboration layer only):

1. **Market shock signals** *(causal)* — Brent crude, natural gas, and VIX vs. a **60-day** rolling baseline; react to acute price moves
2. **Market level signals** *(causal)* — The same three commodities/VIX vs. a **120-day** rolling baseline; capture persistent elevated risk that the shorter z-score would absorb as a new normal
3. **News volume signals** *(causal)* — GDELT / RSS article count z-scores for conflict, Hormuz, proxy attacks, Iran instability, troop deployments, nuclear threats, and sanctions
4. **News tone signals** *(causal)* — GDELT / RSS sentiment scores, inverted (more negative = more escalation)
5. **Physical Hormuz signals** *(causal)* — Tanker-equity basket (FRO/STNG/DHT 5-day return) and Brent-WTI spread, both z-scored; these lead GDELT tone by 1–3 days because tanker equities trade on forward fixture expectations
6. **OSINT event signals** *(causal)* — Munitions-use count and air-defense failure rate from the OSINT database, z-scored (weight reduced to reflect sparsity — typically 15/90 active days)
7. **Relative performance signals** *(confirming)* — Energy and defense sectors vs. S&P 500; displayed separately and excluded from regime trigger to avoid circularity
8. **Crypto / credit / bond stress signals** *(confirming)* — BTC, HYG, TLT; lagging cross-asset risk-off indicators

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
| OSINT / Events | 20% |
| Negative Sentiment | 35% |
| Market / Active Conflict | 30% |

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
| **Escalation** | `p_escalation > 0.50` AND `escalation_score > 0.20` | Overweight upstream E&P (XOP) and defense primes (LMT/RTX/NOC); underweight refining (margin squeeze risk); midstream neutral; preserve existing hedges — do not add broad equity risk on headline dips; reduce fragile cyclicals; avoid aggressively extending duration |
| **De-escalation** | `p_deescalation > 0.50` AND `escalation_score < -0.20` | Reduce upstream E&P tactically; overweight refining (crack-spread normalisation); add midstream on weakness; rotate into oversold cyclicals in tranches; do not fully unwind hedges until signal confirms sustained de-escalation |
| **Stabilization** | All other conditions | Maintain neutral broad equity exposure; do not add incremental risk on headline moves. Preserve existing hedges but do not materially increase them. Favour liquidity and quality until OSINT, sentiment, and market-active signals align more clearly. Avoid concentration in pure conflict-beta names absent confirming signals. |

The sub-sector breakdown is generated per-run in the PDF report and notebook output. Key distinctions: **upstream E&P (XOP)** moves on spot crude; **midstream** is infrastructure-insulated; **refining margins compress** when crude spikes without demand recovery; **defense primes** (LMT/RTX/NOC) benefit from contract backlogs but carry a 6–18 month procurement lag.

The regime trigger uses **causal signals only** (news, OSINT, VIX, commodity levels, physical Hormuz proxies). Market-return confirming signals (XLE/SPY, ITA/SPY, BTC, TLT, HYG) are displayed separately as a corroboration layer and do not gate the classification — this prevents the model from recommending overweighting XLE on the basis of XLE outperformance.

> **Important:** Regime recommendations are systematic outputs of a quantitative model, not investment advice. Market conditions are multi-causal and no model captures the full complexity of geopolitical events.

> **On output volatility:** During periods of active or rapidly evolving conflict, day-to-day outputs can be highly volatile. z-scores shift as the rolling baseline absorbs new data, the 3-day smoothing window is intentionally short, and news signals respond to media cycles as much as ground truth. The regime classification (Escalation / Stabilization / De-escalation) can flip on a single day's data. **The 90-day trend chart and multi-day ICEI trajectory are more informative than any single day's probability reading.** Treat individual snapshots as noisy inputs to a directional view, not as precise triggers.

---

## Signal Reference

Signals are tagged **causal** (drive escalation score and regime trigger) or **confirming** (market-return based; corroboration layer only — not used to trigger regime).

**Market shock signals** (60-day rolling z-score — react to acute moves):

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `vol_shock` | 7% | causal | yfinance ^VIX | VIX price level, 60-day rolling z-score |
| `oil_shock` | 6% | causal | yfinance BZ=F | Brent crude price level, 60-day rolling z-score |
| `gas_shock` | 5% | causal | yfinance NG=F | Natural gas price level, 60-day rolling z-score |

**Market level signals** (120-day rolling z-score — capture persistent elevated risk that 60-day z-scores absorb as baseline):

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `oil_level` | 3% | causal | yfinance BZ=F | Brent crude price level vs. 120-day baseline |
| `gas_level` | 2% | causal | yfinance NG=F | Natural gas price level vs. 120-day baseline |
| `vol_level` | 1% | causal | yfinance ^VIX | VIX level vs. 120-day baseline |

**News / sentiment signals** (via BigQuery GKG → REST API → RSS fallback):

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `conflict_news` | 7% | causal | GDELT / RSS | Iran/Israel conflict article volume, z-scored |
| `proxy_news` | 7% | causal | GDELT / RSS | Proxy attack article volume, z-scored |
| `conflict_tone_neg` | 7% | causal | GDELT / RSS | Iran/Israel conflict tone, **inverted** |
| `ceasefire_signal` | 7% | causal | GDELT / RSS | Ceasefire/negotiation volume, **inverted** |
| `hormuz_news` | 6% | causal | GDELT / RSS | Strait of Hormuz disruption article volume, z-scored |
| `troop_deployment` | 3% | causal | GDELT BigQuery | Troop movement / deployment article volume, z-scored |
| `iran_instability` | 1% | causal | GDELT / RSS | Iran internal instability article volume, z-scored |
| `nuclear_volume` | 4% | causal | GDELT BigQuery | Nuclear / WMD escalation article volume, z-scored |
| `sanctions_volume` | 1% | causal | GDELT BigQuery | Economic sanctions / financial pressure article volume, z-scored |
| `hormuz_tone_neg` | 1% | causal | GDELT / RSS | Hormuz news tone, **inverted** |
| `us_strikes` | 6% | causal | GDELT BigQuery | US military strikes on Iran / IRGC / Iran-backed proxies, z-scored |
| `us_casualties` | 5% | causal | GDELT / RSS | American military casualties in the region, z-scored |
| `hezbollah_news` | 4% | causal | GDELT BigQuery | Hezbollah operations and strikes (Lebanon front), z-scored |
| `israel_strikes` | 4% | causal | GDELT BigQuery | IDF / Israeli military airstrikes on Iran, Syria, Lebanon, z-scored |
| `us_centcom` | 3% | causal | GDELT BigQuery | US CENTCOM / carrier strike group / B-2 deployment volume, z-scored |
| `wiki_edits` | 2% | causal | Wikipedia API | Daily edit velocity on Iran-Israel conflict articles — spikes hours before GDELT indexes events |

**OSINT event signals** (sparse; reduced weight to reflect data gaps):

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `osint_munitions` | 2% | causal | OSINT DB | OSINT-verified munitions/operations count, z-scored |
| `osint_intercept_fail` | 2% | causal | OSINT DB | OSINT air-defense failure rate, z-scored |
| `acled_events` | 2% | causal | ACLED | Ground-truth event count, z-scored (0 if disabled) |

**Direct conflict market signals:**

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `ils_shock` | 5% | causal | yfinance ILS=X | Israeli Shekel/USD 60-day z-score — best single-market escalation thermometer; sells off immediately on Iran-Israel tension |
| `ovx_shock` | 4% | causal | yfinance ^OVX | CBOE Crude Oil Volatility Index 60-day z-score — options market's implied fear on oil, leads spot oil moves |

**Physical Hormuz proxies:**

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `tanker_stress` | 1% | causal | yfinance FRO/STNG/DHT | Equal-weight tanker-equity basket 5-day return, z-scored; leads GDELT tone by 1–3 days |
| `brent_wti_spread` | 1% | causal | yfinance BZ=F / CL=F | Brent minus WTI spread, z-scored; positive = Middle East supply-risk premium building |

**Confirming signals** (market-return based; corroboration layer only — do not gate regime):

| Signal | Weight | Role | Source | Description |
|---|---|---|---|---|
| `crypto_risk_off` | 3% | **confirming** | yfinance BTC-USD | BTC 5-day % change, **inverted** |
| `energy_rel` | 2% | **confirming** | yfinance XLE/SPY | XLE 5-day return minus SPY |
| `defense_primes_rel` | 2% | **confirming** | yfinance LMT/RTX/NOC | Defense prime contractors (Lockheed/Raytheon/Northrop) basket vs SPY — more specific than ITA |
| `bond_stress` | 2% | **confirming** | yfinance TLT | TLT 5-day % change, **inverted** |
| `defense_rel` | 1% | **confirming** | yfinance ITA/SPY | ITA 5-day return minus SPY (broad aerospace/defense) |
| `credit_stress` | 1% | **confirming** | yfinance HYG | HYG 5-day % change, **inverted** |

Weights sum to 1.0 across all 26 signals. Causal signal weights are renormalized to 1.0 for the escalation score; confirming weights apply only to the separate confirming composite. If `ENABLE_WEIGHT_OPTIMIZATION = True`, market-component weights are replaced by logistic-regression-derived values at runtime.

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
| `ILS=X` | Israeli Shekel / USD | Direct Conflict Signal |
| `^OVX` | CBOE Crude Oil Volatility Index | Direct Conflict Signal |
| `LMT` | Lockheed Martin | Defense Primes |
| `RTX` | Raytheon Technologies | Defense Primes |
| `NOC` | Northrop Grumman | Defense Primes |

---

## Output Files

After a full run, the notebook produces the following artifacts. With `USE_DRIVE = True` (default), all files are saved to **My Drive → IranDashboard/** and persist across Colab disconnects. With `USE_DRIVE = False`, files are written to the local Colab filesystem and lost on disconnect.

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
| `osint_lead_lag_chart.png` | Cross-correlation of OSINT operation days vs. market escalation score at lags −10 to +10 days |

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

## Understanding the Output

### What the model measures — and what it doesn't

The dashboard is a **quantitative signal aggregator**, not a news reader. It detects escalation risk that has already been reflected in market prices and indexed news flow. It does not read breaking news in real time.

This distinction matters in practice: if troops are moving and casualties are being reported this morning, but markets haven't repriced yet and GDELT hasn't fully indexed the sentiment shift, the model will lag behind what you're seeing in headlines. **When your own news read and the model diverge, the news is probably right and the model is catching up.**

The value of the model runs in the other direction — it catches slow-building market pressure that isn't yet generating obvious headlines, and it removes emotional bias from the assessment by grounding it in price action, article volumes, and verified events.

### The three signal sources and their lag profiles

| Source | What it measures | Typical lag |
|---|---|---|
| **Market prices** (yfinance) | What traders are pricing in for risk | 0–1 day — fast, but markets sometimes discount the probability of full escalation even as ground conditions worsen |
| **GDELT news** | Volume and sentiment tone of published articles | 12–24 hours — GDELT indexes published articles; breaking developments take time to propagate through enough sources to move the aggregate |
| **OSINT database** | Verified Iran-Israel conflict operations | Variable — depends on when the community-maintained GitHub database is updated; can be 1–3 days behind fast-moving events |

### Why "Stabilization" doesn't mean "calm"

The regime label **Stabilization** means *the quantitative signals haven't crossed the threshold for Active Escalation* — not that the situation is fine. An ICEI of 58 (mid-range "mixed signals" band) with a 33% escalation probability is elevated. It reflects real structural tension. "Stabilization" in this model's vocabulary means "the systematic signal does not yet show a dominant directional trend toward rapid phase change" — which is compatible with serious deterioration happening on the ground.

### How to use the model and your own judgment together

- Use the **ICEI trend over multiple runs** rather than any single snapshot — the direction matters more than the absolute reading
- Use the **90-day escalation score chart** to see whether pressure has been building gradually
- If your news read shows clear escalation but the model is still in Stabilization, treat that as the model lagging, not as confirmation that things are fine
- The model is most useful for catching things you might miss — not for overriding what you can see directly

### Known limitations

- **Sparse OSINT data:** The OSINT database typically has verified events on ~15–20 out of 90 days. The Random Forest ML layer trains on this; with few positive examples, the model is conservative about calling Escalation
- **GDELT rate limits:** Without BigQuery, the REST API is shared public infrastructure that frequently returns empty responses. BigQuery (free tier) gives much more reliable signal
- **No real-time news feed:** The model is not connected to a live news API. It does not know what happened this hour
- **US-centric market hours:** Yahoo Finance data is current to the prior trading day's close; overnight developments won't appear until the next run after markets open

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
