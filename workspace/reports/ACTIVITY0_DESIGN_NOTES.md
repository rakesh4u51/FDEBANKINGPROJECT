# Activity 0 — Architecture study & design worksheet

## Pipeline stages → activity

| # | Stage | Component | Activity |
|:-:|-------|-----------|:--------:|
| 1 | Generate 1,000 txns → chunk + process concurrently | `common.generator` → `common.batch.process_in_batches` | 1 |
| 2 | Rule prefilter (all txns) → Claude classification (candidates only) | `common.patterns.prefilter_candidates` → `classify_with_claude` | 2 |
| 3 | HIGH / MEDIUM / LOW tiering, HIGH sorted by score | `common.risk.prioritize_queue` | 3 |
| 4 | Throughput + p50/p95/p99 benchmark vs `target_tps` | `engine.fraud_engine` + `common.metrics` | 4 |
| 5 | Daily fraud summary report | `common.reporting.write_report` | 5 |

Transaction path: generated → batched → prefiltered → classified → tiered → benchmarked → reported.

## Worksheet answers

1. **Prefilter before Claude:** the prefilter is a cheap deterministic pass over all 1,000; the LLM is the expensive step. Reversing the order pays LLM latency/cost on every transaction (this run: 81 of 1,000 reach Claude across 20 calls).
2. **ThreadPoolExecutor, not processes:** the work is I/O-bound (waiting on network LLM responses), so threads give concurrency without process start-up and serialization overhead.
3. **Two-value verdict:** analysts either get flooded (no prioritization) or borderline cases get blocked/cleared outright instead of being routed to step-up verification.
4. **Throughput + p95/p99:** an average hides tail latency; a few slow batches can starve the queue even when the mean looks fine.
5. **Tuning knobs:** `DEFAULT_BATCH_SIZE` (bigger = fewer calls, but higher per-batch latency) and `DEFAULT_MAX_WORKERS` (more = more parallelism, but provider rate-limit/error risk).

## Activity 4 tuning record

| batch_size | max_workers | Batches / waves | throughput_tps | Meets 150? |
|-----------:|------------:|----------------:|---------------:|:----------:|
| 25 (default) | 8 (default) | 40 / 5 | 126.19 | No |
| 25 | 20 | 40 / 2 | 177.47 | Yes |
| **50 (chosen)** | **20 (chosen)** | **20 / 1** | **~190-300** | **Yes** |
| 100 | 10 | 10 / 1 | 297.34 | Yes |

Tradeoff: up to 20 concurrent LLM calls (rate-limit exposure) in exchange for a single wave of batches. Throughput varies run to run with OpenRouter latency.

## Design deviation (documented)

The prompt's literal rule `merchant_category in HIGH_RISK_MERCHANTS` flags 332/1,000 (33%), because high-risk categories are 3 of the 10 categories in normal traffic. That fails the 5-12% acceptance criterion. The merchant rule now fires only when `amount_inr > 40,000` (`HIGH_RISK_MERCHANT_MIN_AMOUNT_INR`), which gives 81/1,000 (8.1%).
