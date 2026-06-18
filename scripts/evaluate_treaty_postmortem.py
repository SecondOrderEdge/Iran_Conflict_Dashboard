"""
evaluate_treaty_postmortem.py — Terminal-outcome verification of the ICEI.

The Iran-Israel treaty (effective 2026-06-18) gives the dashboard something it
never had while running live: a KNOWN terminal outcome. The conflict resolved
into de-escalation/peace — no short war, no extended war, no long proxy war, no
Strait of Hormuz or Bab-el-Mandeb closure. This script grades every historical
ICEI snapshot against that realized ground truth.

This is distinct from the notebook's walk-forward backtest, which scores the
*market signal layer* against OSINT operation-days (a process check). Here we
score the *published probabilistic forecasts* against what actually happened.

What it computes
----------------
  1. Tail / scenario verification — Brier score, log-loss and false-alarm
     discipline for every forecast whose event did NOT occur by the treaty
     (escalation regime, the three war-horizon buckets, Hormuz/BAM closure).
  2. Calibration — reliability of p_escalation across probability bins, given
     escalation never materialised.
  3. Skill vs. baselines — Brier Skill Score against an uninformed 0.5 forecast
     and against persistence.
  4. Timeliness / lead-time — when the index first (and durably) leaned
     de-escalation relative to the treaty date.
  5. Decision summary — distribution of portfolio_regime calls, incl. the
     "Elevated Risk" false alarms against a peace outcome.

Outputs (written to OUTPUT_DIR, default ./postmortem/)
  - treaty_postmortem_scorecard.csv  — one row per scored forecast series
  - icei_trajectory.png              — ICEI + CI band + regime, treaty marker
  - regime_probabilities.png         — p_esc / p_stab / p_deesc over time
  - scenario_tail_probs.png          — the events that never happened
  - calibration_pescalation.png      — reliability bars for p_escalation
  - treaty_postmortem_summary.md     — plain-English findings

Usage
    python scripts/evaluate_treaty_postmortem.py
    HISTORY_CSV=latest/escalation_index_history.csv TREATY_DATE=2026-06-18 \
        OUTPUT_DIR=postmortem python scripts/evaluate_treaty_postmortem.py
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Config ──────────────────────────────────────────────────────────────────
HISTORY_CSV = Path(os.environ.get("HISTORY_CSV", "latest/escalation_index_history.csv"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "postmortem"))
TREATY_DATE = pd.Timestamp(os.environ.get("TREATY_DATE", "2026-06-18"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Ground truth ────────────────────────────────────────────────────────────
# The treaty is a terminal de-escalation event. None of the adverse scenarios
# materialised, so each of these forecast series has a realised outcome of 0
# (the event never happened) over the entire history. Verification therefore
# reduces to: were these probabilities appropriately LOW, and did the index
# turn toward de-escalation in good time?
#
# Each entry: column -> human label. All realised y = 0.
NON_EVENTS = {
    "p_escalation": "Escalation regime",
    "p_short_war_2_4w": "Short war (2-4w)",
    "p_extended_1_3m": "Extended war (1-3m)",
    "p_long_proxy_6m": "Long proxy war (6m)",
    "hormuz_closure_prob": "Hormuz closure",
    "bam_closure_prob": "Bab-el-Mandeb closure",
}
# Columns stored as 0-100 percentages rather than 0-1 probabilities.
PERCENT_COLS = {"hormuz_closure_prob", "bam_closure_prob"}


def load_history(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    # Some days carry two snapshots; keep the last (most-informed) per day for
    # daily trajectory / lead-time work, but keep every row for scoring.
    return df


def as_prob(series: pd.Series, col: str) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if col in PERCENT_COLS:
        s = s / 100.0
    return s.clip(0.0, 1.0)


# ── 1. Scoring helpers ──────────────────────────────────────────────────────
def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray, eps: float = 1e-12) -> float:
    p = np.clip(p, eps, 1 - eps)
    return float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p))))


def score_non_events(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, label in NON_EVENTS.items():
        if col not in df.columns:
            continue
        p = as_prob(df[col], col).dropna()
        if p.empty:
            continue
        p = p.to_numpy()
        y = np.zeros_like(p)  # event never occurred
        # Baselines for skill: uninformed 0.5, and climatology (realised base
        # rate = 0). Climatology is degenerate (perfect) when the event never
        # happens, so the meaningful skill reference is the uninformed forecast.
        bs = brier(p, y)
        bs_uninformed = brier(np.full_like(p, 0.5), y)
        bss_vs_uninformed = 1 - bs / bs_uninformed if bs_uninformed > 0 else np.nan
        rows.append(
            {
                "series": label,
                "column": col,
                "n": len(p),
                "mean_prob": round(float(p.mean()), 4),
                "max_prob": round(float(p.max()), 4),
                "pct_days_gt_0.30": round(float((p > 0.30).mean()), 4),
                "pct_days_gt_0.50": round(float((p > 0.50).mean()), 4),
                "brier": round(bs, 5),
                "log_loss": round(log_loss(p, y), 5),
                "bss_vs_uninformed": round(float(bss_vs_uninformed), 4),
            }
        )
    return pd.DataFrame(rows)


def persistence_skill(df: pd.DataFrame, col: str = "p_escalation") -> dict:
    """Brier Skill Score of the model's p_escalation vs. a persistence forecast
    (yesterday's value), both against the realised y = 0."""
    daily = df.groupby("date", as_index=False).last()
    p = as_prob(daily[col], col).to_numpy()
    y = np.zeros_like(p)
    persist = np.concatenate([[p[0]], p[:-1]])  # yesterday's forecast
    bs_model = brier(p, y)
    bs_persist = brier(persist, y)
    bss = 1 - bs_model / bs_persist if bs_persist > 0 else np.nan
    return {
        "brier_model": round(bs_model, 5),
        "brier_persistence": round(bs_persist, 5),
        "bss_vs_persistence": round(float(bss), 4),
    }


# ── 2. Lead-time / timeliness ───────────────────────────────────────────────
def lead_time(df: pd.DataFrame) -> dict:
    daily = df.groupby("date", as_index=False).last()
    out = {"treaty_date": TREATY_DATE.date().isoformat()}

    # First explicit "De-escalation" portfolio_regime call. NOTE: the README
    # warns the regime can flip on a single day's data, so the *first* flip is
    # likely noise. We also report total/late counts and the first DURABLE run
    # (>=3 consecutive days) to separate a one-off flip from real foresight.
    deesc = daily[daily["portfolio_regime"] == "De-escalation"]
    if not deesc.empty:
        first = deesc["date"].min()
        out["first_deescalation_call"] = first.date().isoformat()
        out["lead_days_regime_first_flip"] = int((TREATY_DATE - first).days)
        out["deescalation_call_count"] = int(len(deesc))
        last14 = daily[daily["date"] >= TREATY_DATE - pd.Timedelta(days=14)]
        out["deescalation_calls_last_14d"] = int(
            (last14["portfolio_regime"] == "De-escalation").sum()
        )
        is_de = (daily["portfolio_regime"] == "De-escalation").to_numpy()
        run = 0
        first_durable = None
        for i, v in enumerate(is_de):
            run = run + 1 if v else 0
            if run >= 3 and first_durable is None:
                first_durable = daily["date"].iloc[i - 2]
        out["first_durable_deescalation_run"] = (
            first_durable.date().isoformat() if first_durable is not None else "none (no 3-day run)"
        )

    # When p_deescalation first overtakes p_escalation (directional turn).
    pd_de = as_prob(daily["p_deescalation"], "p_deescalation").to_numpy()
    pd_es = as_prob(daily["p_escalation"], "p_escalation").to_numpy()
    crossed = np.where(pd_de > pd_es)[0]
    if crossed.size:
        d = daily["date"].iloc[crossed[0]]
        out["first_pdeesc_gt_pesc"] = d.date().isoformat()
        out["lead_days_prob_cross"] = int((TREATY_DATE - d).days)

    # ICEI durably below 50 (10-snapshot run).
    icei = pd.to_numeric(daily["escalation_index"], errors="coerce")
    below = (icei < 50).rolling(10).sum() == 10
    if below.any():
        d = daily["date"].iloc[below.idxmax()]
        out["icei_durably_below_50"] = d.date().isoformat()

    out["elevated_risk_false_alarm_days"] = int(
        (daily["portfolio_regime"] == "Elevated Risk").sum()
    )
    return out


# ── 3. Calibration of p_escalation ──────────────────────────────────────────
def calibration_table(df: pd.DataFrame, col: str = "p_escalation", bins=10):
    p = as_prob(df[col], col).dropna().to_numpy()
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    rows = []
    for b in range(bins):
        m = idx == b
        if not m.any():
            continue
        rows.append(
            {
                "bin": f"{edges[b]:.1f}-{edges[b+1]:.1f}",
                "n": int(m.sum()),
                "mean_forecast": round(float(p[m].mean()), 4),
                "observed_freq": 0.0,  # escalation never occurred
            }
        )
    return pd.DataFrame(rows)


# ── 4. Charts ───────────────────────────────────────────────────────────────
REGIME_COLOR = {
    "Stabilization": "#5b8c5a",
    "Elevated Risk": "#d98c00",
    "De-escalation": "#2c7fb8",
    "Escalation": "#c0392b",
}


def _treaty_marker(ax):
    ax.axvline(TREATY_DATE, color="black", ls="--", lw=1.2, alpha=0.8)
    ax.annotate(
        "Treaty\nsigned",
        xy=(TREATY_DATE, ax.get_ylim()[1]),
        xytext=(-4, -28),
        textcoords="offset points",
        ha="right",
        fontsize=8,
        color="black",
    )


def chart_trajectory(df: pd.DataFrame, path: Path):
    daily = df.groupby("date", as_index=False).last()
    fig, ax = plt.subplots(figsize=(11, 5))
    icei = pd.to_numeric(daily["escalation_index"], errors="coerce")
    ax.plot(daily["date"], icei, color="#222", lw=1.6, label="ICEI")

    lo = pd.to_numeric(daily.get("icei_ci_lo"), errors="coerce")
    hi = pd.to_numeric(daily.get("icei_ci_hi"), errors="coerce")
    if lo.notna().any():
        ax.fill_between(daily["date"], lo, hi, color="#222", alpha=0.12, label="ICEI 95% CI")

    for regime, color in REGIME_COLOR.items():
        sub = daily[daily["portfolio_regime"] == regime]
        if not sub.empty:
            ax.scatter(sub["date"], pd.to_numeric(sub["escalation_index"], errors="coerce"),
                       s=18, color=color, label=regime, zorder=3)

    ax.axhline(50, color="grey", lw=0.8, ls=":")
    ax.set_ylabel("ICEI (0-100)")
    ax.set_title("ICEI trajectory vs. realised treaty outcome")
    _treaty_marker(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.legend(fontsize=8, ncol=3, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def chart_regime_probs(df: pd.DataFrame, path: Path):
    daily = df.groupby("date", as_index=False).last()
    fig, ax = plt.subplots(figsize=(11, 5))
    for col, color, lab in [
        ("p_escalation", "#c0392b", "P(Escalation)"),
        ("p_stabilization", "#5b8c5a", "P(Stabilization)"),
        ("p_deescalation", "#2c7fb8", "P(De-escalation)"),
    ]:
        ax.plot(daily["date"], as_prob(daily[col], col), color=color, lw=1.6, label=lab)
    ax.set_ylabel("Probability")
    ax.set_ylim(0, 1)
    ax.set_title("Regime probabilities over time (realised outcome: de-escalation)")
    _treaty_marker(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.legend(fontsize=8, loc="center left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def chart_tail_probs(df: pd.DataFrame, path: Path):
    daily = df.groupby("date", as_index=False).last()
    fig, ax = plt.subplots(figsize=(11, 5))
    for col, label in NON_EVENTS.items():
        if col in {"p_escalation"} or col not in daily.columns:
            continue
        ax.plot(daily["date"], as_prob(daily[col], col), lw=1.4, label=label)
    ax.set_ylabel("Forecast probability")
    ax.set_ylim(0, 1)
    ax.set_title("Adverse-scenario probabilities — none of these occurred")
    _treaty_marker(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def chart_calibration(cal: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(cal))
    ax.bar(x - 0.2, cal["mean_forecast"], width=0.4, color="#c0392b", label="Mean forecast")
    ax.bar(x + 0.2, cal["observed_freq"], width=0.4, color="#444", label="Observed (=0)")
    ax.set_xticks(x)
    ax.set_xticklabels(cal["bin"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("P(Escalation)")
    ax.set_title("Calibration of P(Escalation)\nescalation never materialised → observed = 0")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


# ── 5. Report ───────────────────────────────────────────────────────────────
def df_to_md(df: pd.DataFrame) -> str:
    """Minimal Markdown table — avoids a hard dependency on `tabulate`."""
    cols = list(df.columns)
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in df.itertuples(index=False, name=None)
    ]
    return "\n".join([head, sep, *body])


def write_summary(scorecard, persist, lead, cal, df, path: Path):
    daily = df.groupby("date", as_index=False).last()
    start, end = daily["date"].min().date(), daily["date"].max().date()
    lines = []
    lines.append("# ICEI Treaty Post-Mortem")
    lines.append("")
    lines.append(f"- **Treaty effective:** {TREATY_DATE.date()}")
    lines.append(f"- **History scored:** {start} → {end} "
                 f"({len(df)} snapshots, {len(daily)} days)")
    lines.append(f"- **Realised terminal outcome:** de-escalation / peace — "
                 "no war scenario and no strait closure occurred.")
    lines.append("")
    lines.append("## Scenario & tail-risk verification")
    lines.append("Every series below had a realised outcome of 0. "
                 "Lower Brier / log-loss = better; positive BSS = beat an "
                 "uninformed 50% forecast.")
    lines.append("")
    lines.append(df_to_md(scorecard))
    lines.append("")
    lines.append("## Skill of P(Escalation) vs. persistence")
    lines.append(f"- Brier (model): {persist['brier_model']}")
    lines.append(f"- Brier (persistence): {persist['brier_persistence']}")
    lines.append(f"- **BSS vs. persistence: {persist['bss_vs_persistence']}**")
    lines.append("")
    lines.append("## Timeliness / lead-time")
    for k, v in lead.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Calibration of P(Escalation)")
    lines.append(df_to_md(cal))
    lines.append("")
    lines.append("_Generated by scripts/evaluate_treaty_postmortem.py_")
    path.write_text("\n".join(lines))


def main():
    df = load_history(HISTORY_CSV)

    scorecard = score_non_events(df)
    persist = persistence_skill(df)
    lead = lead_time(df)
    cal = calibration_table(df)

    scorecard.to_csv(OUTPUT_DIR / "treaty_postmortem_scorecard.csv", index=False)

    chart_trajectory(df, OUTPUT_DIR / "icei_trajectory.png")
    chart_regime_probs(df, OUTPUT_DIR / "regime_probabilities.png")
    chart_tail_probs(df, OUTPUT_DIR / "scenario_tail_probs.png")
    chart_calibration(cal, OUTPUT_DIR / "calibration_pescalation.png")

    write_summary(scorecard, persist, lead, cal, df,
                  OUTPUT_DIR / "treaty_postmortem_summary.md")

    print(f"Post-mortem written to {OUTPUT_DIR}/")
    print("\nScorecard:")
    print(scorecard.to_string(index=False))
    print("\nPersistence skill:", persist)
    print("Lead-time:", lead)


if __name__ == "__main__":
    main()
