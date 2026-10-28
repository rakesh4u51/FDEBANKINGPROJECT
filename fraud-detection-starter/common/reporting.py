"""
common.reporting — daily fraud summary report (Activity 5).

STUB: implement the two functions during Activity 5.

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

from pathlib import Path

REPORT_DIR = Path("reports")


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
    from collections import Counter

    tier_counts = prioritized.get("counts", {"HIGH": 0, "MEDIUM": 0, "LOW": 0})
    pattern_counter: Counter[str] = Counter()
    high_amount = 0

    for txn in prioritized.get("HIGH", []) + prioritized.get("MEDIUM", []):
        for pattern in txn.get("matched_patterns", []):
            pattern_counter[pattern] += 1

    for txn in prioritized.get("HIGH", []):
        high_amount += int(txn.get("amount_inr", 0))

    total_transactions = sum(tier_counts.values()) or prioritized.get("total_transactions", 0)
    return {
        "total_transactions": int(total_transactions),
        "tier_counts": {
            "HIGH": int(tier_counts.get("HIGH", 0)),
            "MEDIUM": int(tier_counts.get("MEDIUM", 0)),
            "LOW": int(tier_counts.get("LOW", 0)),
        },
        "top_patterns": pattern_counter.most_common(),
        "amount_at_risk_inr": int(high_amount),
        "benchmark": benchmark,
    }


def write_report(summary: dict) -> Path:
    """Render `summary` as reports/DAILY_FRAUD_SUMMARY.md and return the path.

    Follow starter_files/resources/fraud_summary_report_template.md for the
    section headings (Executive summary, Risk tier breakdown, Top fraud
    patterns, Throughput & latency benchmark, Recommendations).
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    tier_counts = summary.get("tier_counts", {"HIGH": 0, "MEDIUM": 0, "LOW": 0})
    total = max(1, int(summary.get("total_transactions", 0)))
    high_count = int(tier_counts.get("HIGH", 0))
    medium_count = int(tier_counts.get("MEDIUM", 0))
    low_count = int(tier_counts.get("LOW", 0))

    top_patterns = summary.get("top_patterns", [])[:3]
    pattern_rows = "\n".join(
        f"| {pattern} | {count} | |" for pattern, count in top_patterns
    ) or "| — | 0 | |"

    benchmark = summary.get("benchmark", {})
    throughput = benchmark.get("throughput_tps", 0)
    p50 = benchmark.get("p50_latency_ms", 0)
    p95 = benchmark.get("p95_latency_ms", 0)
    p99 = benchmark.get("p99_latency_ms", 0)
    target = benchmark.get("target_tps", 150)
    met = throughput >= target
    status_text = "met" if met else "did not meet"

    report_path = REPORT_DIR / "DAILY_FRAUD_SUMMARY.md"
    report_path.write_text(
        """# Daily Fraud Summary Report

**System:** Heritage National Bank real-time fraud detection engine
**Scope:** common/batch · common/patterns · common/risk · common/metrics · engine/fraud_engine
**Run date:** _2026-10-28_  **Prepared by:** _AI Agent_

> Save the completed report to `reports/DAILY_FRAUD_SUMMARY.md`.

---

## 1. Executive summary

{total} transactions were processed in the latest run. The fraud exposure in the HIGH tier was ₹{risk} and the current posture is {status}. Throughput was {throughput} TPS against a {target} TPS target, which {status_text} the target.

---

## 2. Risk tier breakdown

| Tier | Count | % of total | Action |
|------|------:|-----------:|--------|
| HIGH | {high} | {high_pct:.1f}% | Immediate analyst review |
| MEDIUM | {medium} | {medium_pct:.1f}% | Step-up verification / monitor |
| LOW | {low} | {low_pct:.1f}% | Straight-through clear |

**Amount at risk (HIGH tier):** ₹{risk}

---

## 3. Top fraud patterns

| Pattern | Frequency | Notes |
|---------|----------:|-------|
{pattern_rows}

_Pull these from `summary["top_patterns"]`._

---

## 4. Throughput & latency benchmark

| Metric | Value | Target | Met? |
|--------|------:|-------:|:----:|
| Total transactions | {total} | 1,000 | {total_ok} |
| Throughput (tps) | {throughput} | {target} | {met_str} |
| p50 latency (ms) | {p50} | — | |
| p95 latency (ms) | {p95} | — | |
| p99 latency (ms) | {p99} | — | |

_Pull these from `reports/benchmark_result.json`._

---

## 5. Recommendations

Review HIGH-tier cases first, tune batch sizing if throughput dips below target, and keep monitoring the dominant fraud triggers identified above.

---

## 6. Sign-off

| Role | Decision | Name | Date |
|------|----------|------|------|
| Fraud operations lead | Reviewed | | |
| Engineering lead | Approved for next run | | |
""".format(
            total=total,
            risk=f"{summary.get('amount_at_risk_inr', 0):,}",
            status='conservative' if high_count else 'stable',
            throughput=throughput,
            target=target,
            status_text=status_text,
            high=high_count,
            high_pct=(high_count / total * 100) if total else 0,
            medium=medium_count,
            medium_pct=(medium_count / total * 100) if total else 0,
            low=low_count,
            low_pct=(low_count / total * 100) if total else 0,
            pattern_rows=pattern_rows,
            total_ok='Yes' if total >= 1000 else 'No',
            met_str='Yes' if met else 'No',
            p50=p50,
            p95=p95,
            p99=p99,
        )
    )
    return report_path


if __name__ == "__main__":
    demo_summary = {
        "total_transactions": 1000,
        "tier_counts": {"HIGH": 18, "MEDIUM": 46, "LOW": 936},
        "top_patterns": [("AMOUNT_ANOMALY", 22), ("ODD_HOUR", 15)],
        "amount_at_risk_inr": 3_450_000,
        "benchmark": {"throughput_tps": 210.4, "p95_latency_ms": 38.2},
    }
    print(generate_daily_summary.__doc__)
