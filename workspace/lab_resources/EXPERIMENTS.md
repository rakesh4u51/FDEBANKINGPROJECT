# Project 4 — Experiment Lab

Optional experiments to deepen understanding. None are graded.

---

## Experiment 1 — Measure the prefilter's effect

1. Run `prefilter_candidates` over `generate_transactions(count=1000)`.
2. Print `len(candidates)` — expect roughly 60-100 out of 1,000 (the seeded
   anomaly rate plus a few incidental matches).
3. This is the number of transactions that actually reach Claude — the other
   ~900+ never leave the rule layer.

---

## Experiment 2 — Batch size vs. throughput

```python
from engine.fraud_engine import run_fraud_detection
for bs in (10, 25, 50, 100):
    result = run_fraud_detection(count=1000, batch_size=bs)
    print(bs, result["benchmark"]["throughput_tps"])
```

Larger batches mean fewer, chunkier LLM calls; smaller batches mean more
parallelism opportunity but more per-call overhead. Find the knee of the
curve for this workload.

---

## Experiment 3 — Worker count vs. tail latency

```python
from engine.fraud_engine import run_fraud_detection
for workers in (2, 4, 8, 16):
    result = run_fraud_detection(count=1000, max_workers=workers)
    print(workers, result["benchmark"])
```

Watch p95/p99, not just throughput — more workers usually raises throughput
but can also raise tail latency if downstream rate limits kick in.

---

## Experiment 4 — Inject an obvious fraud case

```python
from common.patterns import detect_fraud_signals
obvious = [{
    "txn_id": "TXN-TEST-1", "account_id": "ACC-999999",
    "card_number_masked": "****9999", "amount_inr": 850000,
    "merchant_category": "jewellery", "channel": "ONLINE",
    "city": "Mumbai", "device_id": "DEV-NEW-0001",
    "hour_of_day": 2, "timestamp": "2026-07-15T02:14:00+00:00",
}]
print(detect_fraud_signals(obvious))
```

Confirm it lands in the HIGH tier via `assign_risk_tier`.

---

## Experiment 5 — Disable the prefilter and compare

Temporarily call `classify_with_claude(transactions)` directly on the full
1,000-transaction list instead of the prefiltered candidates. Compare wall
time and (if you're tracking API usage) call volume against the prefiltered
run. This is why the prefilter exists.

---

## Experiment 6 — Tune the risk thresholds

Lower `HIGH_THRESHOLD` in `common/risk.py` from 70 to 55 and re-run the full
pipeline. Compare the new `tier_counts` — how much bigger did the analyst
queue get, and is that a reasonable tradeoff for catching more borderline
cases?
