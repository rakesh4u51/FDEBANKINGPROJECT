"""
common.reporting — daily fraud summary report (Activity 5).

Implemented in Activity 5.

Design intent:
- generate_daily_summary() aggregates the finished run into the numbers the
  fraud operations desk actually reads: how many transactions ran, how many
  landed in each risk tier, which patterns fired most often, total amount at
  risk (HIGH tier), and the throughput/latency benchmark from Activity 4.
- write_report() renders that summary as a markdown file at
  reports/DAILY_FRAUD_SUMMARY.md using
  starter_files/resources/fraud_summary_report_template.md as the shape to
  follow (headings + tables), and returns the path written.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

REPORT_DIR = Path("reports")
REPORT_FILE = "DAILY_FRAUD_SUMMARY.md"

TIER_ACTIONS = {
    "HIGH": "Immediate analyst review",
    "MEDIUM": "Step-up verification / monitor",
    "LOW": "Straight-through clear",
}

PATTERN_NOTES = {
    "VELOCITY_ABUSE": "Burst of transactions on one account in a short span",
    "AMOUNT_ANOMALY": "Ticket size far above the account/category norm",
    "ODD_HOUR": "Activity outside typical customer hours (23:00-04:59)",
    "NEW_DEVICE": "Device not previously seen on the account",
    "MERCHANT_RISK": "High-risk merchant (jewellery, electronics, wallet top-up)",
    "GEO_MISMATCH": "Location inconsistent with recent activity",
}


def generate_daily_summary(prioritized: dict, benchmark: dict) -> dict:
    """Build the aggregate summary dict from prioritize_queue() output and a
    common.metrics.BenchmarkResult.as_dict().

    Return at least:
        {
          "total_transactions": int,
          "tier_counts": {"HIGH": n, "MEDIUM": n, "LOW": n},
          "top_patterns": [(pattern_code, frequency), ...] sorted desc,
          "amount_at_risk_inr": int,   # sum of amount_inr over the HIGH tier
          "benchmark": benchmark,
        }
    """
    pattern_counts: Counter = Counter()
    for t in prioritized.get("HIGH", []) + prioritized.get("MEDIUM", []):
        pattern_counts.update(t.get("matched_patterns", []))

    tier_counts = {tier: prioritized.get("counts", {}).get(tier, 0) for tier in ("HIGH", "MEDIUM", "LOW")}
    return {
        "total_transactions": sum(tier_counts.values()),
        "tier_counts": tier_counts,
        "top_patterns": pattern_counts.most_common(),
        "amount_at_risk_inr": sum(int(t.get("amount_inr", 0)) for t in prioritized.get("HIGH", [])),
        "benchmark": benchmark,
    }


def _inr(amount: float) -> str:
    """Format a rupee amount with Indian digit grouping (12,34,567)."""
    whole = str(int(round(amount)))
    if len(whole) <= 3:
        return whole
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [tail])


def write_report(summary: dict) -> Path:
    """Render `summary` as reports/DAILY_FRAUD_SUMMARY.md and return the path.

    Follow starter_files/resources/fraud_summary_report_template.md for the
    section headings (Executive summary, Risk tier breakdown, Top fraud
    patterns, Throughput & latency benchmark, Recommendations).
    """
    total = summary.get("total_transactions", 0)
    tiers = summary.get("tier_counts", {})
    patterns = summary.get("top_patterns", [])
    bench = summary.get("benchmark", {})
    at_risk = summary.get("amount_at_risk_inr", 0)
    tps = bench.get("throughput_tps", 0.0)
    target = bench.get("target_tps", 150.0)
    met = bench.get("meets_target", tps >= target)

    def pct(n: int) -> str:
        return f"{(100 * n / total):.1f}%" if total else "0.0%"

    def yes_no(ok: bool) -> str:
        return "Yes" if ok else "No"

    flagged = tiers.get("HIGH", 0) + tiers.get("MEDIUM", 0)
    lines = [
        "# Daily Fraud Summary Report",
        "",
        "**System:** Heritage National Bank real-time fraud detection engine",
        "**Scope:** common/batch · common/patterns · common/risk · common/metrics · engine/fraud_engine",
        f"**Run date:** {date.today().isoformat()}  **Prepared by:** Fraud detection engine (automated)",
        "",
        "---",
        "",
        "## 1. Executive summary",
        "",
        f"The engine processed **{total:,}** transactions and flagged **{flagged}** for action "
        f"({tiers.get('HIGH', 0)} HIGH, {tiers.get('MEDIUM', 0)} MEDIUM). "
        f"Amount at risk in the HIGH tier is **₹{_inr(at_risk)}**. "
        f"Throughput was **{tps:,.2f} tps** against a target of {target:g} tps — "
        f"target **{'met' if met else 'NOT met'}**. "
        + ("Overall posture: elevated — clear the HIGH queue first."
           if tiers.get("HIGH", 0) else "Overall posture: normal — no HIGH-tier exposure."),
        "",
        "---",
        "",
        "## 2. Risk tier breakdown",
        "",
        "| Tier | Count | % of total | Action |",
        "|------|------:|-----------:|--------|",
    ]
    for tier in ("HIGH", "MEDIUM", "LOW"):
        n = tiers.get(tier, 0)
        lines.append(f"| {tier} | {n:,} | {pct(n)} | {TIER_ACTIONS[tier]} |")
    lines += [
        f"| **Total** | **{total:,}** | **100%** | |",
        "",
        f"**Amount at risk (HIGH tier):** ₹{_inr(at_risk)}",
        "",
        "---",
        "",
        "## 3. Top fraud patterns",
        "",
        "Frequency of matched patterns across HIGH + MEDIUM transactions.",
        "",
        "| Pattern | Frequency | Notes |",
        "|---------|----------:|-------|",
    ]
    if patterns:
        for code, freq in patterns:
            lines.append(f"| {code} | {freq:,} | {PATTERN_NOTES.get(code, '')} |")
    else:
        lines.append("| _none_ | 0 | No patterns matched in HIGH/MEDIUM tiers |")
    lines += [
        "",
        "---",
        "",
        "## 4. Throughput & latency benchmark",
        "",
        "| Metric | Value | Target | Met? |",
        "|--------|------:|-------:|:----:|",
        f"| Total transactions | {bench.get('total_transactions', total):,} | 1,000 | "
        f"{yes_no(bench.get('total_transactions', total) >= 1000)} |",
        f"| Elapsed (s) | {bench.get('elapsed_seconds', 0.0):,.3f} | — | |",
        f"| Throughput (tps) | {tps:,.2f} | {target:g} | {yes_no(met)} |",
        f"| p50 latency (ms) | {bench.get('p50_latency_ms', 0.0):,.2f} | — | |",
        f"| p95 latency (ms) | {bench.get('p95_latency_ms', 0.0):,.2f} | — | |",
        f"| p99 latency (ms) | {bench.get('p99_latency_ms', 0.0):,.2f} | — | |",
        "",
        "_Source: `reports/benchmark_result.json`. Per-transaction latency is the run's "
        "wall-clock time spread evenly across transactions._",
        "",
        "---",
        "",
        "## 5. Recommendations",
        "",
    ]
    recs = []
    if tiers.get("HIGH", 0):
        recs.append(f"Work the {tiers['HIGH']} HIGH-tier transactions in score order "
                    f"(₹{_inr(at_risk)} exposure); confirm queue size fits analyst capacity.")
    if tiers.get("MEDIUM", 0):
        recs.append(f"Route the {tiers['MEDIUM']} MEDIUM-tier transactions to step-up "
                    "verification (OTP / call-back) rather than outright blocks.")
    if patterns:
        recs.append(f"Most frequent signal is {patterns[0][0]} — review the rule "
                    "threshold behind it to keep false positives in check.")
    if met:
        recs.append("Throughput met target; keep batch size/workers as-is and re-benchmark at peak volume.")
    else:
        recs.append("Throughput below target — tune DEFAULT_BATCH_SIZE / DEFAULT_MAX_WORKERS "
                    "in engine/fraud_engine.py and watch for provider rate limits.")
    recs.append("Add account-level history (velocity, geo) so VELOCITY_ABUSE and GEO_MISMATCH "
                "can be evidenced, not just inferred.")
    lines += [f"{i}. {r}" for i, r in enumerate(recs, 1)]
    lines += [
        "",
        "---",
        "",
        "## 6. Sign-off",
        "",
        "| Role | Decision | Name | Date |",
        "|------|----------|------|------|",
        "| Fraud operations lead | Reviewed | | |",
        "| Engineering lead | Approved for next run | | |",
        "",
    ]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / REPORT_FILE
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    demo_summary = {
        "total_transactions": 1000,
        "tier_counts": {"HIGH": 18, "MEDIUM": 46, "LOW": 936},
        "top_patterns": [("AMOUNT_ANOMALY", 22), ("ODD_HOUR", 15)],
        "amount_at_risk_inr": 3_450_000,
        "benchmark": {"throughput_tps": 210.4, "p95_latency_ms": 38.2},
    }
    print(generate_daily_summary.__doc__)
