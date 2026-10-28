# Project 4 — Concepts Deep Dive

## The engine model — filter cheap, classify smart, act fast

```
1,000 transactions
      │
      ▼
Batch + concurrency (Activity 1) ──► throughput at scale
      │
      ▼
Rule prefilter (cheap, all 1,000) ──► candidates only (Activity 2)
      │
      ▼
Claude pattern match (candidates only) ──► fraud_score + matched_patterns
      │
      ▼
Risk tiering (Activity 3) ──► HIGH / MEDIUM / LOW queue
      │
      ▼
Benchmark (Activity 4) ──► throughput_tps, p50/p95/p99
      │
      ▼
Daily fraud summary report (Activity 5)
```

Each stage is complementary: batching keeps the pipeline from stalling on a
single slow call; the rule prefilter keeps the expensive LLM call off the
critical path for 90%+ of "obviously fine" transactions; risk tiering turns a
raw score into something an analyst can act on immediately; the benchmark
proves the design actually holds up at volume; the report is what the fraud
desk and management actually read.

## The five components and what they do

| Component (`common.*`) | Activity | What it does |
|-------------------------|----------|---------------|
| `batch.process_in_batches` | 1 | Chunk + run concurrently across a thread pool for throughput |
| `patterns.prefilter_candidates` | 2 | Cheap rule pass — no LLM call — narrows 1,000 down to the interesting few |
| `patterns.classify_with_claude` | 2 | ML-style pattern matching — Claude scores only the candidates |
| `risk.assign_risk_tier` / `prioritize_queue` | 3 | Score + pattern count → HIGH / MEDIUM / LOW work queue |
| `metrics.build_benchmark_result` | 4 | Throughput (tps) and p50/p95/p99 latency vs. target |
| `reporting.generate_daily_summary` / `write_report` | 5 | Aggregate + render the daily fraud summary |

## Why a rule prefilter before the LLM call

Sending all 1,000 transactions to Claude on every run is slow, expensive, and
unnecessary — the overwhelming majority of everyday transactions (grocery run,
fuel top-up, routine bill payment) don't need a language model to clear them.
The prefilter is a handful of cheap, deterministic checks (amount threshold,
odd hour, high-risk merchant, unfamiliar device) that narrow the field to a
small candidate set. Claude is then reserved for the genuinely ambiguous
cases, where pattern-matching judgment actually adds value over a fixed
threshold. This is the same "coarse filter, then expensive model" shape used
in real production fraud stacks.

## Why batching + threads, not "call once per transaction"

A loop that calls the pattern matcher once per transaction, waiting for each
call to return before starting the next, cannot keep pace with peak volumes —
latency stacks linearly with transaction count. `common.batch` splits the feed
into fixed-size batches and runs them concurrently with a thread pool: this is
I/O-bound work (waiting on an LLM response), so threads are the right
concurrency primitive, not multiprocessing.

## Risk tiers are a queueing decision, not just a label

HIGH tier is the analyst's immediate work queue, sorted by score — it must be
short enough to be actionable. MEDIUM is monitored / auto-stepped-up
(additional verification). LOW clears straight through. Getting the
thresholds right is a business tuning decision as much as a technical one: too
aggressive and you flood the desk with false positives; too loose and real
fraud clears.

## What "real time" means here

Real time in this lab does not mean sub-millisecond — it means the engine
keeps pace with peak transaction volume without a growing backlog. The
benchmark in Activity 4 is the evidence: throughput (transactions/second)
must meet the target, and tail latency (p95/p99) must stay bounded even under
1,000 transactions in one run.

## Efficiency measurement

`common.metrics.measure()` times the batch-processing phase; `common.metrics
.build_benchmark_result()` turns that into throughput and latency
percentiles. The daily report's benchmark section is built directly from
these numbers — pattern-matching accuracy should not come at the cost of
throughput, and vice versa.
