# Evidence folder

Save screenshots here when completing the lab. Replace each `.svg` placeholder with a `.png` of the same base name.

| File | What to capture |
|------|-----------------|
| `01_batch_throughput.png` | Batch processing running concurrently across the thread pool |
| `02_pattern_matching.png` | Claude-scored candidates — `fraud_score` + `matched_patterns` |
| `03_risk_tiers.png` | HIGH/MEDIUM/LOW queue, HIGH sorted by score |
| `04_benchmark.png` | 1,000-transaction benchmark — throughput (tps) + p50/p95/p99 latency |
| `05_fraud_report.png` | `reports/DAILY_FRAUD_SUMMARY.md` — tier table, top patterns, benchmark section |
| `06_resilience.png` | `python -m engine.resilience_drill` — `RETRY_ABSORBED`, `CIRCUIT_OPENED`, all checks PASS |
