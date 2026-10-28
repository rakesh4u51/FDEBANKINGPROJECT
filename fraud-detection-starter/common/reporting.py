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
    # TODO(P4): count patterns across HIGH+MEDIUM transactions, sum HIGH amounts,
    #           assemble the dict shape above.
    raise NotImplementedError("Activity 5: implement generate_daily_summary()")


def write_report(summary: dict) -> Path:
    """Render `summary` as reports/DAILY_FRAUD_SUMMARY.md and return the path.

    Follow starter_files/resources/fraud_summary_report_template.md for the
    section headings (Executive summary, Risk tier breakdown, Top fraud
    patterns, Throughput & latency benchmark, Recommendations).
    """
    # TODO(P4): REPORT_DIR.mkdir(...), build markdown text from `summary`, write it.
    raise NotImplementedError("Activity 5: implement write_report()")


if __name__ == "__main__":
    demo_summary = {
        "total_transactions": 1000,
        "tier_counts": {"HIGH": 18, "MEDIUM": 46, "LOW": 936},
        "top_patterns": [("AMOUNT_ANOMALY", 22), ("ODD_HOUR", 15)],
        "amount_at_risk_inr": 3_450_000,
        "benchmark": {"throughput_tps": 210.4, "p95_latency_ms": 38.2},
    }
    print(generate_daily_summary.__doc__)
