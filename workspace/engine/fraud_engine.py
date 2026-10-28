"""
Real-time fraud detection engine — orchestrator.

Wires the pieces built in Activities 1-3 and 5 into one pipeline, exercised
end-to-end in Activity 4 (process 1,000 transactions + benchmark).

Pipeline: generate -> batch-process (pattern match per batch) -> prioritize -> report.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from common.batch import process_in_batches
from common.generator import generate_transactions
from common.metrics import build_benchmark_result, measure
from common.patterns import detect_fraud_signals
from common.reporting import generate_daily_summary, write_report
from common.risk import prioritize_queue

DEFAULT_TRANSACTION_COUNT = 1000
# Tuned in Activity 4. Baseline 25 x 8 workers = 40 batches in 5 waves -> ~126 tps
# (below the 150 tps target). 50 x 20 workers = 20 batches in a single wave ->
# ~300 tps. Tradeoff: up to 20 concurrent LLM calls (rate-limit exposure) and
# larger per-call prompts (higher single-batch latency).
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_WORKERS = 20


def _score_batch(batch: list[dict]) -> list[dict]:
    """Run pattern matching on one batch and return it with scores attached."""
    return detect_fraud_signals(batch)


def run_fraud_detection(
    count: int = DEFAULT_TRANSACTION_COUNT,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
    target_tps: float = 150.0,
) -> dict:
    """Run the full pipeline over `count` synthetic transactions and return
    {"summary": ..., "benchmark": ..., "report_path": ...}.
    """
    transactions = generate_transactions(count=count)

    started = time.perf_counter()
    with measure("fraud_detection_run", items_processed=count) as m:
        # Activity 1 — concurrent batch processing for throughput.
        scored = process_in_batches(
            transactions, worker_fn=_score_batch,
            batch_size=batch_size, max_workers=max_workers,
        )
    elapsed_seconds = time.perf_counter() - started

    # Approximate per-transaction latency for the percentile benchmark: spread
    # the measured wall-clock time evenly (real telemetry would time each txn).
    per_txn_ms = (m.elapsed_ms / max(1, len(scored)))
    latencies_ms = [per_txn_ms] * len(scored)

    # Activity 4 — benchmark latency/throughput against target_tps.
    benchmark = build_benchmark_result(
        total_transactions=len(scored),
        elapsed_seconds=elapsed_seconds,
        latencies_ms=latencies_ms,
        target_tps=target_tps,
    )

    # Persist the raw benchmark for the daily report and the evidence capture step.
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/benchmark_result.json").write_text(
        json.dumps(benchmark.as_dict(), indent=2), encoding="utf-8"
    )

    # Activity 3 — real-time risk prioritization (HIGH/MEDIUM/LOW).
    prioritized = prioritize_queue(scored)

    # Activity 5 — daily fraud summary report with pattern analysis.
    summary = generate_daily_summary(prioritized, benchmark.as_dict())
    report_path = write_report(summary)

    return {
        "summary": summary,
        "benchmark": benchmark.as_dict(),
        "prioritized_counts": prioritized.get("counts", {}),
        "report_path": str(report_path),
    }


if __name__ == "__main__":
    result = run_fraud_detection(count=DEFAULT_TRANSACTION_COUNT)
    print(f"Processed {DEFAULT_TRANSACTION_COUNT} transactions")
    print("Benchmark:", result["benchmark"])
    print("Tier counts:", result["prioritized_counts"])
    print("Report written to:", result["report_path"])
