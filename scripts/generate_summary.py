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

# ── Read CSVs ──────────────────────────────────────────────────────────────

def read_csv_first_row(path):
    try:
        with open(path) as f:
            rows = list(csv.DictReader(f))
        return rows[0] if rows else {}
    except FileNotFoundError:
        return {}

def read_csv_all_rows(path):
    try:
        with open(path) as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []

latest   = read_csv_first_row(OUTPUT_DIR / "conflict_dashboard_latest.csv")
avail    = read_csv_all_rows(OUTPUT_DIR / "data_availability_summary.csv")
icei_hist = read_csv_all_rows(OUTPUT_DIR / "escalation_index_history.csv")

# ── Build context for Claude ───────────────────────────────────────────────

def safe(d, k, default="N/A"):
    return d.get(k, default) or default

def fmt_pct(val):
    try:
        return f"{float(val)*100:.1f}%"
    except (ValueError, TypeError):
        return str(val)

def fmt_f(val, decimals=2):
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)

regime        = safe(latest, "portfolio_regime")
esc_score     = fmt_f(safe(latest, "escalation_score"))
p_esc         = fmt_pct(safe(latest, "p_escalation"))
p_stab        = fmt_pct(safe(latest, "p_stabilization"))
p_deesc       = fmt_pct(safe(latest, "p_deescalation"))
icei          = fmt_f(safe(latest, "icei"), 1)
icei_delta    = fmt_f(safe(latest, "icei_delta"), 1)
p_short       = fmt_pct(safe(latest, "p_short_war_2_4w"))
p_extended    = fmt_pct(safe(latest, "p_extended_1_3m"))
p_long        = fmt_pct(safe(latest, "p_long_proxy_6m"))
signal_cov    = fmt_pct(safe(latest, "signal_coverage"))

# ICEI 7-day trend from history
icei_7d_ago = "N/A"
if len(icei_hist) >= 7:
    icei_7d_ago = fmt_f(icei_hist[-7].get("icei", "N/A"), 1)

# Data availability
avail_summary = ", ".join(
    f"{r.get('layer','?')}: {r.get('status','?')}"
    for r in avail
) or "N/A"

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

IRAN CONFLICT ESCALATION INDEX (ICEI)
======================================
Composite:            {icei} / 100  (0–30 low pressure | 30–50 below-neutral | 50–70 mixed | 70+ elevated)
Change vs prev run:   {icei_delta}
7 days ago:           {icei_7d_ago}

DURATION SCENARIOS
==================
P(Short war 2–4w):    {p_short}
P(Extended 1–3m):     {p_extended}
P(Long proxy 6m+):    {p_long}

DATA AVAILABILITY
=================
{avail_summary}
Signal Coverage:      {signal_cov}
""".strip()

prompt = f"""You are a geopolitical risk analyst writing a concise daily briefing for a portfolio management team.

Below is the quantitative output from the Iran Conflict Escalation Dashboard — a systematic model that combines market signals, GDELT news analytics, and OSINT-verified conflict events.

{context}

Write a 3–4 paragraph plain-English briefing suitable for an email to investors and risk managers. Structure it as:

1. **Headline / current assessment** — one sentence summarising the regime and ICEI reading.
2. **What the signals are saying** — briefly interpret the escalation score, probability split, and any notable changes (regime flip, ICEI threshold crossing). Do not just restate the numbers — explain what they mean in plain English.
3. **Duration outlook** — what the conflict duration probabilities suggest about the most likely scenario if escalation does occur.
4. **Positioning note** — one short paragraph on what the current regime implies for portfolio positioning, based on the regime guidance for {regime}.

Tone: professional, direct, neutral. Avoid hyperbole. Flag genuine uncertainty where appropriate. Do not make specific buy/sell recommendations for individual securities. Do not present the model output as definitive — acknowledge it is a quantitative signal, not a forecast.

Keep the total length to 250–350 words.
"""

# ── Call Claude ────────────────────────────────────────────────────────────

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set")
    sys.exit(1)

client = anthropic.Anthropic(api_key=api_key)

print("Calling Claude for summary...")
message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=600,
    messages=[{"role": "user", "content": prompt}]
)
summary_md = message.content[0].text
print("Summary generated.")
print("---")
print(summary_md)
print("---")

# ── Build HTML email body ──────────────────────────────────────────────────

def md_to_simple_html(text):
    """Minimal markdown → HTML: bold, paragraphs. No external deps."""
    import re
    # Bold: **text** → <strong>text</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Paragraphs
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
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{icei} / 100 ({icei_delta:+} vs prev)</td></tr>
  <tr><td style="padding:5px 10px;border:1px solid #E5E7EB;">P(Escalation)</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{p_esc}</td></tr>
  <tr style="background:#F9FAFB;"><td style="padding:5px 10px;border:1px solid #E5E7EB;">P(Stabilization)</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{p_stab}</td></tr>
  <tr><td style="padding:5px 10px;border:1px solid #E5E7EB;">Escalation Score</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{esc_score}</td></tr>
  <tr style="background:#F9FAFB;"><td style="padding:5px 10px;border:1px solid #E5E7EB;">Signal Coverage</td>
      <td style="padding:5px 10px;border:1px solid #E5E7EB;text-align:right;">{signal_cov}</td></tr>
</table>"""

run_url = os.environ.get("RUN_URL", "#")
repo_url = os.environ.get("REPO_URL", "#")

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

<p style="font-size:11px;color:#9CA3AF;margin-top:24px;border-top:1px solid #E5E7EB;padding-top:12px;">
  <a href="{run_url}" style="color:#4F8BBF;">Download full PDF report and charts</a> ·
  <a href="{repo_url}" style="color:#4F8BBF;">Repository</a><br><br>
  This briefing is generated by a quantitative model for informational purposes only.
  It does not constitute investment advice. See the repository disclaimer for full terms.
</p>

</body>
</html>"""

out_path = OUTPUT_DIR / "email_summary.html"
out_path.write_text(html_body, encoding="utf-8")
print(f"HTML summary written to {out_path}")

# Also write plain-text version for non-HTML clients
plain_path = OUTPUT_DIR / "email_summary.txt"
plain_path.write_text(
    f"Iran Conflict Escalation Dashboard — {TODAY}\n"
    f"{'='*50}\n\n"
    + (f"⚠️ {regime_context}\n" if regime_context else "")
    + summary_md + "\n\n"
    + f"Regime: {regime} | ICEI: {icei} | P(Esc): {p_esc} | Score: {esc_score}\n\n"
    + f"Full report: {run_url}\n\n"
    + "This briefing is generated by a quantitative model for informational purposes only.\n"
    + "It does not constitute investment advice.\n",
    encoding="utf-8"
)
print(f"Plain text summary written to {plain_path}")
