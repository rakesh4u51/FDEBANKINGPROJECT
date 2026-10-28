"""
Resilience drill — prove retries absorb blips and the circuit breaker trips.

Runs the real engine path (process_in_batches -> detect_fraud_signals over
1,000 transactions, same batch size / workers as fraud_engine) with a
FaultInjector in front of the Claude call:

  Phase 1  calls 1-5   : fail on first attempt only  -> RETRY_ABSORBED
  Phase 2  calls 6-20  : sustained provider outage   -> CIRCUIT_OPENED,
                         remaining calls fail fast (CIRCUIT_REJECTED) and
                         degrade to the rule fallback (FALLBACK_USED)
  Phase 3  call while OPEN                           -> CIRCUIT_REJECTED
  Phase 4  after the recovery timeout, a real probe  -> CIRCUIT_HALF_OPEN,
                         CIRCUIT_CLOSED

Writes reports/resilience_events.jsonl and reports/RESILIENCE_DRILL.md.
Does not touch DAILY_FRAUD_SUMMARY.md or benchmark_result.json.

    python -m engine.resilience_drill
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import common.patterns as patterns
from common.batch import process_in_batches
from common.generator import generate_transactions
from common.resilience import EVENTS, FaultInjector
from engine.fraud_engine import DEFAULT_BATCH_SIZE, DEFAULT_MAX_WORKERS, DEFAULT_TRANSACTION_COUNT, _score_batch

EVENTS_FILE = Path("reports/resilience_events.jsonl")
REPORT_FILE = Path("reports/RESILIENCE_DRILL.md")


def run_drill(count: int = DEFAULT_TRANSACTION_COUNT) -> dict:
    breaker = patterns.CLAUDE_BREAKER
    EVENTS.reset()
    breaker.reset()
    transactions = generate_transactions(count=count)
    candidates = patterns.prefilter_candidates(transactions)

    print(f"== Phase 1-2: {count} txns, {DEFAULT_MAX_WORKERS} workers, 5 flaky calls then provider outage")
    patterns.fault_injector = FaultInjector(flaky_calls=5, outage_calls=15)
    try:
        started = time.perf_counter()
        scored = process_in_batches(transactions, worker_fn=_score_batch,
                                    batch_size=DEFAULT_BATCH_SIZE, max_workers=DEFAULT_MAX_WORKERS)
        elapsed = time.perf_counter() - started
        state_after_outage = breaker.state
    finally:
        patterns.fault_injector = None  # provider is healthy from here on

    print("== Phase 3: call while breaker is OPEN (must fail fast)")
    fast_started = time.perf_counter()
    patterns.detect_fraud_signals(candidates[:5])
    fast_fail_ms = (time.perf_counter() - fast_started) * 1000

    print(f"== Phase 4: wait {breaker.recovery_timeout_s:g}s recovery timeout, then probe the provider")
    time.sleep(breaker.recovery_timeout_s + 0.2)
    patterns.detect_fraud_signals(candidates[:5])

    counts = EVENTS.counts()
    scored_ids = {t["txn_id"] for t in scored}
    flagged = {t["txn_id"] for t in candidates}
    checks = {
        "Retries absorbed transient faults (RETRY_ABSORBED)": counts.get("RETRY_ABSORBED", 0) >= 1,
        "Circuit breaker tripped (CIRCUIT_OPENED)": counts.get("CIRCUIT_OPENED", 0) >= 1,
        "Open breaker failed fast (CIRCUIT_REJECTED)": counts.get("CIRCUIT_REJECTED", 0) >= 1,
        "Degraded to rule fallback (FALLBACK_USED)": counts.get("FALLBACK_USED", 0) >= 1,
        f"All {count} transactions scored, none lost": len(scored) == count and len(scored_ids) == count,
        "Every flagged candidate kept a non-zero score": all(
            t["fraud_score"] > 0 for t in scored if t["txn_id"] in flagged),
        "Breaker recovered (CIRCUIT_HALF_OPEN -> CIRCUIT_CLOSED)": (
            counts.get("CIRCUIT_HALF_OPEN", 0) >= 1 and counts.get("CIRCUIT_CLOSED", 0) >= 1
            and breaker.state == "CLOSED"),
    }
    result = {
        "counts": counts, "checks": checks, "elapsed_s": round(elapsed, 3),
        "state_after_outage": state_after_outage, "final_state": breaker.state,
        "fast_fail_ms": round(fast_fail_ms, 2), "candidates": len(candidates),
    }
    EVENTS.write_jsonl(EVENTS_FILE)
    _write_report(result)
    return result


def _write_report(result: dict) -> None:
    breaker = patterns.CLAUDE_BREAKER
    lines = [
        "# Resilience Drill — Retries & Circuit Breaker",
        "",
        "**System:** Heritage National Bank real-time fraud detection engine",
        f"**Run date:** {date.today().isoformat()}  **Command:** `python -m engine.resilience_drill`",
        f"**Breaker:** `{breaker.name}` — opens after {breaker.failure_threshold} consecutive failed calls, "
        f"half-opens after {breaker.recovery_timeout_s:g}s. **Retries:** 2 per call, exponential backoff + jitter.",
        "",
        "## 1. Acceptance checks",
        "",
        "| Check | Result |",
        "|-------|:------:|",
    ]
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in result["checks"].items()]
    lines += [
        "",
        f"Breaker state after outage: **{result['state_after_outage']}** · "
        f"call while open returned in **{result['fast_fail_ms']} ms** · "
        f"final state: **{result['final_state']}** · "
        f"1,000-txn run under faults: **{result['elapsed_s']} s**",
        "",
        "## 2. Event counts",
        "",
        "| Event | Count |",
        "|-------|------:|",
    ]
    lines += [f"| {event} | {n} |" for event, n in result["counts"].items()]
    lines += [
        "",
        f"## 3. Event timeline (`{EVENTS_FILE}`)",
        "",
        "```",
    ]
    for row in EVENTS.events():
        detail = " ".join(f"{k}={v}" for k, v in row.items() if k not in ("ts", "event"))
        lines.append(f"{row['ts'][11:23]}  {row['event']:<18} {detail}")
    lines += ["```", ""]
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = run_drill()
    print("\nEvent counts:", result["counts"])
    for name, ok in result["checks"].items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("Events written to:", EVENTS_FILE)
    print("Report written to:", REPORT_FILE)
