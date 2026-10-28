# Resilience Drill — Retries & Circuit Breaker

**System:** Heritage National Bank real-time fraud detection engine
**Run date:** 2026-10-28  **Command:** `python -m engine.resilience_drill`
**Breaker:** `claude` — opens after 3 consecutive failed calls, half-opens after 5s. **Retries:** 2 per call, exponential backoff + jitter.

## 1. Acceptance checks

| Check | Result |
|-------|:------:|
| Retries absorbed transient faults (RETRY_ABSORBED) | PASS |
| Circuit breaker tripped (CIRCUIT_OPENED) | PASS |
| Open breaker failed fast (CIRCUIT_REJECTED) | PASS |
| Degraded to rule fallback (FALLBACK_USED) | PASS |
| All 1000 transactions scored, none lost | PASS |
| Every flagged candidate kept a non-zero score | PASS |
| Breaker recovered (CIRCUIT_HALF_OPEN -> CIRCUIT_CLOSED) | PASS |

Breaker state after outage: **OPEN** · call while open returned in **13.53 ms** · final state: **CLOSED** · 1,000-txn run under faults: **3.8 s**

## 2. Event counts

| Event | Count |
|-------|------:|
| RETRY_SCHEDULED | 35 |
| RETRIES_EXHAUSTED | 15 |
| FALLBACK_USED | 16 |
| CIRCUIT_OPENED | 1 |
| RETRY_ABSORBED | 5 |
| CIRCUIT_REJECTED | 1 |
| CIRCUIT_HALF_OPEN | 1 |
| CIRCUIT_CLOSED | 1 |

## 3. Event timeline (`reports/resilience_events.jsonl`)

```
01:54:08.498  RETRY_SCHEDULED    call=1 attempt=1 error=TransientProviderError backoff_ms=150
01:54:08.517  RETRY_SCHEDULED    call=2 attempt=1 error=TransientProviderError backoff_ms=159
01:54:08.536  RETRY_SCHEDULED    call=3 attempt=1 error=TransientProviderError backoff_ms=108
01:54:08.543  RETRY_SCHEDULED    call=4 attempt=1 error=TransientProviderError backoff_ms=157
01:54:08.560  RETRY_SCHEDULED    call=5 attempt=1 error=TransientProviderError backoff_ms=162
01:54:08.611  RETRY_SCHEDULED    call=6 attempt=1 error=TransientProviderError backoff_ms=150
01:54:08.614  RETRY_SCHEDULED    call=7 attempt=1 error=TransientProviderError backoff_ms=152
01:54:08.616  RETRY_SCHEDULED    call=8 attempt=1 error=TransientProviderError backoff_ms=137
01:54:08.624  RETRY_SCHEDULED    call=9 attempt=1 error=TransientProviderError backoff_ms=170
01:54:08.626  RETRY_SCHEDULED    call=10 attempt=1 error=TransientProviderError backoff_ms=122
01:54:08.627  RETRY_SCHEDULED    call=11 attempt=1 error=TransientProviderError backoff_ms=195
01:54:08.627  RETRY_SCHEDULED    call=12 attempt=1 error=TransientProviderError backoff_ms=197
01:54:08.628  RETRY_SCHEDULED    call=13 attempt=1 error=TransientProviderError backoff_ms=150
01:54:08.628  RETRY_SCHEDULED    call=14 attempt=1 error=TransientProviderError backoff_ms=150
01:54:08.629  RETRY_SCHEDULED    call=15 attempt=1 error=TransientProviderError backoff_ms=155
01:54:08.629  RETRY_SCHEDULED    call=16 attempt=1 error=TransientProviderError backoff_ms=147
01:54:08.629  RETRY_SCHEDULED    call=17 attempt=1 error=TransientProviderError backoff_ms=180
01:54:08.629  RETRY_SCHEDULED    call=18 attempt=1 error=TransientProviderError backoff_ms=183
01:54:08.629  RETRY_SCHEDULED    call=19 attempt=1 error=TransientProviderError backoff_ms=128
01:54:08.630  RETRY_SCHEDULED    call=20 attempt=1 error=TransientProviderError backoff_ms=197
01:54:08.798  RETRY_SCHEDULED    call=10 attempt=2 error=TransientProviderError backoff_ms=325
01:54:08.804  RETRY_SCHEDULED    call=8 attempt=2 error=TransientProviderError backoff_ms=238
01:54:08.808  RETRY_SCHEDULED    call=19 attempt=2 error=TransientProviderError backoff_ms=398
01:54:08.811  RETRY_SCHEDULED    call=6 attempt=2 error=TransientProviderError backoff_ms=385
01:54:08.817  RETRY_SCHEDULED    call=7 attempt=2 error=TransientProviderError backoff_ms=311
01:54:08.826  RETRY_SCHEDULED    call=16 attempt=2 error=TransientProviderError backoff_ms=352
01:54:08.829  RETRY_SCHEDULED    call=14 attempt=2 error=TransientProviderError backoff_ms=341
01:54:08.829  RETRY_SCHEDULED    call=13 attempt=2 error=TransientProviderError backoff_ms=260
01:54:08.834  RETRY_SCHEDULED    call=15 attempt=2 error=TransientProviderError backoff_ms=243
01:54:08.845  RETRY_SCHEDULED    call=9 attempt=2 error=TransientProviderError backoff_ms=313
01:54:08.860  RETRY_SCHEDULED    call=17 attempt=2 error=TransientProviderError backoff_ms=263
01:54:08.863  RETRY_SCHEDULED    call=18 attempt=2 error=TransientProviderError backoff_ms=260
01:54:08.872  RETRY_SCHEDULED    call=11 attempt=2 error=TransientProviderError backoff_ms=262
01:54:08.875  RETRY_SCHEDULED    call=12 attempt=2 error=TransientProviderError backoff_ms=304
01:54:08.877  RETRY_SCHEDULED    call=20 attempt=2 error=TransientProviderError backoff_ms=388
01:54:09.093  RETRIES_EXHAUSTED  call=8 attempts=3 error=TransientProviderError
01:54:09.093  FALLBACK_USED      candidates=4 reason=TransientProviderError
01:54:09.128  RETRIES_EXHAUSTED  call=15 attempts=3 error=TransientProviderError
01:54:09.128  FALLBACK_USED      candidates=4 reason=TransientProviderError
01:54:09.140  RETRIES_EXHAUSTED  call=13 attempts=3 error=TransientProviderError
01:54:09.140  CIRCUIT_OPENED     breaker=claude consecutive_failures=3 threshold=3 error=TransientProviderError
01:54:09.140  FALLBACK_USED      candidates=4 reason=TransientProviderError
01:54:09.173  RETRIES_EXHAUSTED  call=18 attempts=3 error=TransientProviderError
01:54:09.173  FALLBACK_USED      candidates=3 reason=TransientProviderError
01:54:09.175  RETRIES_EXHAUSTED  call=17 attempts=3 error=TransientProviderError
01:54:09.175  FALLBACK_USED      candidates=7 reason=TransientProviderError
01:54:09.177  RETRIES_EXHAUSTED  call=10 attempts=3 error=TransientProviderError
01:54:09.177  FALLBACK_USED      candidates=4 reason=TransientProviderError
01:54:09.180  RETRIES_EXHAUSTED  call=7 attempts=3 error=TransientProviderError
01:54:09.180  FALLBACK_USED      candidates=5 reason=TransientProviderError
01:54:09.184  RETRIES_EXHAUSTED  call=11 attempts=3 error=TransientProviderError
01:54:09.184  FALLBACK_USED      candidates=4 reason=TransientProviderError
01:54:09.209  RETRIES_EXHAUSTED  call=9 attempts=3 error=TransientProviderError
01:54:09.209  FALLBACK_USED      candidates=5 reason=TransientProviderError
01:54:09.221  RETRIES_EXHAUSTED  call=14 attempts=3 error=TransientProviderError
01:54:09.221  FALLBACK_USED      candidates=1 reason=TransientProviderError
01:54:09.229  RETRIES_EXHAUSTED  call=16 attempts=3 error=TransientProviderError
01:54:09.229  FALLBACK_USED      candidates=2 reason=TransientProviderError
01:54:09.231  RETRIES_EXHAUSTED  call=12 attempts=3 error=TransientProviderError
01:54:09.231  FALLBACK_USED      candidates=6 reason=TransientProviderError
01:54:09.246  RETRIES_EXHAUSTED  call=6 attempts=3 error=TransientProviderError
01:54:09.246  FALLBACK_USED      candidates=2 reason=TransientProviderError
01:54:09.256  RETRIES_EXHAUSTED  call=19 attempts=3 error=TransientProviderError
01:54:09.256  FALLBACK_USED      candidates=4 reason=TransientProviderError
01:54:09.316  RETRIES_EXHAUSTED  call=20 attempts=3 error=TransientProviderError
01:54:09.316  FALLBACK_USED      candidates=3 reason=TransientProviderError
01:54:10.439  RETRY_ABSORBED     call=5 attempts=2
01:54:10.564  RETRY_ABSORBED     call=3 attempts=2
01:54:10.605  RETRY_ABSORBED     call=2 attempts=2
01:54:10.899  RETRY_ABSORBED     call=1 attempts=2
01:54:12.084  RETRY_ABSORBED     call=4 attempts=2
01:54:12.103  CIRCUIT_REJECTED   call=21 breaker=claude
01:54:12.103  FALLBACK_USED      candidates=5 reason=CircuitOpenError
01:54:17.316  CIRCUIT_HALF_OPEN  breaker=claude after_s=8.18
01:54:19.434  CIRCUIT_CLOSED     breaker=claude reason=probe succeeded
```
