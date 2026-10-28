"""
common.metrics — latency and throughput measurement for the fraud engine.

Baseline is provided and working. `measure()` times a phase of the pipeline;
`compute_latency_percentiles()` turns a list of per-transaction latencies into
p50/p95/p99; `BenchmarkResult` is the shape Activity 4 and the daily report
(Activity 5) both read from.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class RunMetrics:
    phase: str
    elapsed_ms: float = 0.0
    items_processed: int = 0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "phase": self.phase,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "items_processed": self.items_processed,
            "notes": self.notes,
        }


@contextmanager
def measure(phase: str, items_processed: int = 0):
    """Time a pipeline phase and return a RunMetrics the caller can annotate."""
    m = RunMetrics(phase=phase, items_processed=items_processed)
    started = time.perf_counter()
    try:
        yield m
    finally:
        m.elapsed_ms = (time.perf_counter() - started) * 1000


@dataclass
class BenchmarkResult:
    total_transactions: int
    elapsed_seconds: float
    throughput_tps: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    target_tps: float = 150.0

    @property
    def meets_target(self) -> bool:
        return self.throughput_tps >= self.target_tps

    def as_dict(self) -> dict:
        return {
            "total_transactions": self.total_transactions,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "throughput_tps": round(self.throughput_tps, 2),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "target_tps": self.target_tps,
            "meets_target": self.meets_target,
        }


def compute_latency_percentiles(latencies_ms: list[float]) -> dict:
    """Return p50/p95/p99 (ms) from a list of per-transaction latencies."""
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    ordered = sorted(latencies_ms)

    def pct(p: float) -> float:
        k = max(0, min(len(ordered) - 1, int(round(p * (len(ordered) - 1)))))
        return ordered[k]

    return {"p50": pct(0.50), "p95": pct(0.95), "p99": pct(0.99)}


def build_benchmark_result(
    total_transactions: int,
    elapsed_seconds: float,
    latencies_ms: list[float],
    target_tps: float = 150.0,
) -> BenchmarkResult:
    pct = compute_latency_percentiles(latencies_ms)
    throughput = total_transactions / elapsed_seconds if elapsed_seconds > 0 else 0.0
    return BenchmarkResult(
        total_transactions=total_transactions,
        elapsed_seconds=elapsed_seconds,
        throughput_tps=throughput,
        p50_latency_ms=pct["p50"],
        p95_latency_ms=pct["p95"],
        p99_latency_ms=pct["p99"],
        target_tps=target_tps,
    )
