# Daily Fraud Summary Report

**System:** Heritage National Bank real-time fraud detection engine
**Scope:** common/batch · common/patterns · common/risk · common/metrics · engine/fraud_engine
**Run date:** 2026-10-27  **Prepared by:** Fraud detection engine (automated)

---

## 1. Executive summary

The engine processed **1,000** transactions and flagged **58** for action (53 HIGH, 5 MEDIUM). Amount at risk in the HIGH tier is **₹2,80,73,491**. Throughput was **300.41 tps** against a target of 150 tps — target **met**. Overall posture: elevated — clear the HIGH queue first.

---

## 2. Risk tier breakdown

| Tier | Count | % of total | Action |
|------|------:|-----------:|--------|
| HIGH | 53 | 5.3% | Immediate analyst review |
| MEDIUM | 5 | 0.5% | Step-up verification / monitor |
| LOW | 942 | 94.2% | Straight-through clear |
| **Total** | **1,000** | **100%** | |

**Amount at risk (HIGH tier):** ₹2,80,73,491

---

## 3. Top fraud patterns

Frequency of matched patterns across HIGH + MEDIUM transactions.

| Pattern | Frequency | Notes |
|---------|----------:|-------|
| AMOUNT_ANOMALY | 53 | Ticket size far above the account/category norm |
| ODD_HOUR | 53 | Activity outside typical customer hours (23:00-04:59) |
| NEW_DEVICE | 51 | Device not previously seen on the account |
| MERCHANT_RISK | 15 | High-risk merchant (jewellery, electronics, wallet top-up) |

---

## 4. Throughput & latency benchmark

| Metric | Value | Target | Met? |
|--------|------:|-------:|:----:|
| Total transactions | 1,000 | 1,000 | Yes |
| Elapsed (s) | 3.329 | — | |
| Throughput (tps) | 300.41 | 150 | Yes |
| p50 latency (ms) | 3.33 | — | |
| p95 latency (ms) | 3.33 | — | |
| p99 latency (ms) | 3.33 | — | |

_Source: `reports/benchmark_result.json`. Per-transaction latency is the run's wall-clock time spread evenly across transactions._

---

## 5. Recommendations

1. Work the 53 HIGH-tier transactions in score order (₹2,80,73,491 exposure); confirm queue size fits analyst capacity.
2. Route the 5 MEDIUM-tier transactions to step-up verification (OTP / call-back) rather than outright blocks.
3. Most frequent signal is AMOUNT_ANOMALY — review the rule threshold behind it to keep false positives in check.
4. Throughput met target; keep batch size/workers as-is and re-benchmark at peak volume.
5. Add account-level history (velocity, geo) so VELOCITY_ABUSE and GEO_MISMATCH can be evidenced, not just inferred.

---

## 6. Sign-off

| Role | Decision | Name | Date |
|------|----------|------|------|
| Fraud operations lead | Reviewed | | |
| Engineering lead | Approved for next run | | |
