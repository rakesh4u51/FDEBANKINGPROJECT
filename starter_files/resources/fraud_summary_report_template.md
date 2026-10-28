# Daily Fraud Summary Report

**System:** Heritage National Bank real-time fraud detection engine
**Scope:** common/batch · common/patterns · common/risk · common/metrics · engine/fraud_engine
**Run date:** _<yyyy-mm-dd>_  **Prepared by:** _<your name>_

> Save the completed report to `reports/DAILY_FRAUD_SUMMARY.md`.

---

## 1. Executive summary

_2-3 sentences: transactions processed, headline fraud exposure (amount at
risk), whether throughput met target, overall posture._

---

## 2. Risk tier breakdown

| Tier | Count | % of total | Action |
|------|------:|-----------:|--------|
| HIGH | _<n>_ | _<%>_ | Immediate analyst review |
| MEDIUM | _<n>_ | _<%>_ | Step-up verification / monitor |
| LOW | _<n>_ | _<%>_ | Straight-through clear |

**Amount at risk (HIGH tier):** ₹_<amount_at_risk_inr>_

---

## 3. Top fraud patterns

| Pattern | Frequency | Notes |
|---------|----------:|-------|
| _<PATTERN_CODE>_ | _<n>_ | _<one line: what it usually means>_ |
| _<PATTERN_CODE>_ | _<n>_ | |
| _<PATTERN_CODE>_ | _<n>_ | |

_Pull these from `summary["top_patterns"]`._

---

## 4. Throughput & latency benchmark

| Metric | Value | Target | Met? |
|--------|------:|-------:|:----:|
| Total transactions | _<n>_ | 1,000 | |
| Throughput (tps) | _<n>_ | _<target_tps>_ | |
| p50 latency (ms) | _<n>_ | — | |
| p95 latency (ms) | _<n>_ | — | |
| p99 latency (ms) | _<n>_ | — | |

_Pull these from `reports/benchmark_result.json`._

---

## 5. Recommendations

_e.g. tune risk thresholds, adjust batch size/workers if throughput is
marginal, add a geo-velocity signal, review the HIGH-tier queue size against
analyst capacity._

---

## 6. Sign-off

| Role | Decision | Name | Date |
|------|----------|------|------|
| Fraud operations lead | Reviewed | | |
| Engineering lead | Approved for next run | | |
