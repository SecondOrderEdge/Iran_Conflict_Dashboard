"""
generate_summary.py — Post-run Claude API summary generator.

Reads dashboard output CSVs, calls Claude to produce a plain-English
analyst briefing, and writes outputs/email_summary.html.

Usage (called by GitHub Actions after papermill run):
    python scripts/generate_summary.py

Required env var:
    ANTHROPIC_API_KEY

Optional env vars (fall through to safe defaults):
    OUTPUT_DIR  — path to dashboard outputs (default: outputs/)
    REGIME_CHANGED, CURR_REGIME, PREV_REGIME, CURR_ICEI,
    CURR_P_ESC, CURR_SCORE, ICEI_ALERT  — set by detect-regime-change step
"""

import csv
import os
import sys
from datetime import date
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("anthropic SDK not installed — run: pip install anthropic")
    sys.exit(1)

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "outputs"))
TODAY = date.today().isoformat()

# ── CSV helpers ────────────────────────────────────────────────────────────

def read_csv_all_rows(path):
    try:
        with open(path) as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []

# ── Read primary source: escalation_index_history.csv (last row) ──────────
# This CSV is written by the notebook with flat columns matching the keys
# used below: escalation_index, escalation_score, p_escalation, etc.

history_path  = OUTPUT_DIR / "escalation_index_history.csv"
latest_path   = OUTPUT_DIR / "conflict_dashboard_latest.csv"  # existence check only
avail_path    = OUTPUT_DIR / "data_availability_summary.csv"

# Gate: if the notebook didn't complete at all, neither file will exist.
if not history_path.exists() and not latest_path.exists():
    print(f"ERROR: Neither {history_path} nor {latest_path} found — "
          "did the notebook run complete successfully?")
    print(f"Contents of {OUTPUT_DIR}: "
          f"{list(OUTPUT_DIR.iterdir()) if OUTPUT_DIR.exists() else 'directory missing'}")
    sys.exit(1)

# Prefer history (has proper column names); fall back to latest if needed.
if history_path.exists():
    icei_hist = read_csv_all_rows(history_path)
    latest = icei_hist[-1] if icei_hist else {}
else:
    print(f"WARNING: {history_path} not found — falling back to {latest_path} (limited data).")
    icei_hist = []
    # dashboard CSV is vertical: rows are metrics, single column "Latest Value"
    # Build a flat dict by pivoting on the unnamed first column.
    latest = {}
    try:
        with open(latest_path) as f:
            for row in csv.DictReader(f):
                keys = list(row.keys())
                label = row.get("", row.get(keys[0], "")).strip().lower().replace(" ", "_")
                label = label.replace("(", "").replace(")", "").replace("-", "_")
                value = row.get("Latest Value", "")
                if label:
                    latest[label] = value
    except FileNotFoundError:
        pass

# Read availability CSV — format: unnamed index col = layer name, 'Status' column
avail_rows = read_csv_all_rows(avail_path)

# ── Build context for Claude ───────────────────────────────────────────────

def safe(d, *keys, default="N/A"):
    """Try multiple key aliases; return first non-empty value."""
    for k in keys:
        v = d.get(k)
        if v not in (None, "", "nan", "NaN"):
            return v
    return default

def fmt_pct(val):
    try:
        return f"{float(val)*100:.1f}%"
    except (ValueError, TypeError):
        return str(val) if val not in (None, "") else "N/A"

def fmt_f(val, decimals=2):
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return str(val) if val not in (None, "") else "N/A"

# escalation_index_history uses "escalation_index" for ICEI value
regime    = safe(latest, "portfolio_regime")
esc_score = fmt_f(safe(latest, "escalation_score"))
p_esc     = fmt_pct(safe(latest, "p_escalation"))
p_stab    = fmt_pct(safe(latest, "p_stabilization"))
p_deesc   = fmt_pct(safe(latest, "p_deescalation"))
icei      = fmt_f(safe(latest, "escalation_index", "icei"), 1)
p_short   = fmt_pct(safe(latest, "p_short_war_2_4w"))
p_extended = fmt_pct(safe(latest, "p_extended_1_3m"))
p_long    = fmt_pct(safe(latest, "p_long_proxy_6m"))
data_completeness = fmt_pct(safe(latest, "data_completeness", "model_confidence"))
hormuz_prob = fmt_f(safe(latest, "hormuz_closure_prob"), 1)
bam_prob    = fmt_f(safe(latest, "bam_closure_prob"), 1)
expansion   = fmt_f(safe(latest, "expansion_index_val"), 3)

# Bootstrap 90% CI for ICEI
icei_ci_lo = fmt_f(safe(latest, "icei_ci_lo"), 1)
icei_ci_hi = fmt_f(safe(latest, "icei_ci_hi"), 1)
icei_ci_str = f"{icei_ci_lo}–{icei_ci_hi}" if icei_ci_lo != "N/A" else "N/A"

# ICEI delta: compute from last 2 history rows
icei_delta = "N/A"
if len(icei_hist) >= 2:
    try:
        prev = float(icei_hist[-2].get("escalation_index", ""))
        curr = float(icei_hist[-1].get("escalation_index", ""))
        d = round(curr - prev, 1)
        icei_delta = f"{'+' if d >= 0 else ''}{d}"
    except (ValueError, TypeError):
        pass

# ICEI 7-day trend from history
icei_7d_ago = "N/A"
if len(icei_hist) >= 7:
    icei_7d_ago = fmt_f(icei_hist[-7].get("escalation_index", "N/A"), 1)

# Data availability — CSV has unnamed index col (layer name) and 'Status' col
avail_summary = "N/A"
if avail_rows:
    parts = []
    for r in avail_rows:
        keys = list(r.keys())
        # Layer is in the unnamed first column (key = '')
        layer  = r.get("", r.get(keys[0], "?") if keys else "?").strip()
        status = r.get("Status", r.get("status", "?")).strip()
        if layer:
            parts.append(f"{layer}: {status}")
    avail_summary = ", ".join(parts) if parts else "N/A"

print(f"DEBUG: regime={regime} icei={icei} icei_delta={icei_delta} p_esc={p_esc} score={esc_score}")
print(f"DEBUG: avail_summary={avail_summary[:120]}")

# Regime change context from env
regime_changed = os.environ.get("REGIME_CHANGED", "false") == "true"
prev_regime    = os.environ.get("PREV_REGIME", "unknown")
icei_alert     = os.environ.get("ICEI_ALERT", "")

regime_context = ""
if regime_changed:
    regime_context = f"⚠️ REGIME CHANGE: {prev_regime} → {regime}\n"
if icei_alert:
    regime_context += f"⚠️ ICEI ALERT: {icei_alert}\n"

# ── Prompt ─────────────────────────────────────────────────────────────────

context = f"""
Date: {TODAY}
{regime_context}
CURRENT MODEL OUTPUT
====================
Portfolio Regime:     {regime}
Escalation Score:     {esc_score}  (range -1 to +1; positive = escalation pressure)
P(Escalation):        {p_esc}
P(Stabilization):     {p_stab}
P(De-escalation):     {p_deesc}
Data Completeness:    {data_completeness}  (fraction of signal weights with live data)

IRAN CONFLICT ESCALATION INDEX (ICEI)
======================================
Composite:            {icei} / 100  (0–35 low | 35–50 contained | 50–65 elevated risk | 65–80 escalation | 80+ critical)
90% Confidence Interval: {icei_ci_str}
Change vs prev run:   {icei_delta}
7 days ago:           {icei_7d_ago}

DURATION SCENARIOS
==================
P(Short war 2–4w):    {p_short}
P(Extended 1–3m):     {p_extended}
P(Long proxy 6m+):    {p_long}

CHOKEPOINT RISK
===============
Hormuz Closure Risk:  {hormuz_prob} / 100  (0=no risk | 50=elevated | 80+=critical)
Bab al-Mandeb Risk:   {bam_prob} / 100
War Expansion Index:  {expansion}  (positive = watchlist countries entering conflict)

NOTE: Hormuz scores weight oil_shock and ovx_shock most heavily (real-time market
signals). GDELT narrative signals lag 12-24 hours. If Hormuz is actively closed,
the score may initially lag behind reality until oil/options markets fully price it in.

DATA AVAILABILITY
=================
{avail_summary}
""".strip()

prompt = f"""You are a geopolitical risk analyst writing a concise daily briefing for a portfolio management team.

Below is the quantitative output from the Iran Conflict Escalation Dashboard — a systematic model that combines market signals, GDELT news analytics, and OSINT-verified conflict events.

{context}

REGIME DEFINITIONS (use these to calibrate your language — do not soften or upgrade the regime label):
- Stabilization  (ICEI 0–35):   Conflict pressure is low. Routine monitoring only.
- Elevated Risk  (ICEI 35–65):  Active conflict signals present. Hedging warranted.
                                 This regime covers situations such as ongoing strikes,
                                 chokepoint disruption, and proxy escalation — it does NOT
                                 mean the situation is calm or contained.
- Escalation     (ICEI 65–80):  Direct state-on-state military action likely or underway.
                                 Significant portfolio repositioning indicated.
- Regional War   (ICEI 80–90):  Multi-actor conflict with regional spread.
- Nuclear Threshold (ICEI 90+): Existential escalation signals.

Write a 3–4 paragraph plain-English briefing. Structure it as:

1. **Headline / current assessment** — one sentence stating the regime and ICEI. Be direct.
   If the model is reading Elevated Risk with active chokepoint disruption and ongoing
   strikes, say so plainly. Do not soften a score of 50+ into language implying calm.

2. **What the signals are saying** — interpret the escalation score and probability split
   honestly. If the dominant signals are oil market stress, ILS weakness, and strike
   volumes, name them. Explain what combination of events is driving the reading.

3. **Chokepoint risk** — if Hormuz or Bab al-Mandeb is above 40/100, describe the
   disruption plainly. Note that Hormuz market signals (oil, OVX) reprice within hours
   but GDELT narrative may lag 12–24 hours, so the score may be a floor not a ceiling.

4. **Duration outlook** — what the scenario probabilities suggest about how long elevated
   tension is likely to persist.

5. **Positioning note** — what the regime implies for portfolio exposure.

Tone: direct and factual. Match the severity of the language to the severity of the
signal readings — a model reading of 53/100 with active Hormuz disruption and ongoing
strikes is a serious situation and should be described as one. Do not add diplomatic
hedges that contradict what the numbers show. Do not make specific buy/sell
recommendations. Acknowledge data limitations (GDELT lag, no classified sources) once
in the chokepoint section — do not repeat the caveat throughout.

Keep the total length to 350–450 words.
"""

# ── Call Claude ────────────────────────────────────────────────────────────

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set")
    sys.exit(1)

client = anthropic.Anthropic(api_key=api_key)

print("Calling Claude for summary...")
try:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    summary_md = message.content[0].text
    print("Summary generated.")
except anthropic.BadRequestError as e:
    if "credit balance" in str(e).lower():
        print("WARNING: Anthropic credit balance too low — writing fallback summary. "
              "Add credits at console.anthropic.com.")
    else:
        print(f"WARNING: Anthropic API error ({e}) — writing fallback summary.")
    summary_md = (
        f"**Automated summary unavailable** (Anthropic API error — see workflow logs).\n\n"
        f"Current regime: **{regime}** | ICEI: {icei} | P(Escalation): {p_esc} | "
        f"Escalation Score: {esc_score}."
    )
except Exception as e:
    print(f"WARNING: Unexpected error calling Claude ({e}) — writing fallback summary.")
    summary_md = (
        f"**Automated summary unavailable** (see workflow logs).\n\n"
        f"Current regime: **{regime}** | ICEI: {icei} | P(Escalation): {p_esc} | "
        f"Escalation Score: {esc_score}."
    )
print("---")
print(summary_md)
print("---")

# ── Build HTML email body ──────────────────────────────────────────────────

def md_to_simple_html(text):
    """Minimal markdown → HTML: bold, paragraphs. No external deps."""
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return "\n".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paras)

alert_banner = ""
if regime_changed or icei_alert:
    alert_items = []
    if regime_changed:
        alert_items.append(f"<li>Regime change: <strong>{prev_regime} → {regime}</strong></li>")
    if icei_alert:
        alert_items.append(f"<li>{icei_alert}</li>")
    alert_banner = f"""
<div style="background:#FEF3C7;border-left:4px solid #F59E0B;padding:12px 16px;margin-bottom:16px;border-radius:4px;">
  <strong>⚠️ Alert</strong>
  <ul style="margin:4px 0 0 0;padding-left:18px;">{''.join(alert_items)}</ul>
</div>"""

metrics_table = f"""
<table style="border-collapse:collapse;width:100%;max-width:480px;margin:16px 0;font-size:13px;">
  <tr style="background:#F3F4F6;">
    <th style="text-align:left;padding:6px 10px;border:1px solid #E5E7EB;">Metric</th>
    <th style="text-align:right;padding:6px 10px;border:1px solid #E5E7EB;">Value</th>
  </tr>
  <tr><td style="padding:5px 10px;border:1px solid #E5E7EB;">Portfolio Regime</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;"><strong>{regime}</strong></td></tr>
  <tr style="background:#F9FAFB;"><td style="padding:5px 10px;border:1px solid #E5E7EB;">ICEI</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{icei} / 100 ({icei_delta} vs prev)</td></tr>
  <tr><td style="padding:5px 10px;border:1px solid #E5E7EB;">P(Escalation)</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{p_esc}</td></tr>
  <tr style="background:#F9FAFB;"><td style="padding:5px 10px;border:1px solid #E5E7EB;">P(Stabilization)</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{p_stab}</td></tr>
  <tr><td style="padding:5px 10px;border:1px solid #E5E7EB;">Escalation Score</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{esc_score}</td></tr>
  <tr style="background:#F9FAFB;"><td style="padding:5px 10px;border:1px solid #E5E7EB;">ICEI 90% CI</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{icei_ci_str}</td></tr>
  <tr><td style="padding:5px 10px;border:1px solid #E5E7EB;">Data Completeness</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{data_completeness}</td></tr>
  <tr><td style="padding:5px 10px;border:1px solid #E5E7EB;">Hormuz Closure Risk</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{hormuz_prob} / 100</td></tr>
  <tr style="background:#F9FAFB;"><td style="padding:5px 10px;border:1px solid #E5E7EB;">Bab al-Mandeb Risk</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{bam_prob} / 100</td></tr>
</table>"""

run_url  = os.environ.get("RUN_URL",  "#")
repo_url = os.environ.get("REPO_URL", "#")

# ── Inline chart helpers ───────────────────────────────────────────────────

def img_to_b64(path):
    """Return a base64 data URI for a PNG, or None if the file doesn't exist."""
    import base64
    try:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def chart_block(img_uri, caption):
    """Return an HTML <figure> block, or empty string if no image available."""
    if not img_uri:
        return ""
    return (
        f'<figure style="margin:20px 0 8px 0;">'
        f'<img src="{img_uri}" alt="{caption}" '
        f'style="width:100%;max-width:600px;border:1px solid #E5E7EB;border-radius:4px;">'
        f'<figcaption style="font-size:11px;color:#6B7280;margin-top:4px;">{caption}</figcaption>'
        f'</figure>'
    )

_icei_chart  = img_to_b64(str(OUTPUT_DIR / "escalation_index_chart.png"))
_dur_chart   = img_to_b64(str(OUTPUT_DIR / "conflict_duration_chart.png"))

icei_chart_html = chart_block(_icei_chart, f"Iran Conflict Escalation Index (ICEI) — {TODAY}")
dur_chart_html  = chart_block(_dur_chart,  "Conflict Duration Scenario Probabilities")

html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Georgia,serif;max-width:640px;margin:0 auto;padding:24px;color:#111;">

<div style="border-bottom:2px solid #163A5F;padding-bottom:8px;margin-bottom:20px;">
  <h2 style="margin:0;color:#163A5F;font-size:18px;">Iran Conflict Escalation Dashboard</h2>
  <p style="margin:4px 0 0 0;font-size:12px;color:#6B7280;">{TODAY} · automated daily briefing</p>
</div>

{alert_banner}

{md_to_simple_html(summary_md)}

{metrics_table}

{icei_chart_html}

{dur_chart_html}

<p style="font-size:11px;color:#9CA3AF;margin-top:24px;border-top:1px solid #E5E7EB;padding-top:12px;">
  <a href="{run_url}" style="color:#4F8BBF;">Download full PDF report and charts</a> ·
  <a href="{repo_url}" style="color:#4F8BBF;">Repository</a>
</p>
<div style="font-size:10px;color:#9CA3AF;border-top:1px solid #E5E7EB;padding-top:10px;margin-top:4px;line-height:1.5;">
  <strong>DISCLAIMER</strong> — This dashboard is a systematic aggregation of publicly available market data,
  GDELT news analytics, and open-source conflict event counts. It is <em>not</em> a forecast, a classified
  intelligence product, or real-time situational awareness. It cannot access ship-tracking data (AIS),
  satellite imagery, government intelligence assessments, or any non-public information source.
  GDELT news signals typically lag real-world events by 12–24 hours; market-derived signals (oil, FX,
  options volatility) are more timely but reflect trader positioning rather than ground truth.
  The Iran Conflict Escalation Index (ICEI) is a weighted composite of 40+ sentiment and market signals
  normalised to a 0–100 scale; it is not a probability of war. Regime classifications (Stabilization,
  Elevated Risk, Escalation, etc.) are threshold-based labels applied to the composite score and should
  be treated as a relative, directional indicator only. Bootstrap confidence intervals reflect input-data
  variability, not model accuracy. This output is provided for informational and research purposes only.
  It does not constitute investment advice, financial advice, or any form of recommendation to buy or sell
  any security. Past signal performance is not indicative of future results. Users should conduct their
  own due diligence and consult qualified advisers before making investment decisions.
</div>

</body>
</html>"""

out_path = OUTPUT_DIR / "email_summary.html"
out_path.write_text(html_body, encoding="utf-8")
print(f"HTML summary written to {out_path}")

plain_path = OUTPUT_DIR / "email_summary.txt"
DISCLAIMER_TEXT = (
    "DISCLAIMER\n"
    "----------\n"
    "This dashboard is a systematic aggregation of publicly available market data, GDELT news\n"
    "analytics, and open-source conflict event counts. It is NOT a forecast, a classified\n"
    "intelligence product, or real-time situational awareness. It cannot access ship-tracking\n"
    "data (AIS), satellite imagery, government intelligence assessments, or any non-public\n"
    "information source. GDELT news signals typically lag real-world events by 12-24 hours;\n"
    "market-derived signals (oil, FX, options volatility) are more timely but reflect trader\n"
    "positioning rather than ground truth.\n\n"
    "The Iran Conflict Escalation Index (ICEI) is a weighted composite of 40+ sentiment and\n"
    "market signals normalised to a 0-100 scale; it is not a probability of war. Regime\n"
    "classifications are threshold-based labels applied to the composite score and should be\n"
    "treated as a relative, directional indicator only. Bootstrap confidence intervals reflect\n"
    "input-data variability, not model accuracy.\n\n"
    "This output is provided for informational and research purposes only. It does not\n"
    "constitute investment advice, financial advice, or any form of recommendation to buy or\n"
    "sell any security. Past signal performance is not indicative of future results. Users\n"
    "should conduct their own due diligence and consult qualified advisers before making\n"
    "investment decisions.\n"
)

plain_path.write_text(
    f"Iran Conflict Escalation Dashboard — {TODAY}\n"
    f"{'='*50}\n\n"
    + (f"⚠️ {regime_context}\n" if regime_context else "")
    + summary_md + "\n\n"
    + f"Regime: {regime} | ICEI: {icei} | P(Esc): {p_esc} | Score: {esc_score}\n"
    + f"Hormuz Risk: {hormuz_prob}/100 | Bab al-Mandeb Risk: {bam_prob}/100\n\n"
    + f"Full report: {run_url}\n\n"
    + ("-"*50) + "\n"
    + DISCLAIMER_TEXT,
    encoding="utf-8"
)
print(f"Plain text summary written to {plain_path}")
