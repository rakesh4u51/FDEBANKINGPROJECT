# Project 4 — Prompt Library

Copy-paste prompts for Claude Code. Reference `pattern_reference.py` for patterns.

---

## Activity 1 — Batch transaction processing

```
Implement common/batch.py: chunk_transactions(transactions, batch_size) as a
generator yielding fixed-size slices, and process_in_batches(transactions,
worker_fn, batch_size, max_workers) using concurrent.futures.ThreadPoolExecutor
to run worker_fn on every batch concurrently, then flatten the results back
into one list preserving the original transaction order. Remove the
NotImplementedError and TODO(P4) markers.
```

---

## Activity 2 — ML-style pattern matching using Claude

```
Implement common/patterns.py:
- prefilter_candidates: cheap rule pass over ALL transactions (no LLM call) —
  flag amount_inr > AMOUNT_THRESHOLD_INR, hour_of_day in ODD_HOURS, merchant
  in HIGH_RISK_MERCHANTS, or "NEW" in device_id.
- classify_with_claude: send only the pre-filtered candidates to Claude in one
  batch prompt using CLASSIFY_SYSTEM_PROMPT, call get_llm_client().messages
  .create(model=resolve_model(model), ...), parse the JSON array response
  (strip markdown fences defensively) into {txn_id: {fraud_score,
  matched_patterns}}.
- detect_fraud_signals: prefilter, classify only the candidates, merge scores
  back onto the full transaction list (default fraud_score=0,
  matched_patterns=[] for anything not flagged).
Remove the NotImplementedError and TODO(P4) markers.
```

---

## Activity 3 — Real-time risk prioritization

```
Implement common/risk.py: assign_risk_tier(fraud_score, matched_patterns)
returns HIGH if fraud_score >= 70 or 2+ matched patterns, MEDIUM if
fraud_score >= 40 or exactly 1 matched pattern, else LOW. prioritize_queue
buckets a scored transaction list by tier, sorts HIGH by fraud_score
descending, and returns counts per tier. Remove the NotImplementedError and
TODO(P4) markers.
```

---

## Activity 4 — Process 1,000 transactions + benchmark

```
Run engine/fraud_engine.py's run_fraud_detection(count=1000) end to end.
Confirm reports/benchmark_result.json is written with throughput_tps and
p50/p95/p99 latency, and that throughput_tps meets target_tps (150 by
default). If it doesn't, tune batch_size / max_workers in
DEFAULT_BATCH_SIZE / DEFAULT_MAX_WORKERS and re-run — explain the tradeoff
you made.
```

---

## Activity 5 — Daily fraud summary report

```
Implement common/reporting.py: generate_daily_summary(prioritized, benchmark)
aggregates total_transactions, tier_counts, top_patterns (frequency across
HIGH+MEDIUM transactions, sorted desc), amount_at_risk_inr (sum of amount_inr
over the HIGH tier), and the benchmark dict. write_report renders
reports/DAILY_FRAUD_SUMMARY.md following
starter_files/resources/fraud_summary_report_template.md — executive summary,
risk tier breakdown, top fraud patterns, throughput & latency benchmark,
recommendations. Remove the NotImplementedError and TODO(P4) markers.
```

---

## Verification

```
Run engine/fraud_engine.py end to end (python -m engine.fraud_engine), then
open reports/DAILY_FRAUD_SUMMARY.md and reports/benchmark_result.json and
confirm the tier counts, top patterns, and throughput numbers look sane for a
1,000-transaction run. Also confirm no NotImplementedError/TODO(P4) markers
remain in common/batch.py, common/patterns.py, common/risk.py, or
common/reporting.py, and no # BUILD: markers remain in
engine/fraud_engine.py.
```
