# CLAUDE.md — Heritage National Bank Fraud Engine (Project 4)

> Authoritative context for Claude Code sessions. Keep accurate and concise.

## Pipeline under construction

```
generate_transactions  →  process_in_batches (Activity 1)
                                   │
                          detect_fraud_signals (Activity 2 — Claude pattern match)
                                   │
                          prioritize_queue (Activity 3 — HIGH/MEDIUM/LOW)
                                   │
                          build_benchmark_result (Activity 4 — latency/throughput)
                                   │
                          generate_daily_summary + write_report (Activity 5)
```

## Systems

| System | Role | Source |
|--------|------|--------|
| common/generator.py | Synthetic transaction feed (baseline, working) | `common/generator.py` |
| common/metrics.py | Latency/throughput measurement (baseline, working) | `common/metrics.py` |
| common/batch.py | Batch + concurrent processing for throughput | `common/batch.py` |
| common/patterns.py | Rule prefilter + Claude-based pattern matching | `common/patterns.py` |
| common/risk.py | HIGH/MEDIUM/LOW risk tiering | `common/risk.py` |
| common/reporting.py | Daily fraud summary report | `common/reporting.py` |
| common/resilience.py | Retries + circuit breaker around the Claude call | `common/resilience.py` |
| engine/resilience_drill.py | Fault-injection drill — resilience evidence | `engine/resilience_drill.py` |
| engine/fraud_engine.py | Orchestrator — wires all of the above | `engine/fraud_engine.py` |

## Non-negotiables — MANDATORY (this lab)

1. **Throughput** — the engine must process 1,000 transactions concurrently in
   batches, not one at a time. `common.batch.process_in_batches` is the only
   place concurrency is introduced.
2. **Cost/latency discipline** — `common.patterns.classify_with_claude` must
   only ever receive pre-filtered candidates from `prefilter_candidates`,
   never the full transaction list. Sending all 1,000 to the LLM is a
   correctness bug in this lab, not just a cost concern.
3. **Risk tiers** — every scored transaction must land in exactly one of
   HIGH / MEDIUM / LOW via `common.risk.assign_risk_tier`.
4. **PII hygiene** — card numbers arrive already masked
   (`card_number_masked`) from the generator; never re-introduce a full PAN
   into a prompt, log, or report.
5. **Benchmark evidence** — Activity 4 must record throughput (tps) and
   p50/p95/p99 latency against `target_tps`.
6. **Resilience** — every Claude call goes through `common.resilience.retry_call`
   with the shared `CLAUDE_BREAKER`; retries absorb transient faults, and an
   open breaker degrades to the rule fallback. Evidence: `python -m engine.resilience_drill`.

## Working rules

- Remove every `# BUILD:` marker in `engine/fraud_engine.py` by wiring in the
  control it names.
- Remove every `TODO(P4)` marker and `raise NotImplementedError` once a stub
  is implemented.
- Run each `common/*.py` file standalone (`python -m common.batch`, etc.) to
  sanity-check a module before wiring it into the engine.

## Model Routing

| Task | Model |
|------|-------|
| Fraud pattern classification (Activity 2) | claude-haiku-4-5 |
| Report narrative / summarization | claude-sonnet-4-5 |
| Complex reasoning / debugging | claude-opus-4-5 |
