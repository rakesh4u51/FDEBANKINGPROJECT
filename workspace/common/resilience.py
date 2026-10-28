"""
common.resilience — retries + circuit breaker around the Claude call.

Design intent:
- Transient provider faults (429 / 5xx / timeouts / dropped connections) are
  absorbed by retry_call(): bounded retries with exponential backoff + jitter.
  A call that succeeds after a retry is logged as RETRY_ABSORBED.
- Sustained failure trips the CircuitBreaker: once `failure_threshold`
  consecutive calls have failed *after* exhausting their retries, it OPENS
  (CIRCUIT_OPENED) and rejects further calls fast (CIRCUIT_REJECTED), so 20
  worker threads stop hammering a dead provider and the engine degrades to the
  rule fallback instead of stalling.
- After `recovery_timeout_s` the breaker goes HALF_OPEN and admits one probe;
  success CLOSES it (CIRCUIT_CLOSED), failure re-OPENS it.
- Every retry / state change is recorded as a structured event in EVENTS and
  can be written to reports/resilience_events.jsonl as evidence.

The breaker counts failed *calls*, not failed attempts: a blip that a retry
absorbs never moves the breaker, only failure that survives retries does.
"""

from __future__ import annotations

import itertools
import json
import random
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

import anthropic

T = TypeVar("T")

CLOSED, OPEN, HALF_OPEN = "CLOSED", "OPEN", "HALF_OPEN"
RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}


class TransientProviderError(ConnectionError):
    """Injected fault — stands in for a 429/503/timeout from the provider."""


class CircuitOpenError(RuntimeError):
    """Raised instead of calling the provider while the breaker is OPEN."""


class EventLog:
    """Thread-safe structured event log for retries and breaker transitions."""

    def __init__(self, echo: bool = True):
        self.echo = echo
        self._events: list[dict] = []
        self._lock = threading.Lock()

    def record(self, event: str, **fields) -> None:
        row = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
               "event": event, **fields}
        with self._lock:
            self._events.append(row)
        if self.echo:
            detail = " ".join(f"{k}={v}" for k, v in fields.items())
            print(f"[resilience] {event:<18} {detail}", flush=True)

    def events(self) -> list[dict]:
        with self._lock:
            return list(self._events)

    def counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self.events():
            counts[row["event"]] = counts.get(row["event"], 0) + 1
        return counts

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def write_jsonl(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in self.events()), encoding="utf-8")
        return path


EVENTS = EventLog()


class CircuitBreaker:
    """Consecutive-failure circuit breaker, shared by all worker threads."""

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout_s: float = 5.0,
                 events: EventLog = EVENTS, clock: Callable[[], float] = time.monotonic):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.events = events
        self.clock = clock
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._state = CLOSED
            self._failures = 0
            self._opened_at = 0.0
            self._probe_in_flight = False

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def allow(self) -> bool:
        """True if a call may go to the provider right now."""
        with self._lock:
            if self._state == OPEN and self.clock() - self._opened_at >= self.recovery_timeout_s:
                self._state = HALF_OPEN
                self._probe_in_flight = False
                self.events.record("CIRCUIT_HALF_OPEN", breaker=self.name,
                                   after_s=round(self.clock() - self._opened_at, 2))
            if self._state == CLOSED:
                return True
            if self._state == HALF_OPEN and not self._probe_in_flight:
                self._probe_in_flight = True  # admit exactly one probe
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            if self._state == HALF_OPEN:
                self._state, self._failures, self._probe_in_flight = CLOSED, 0, False
                self.events.record("CIRCUIT_CLOSED", breaker=self.name, reason="probe succeeded")
            elif self._state == CLOSED:
                self._failures = 0
            # OPEN: late success from a call admitted before the trip — ignore.

    def record_failure(self, error: str = "") -> None:
        with self._lock:
            if self._state == HALF_OPEN:
                self._state, self._opened_at, self._probe_in_flight = OPEN, self.clock(), False
                self.events.record("CIRCUIT_OPENED", breaker=self.name, reason="probe failed", error=error)
            elif self._state == CLOSED:
                self._failures += 1
                if self._failures >= self.failure_threshold:
                    self._state, self._opened_at = OPEN, self.clock()
                    self.events.record("CIRCUIT_OPENED", breaker=self.name,
                                       consecutive_failures=self._failures,
                                       threshold=self.failure_threshold, error=error)


def is_retryable(exc: BaseException) -> bool:
    """Transient provider faults worth retrying; auth/validation errors are not."""
    if isinstance(exc, (TransientProviderError, anthropic.APIConnectionError,
                        anthropic.RateLimitError, anthropic.InternalServerError)):
        return True
    return isinstance(exc, anthropic.APIStatusError) and exc.status_code in RETRYABLE_STATUS


_call_ids = itertools.count(1)


def retry_call(fn: Callable[[], T], *, breaker: CircuitBreaker, retries: int = 2,
               base_delay_s: float = 0.2, max_delay_s: float = 2.0,
               retryable: Callable[[BaseException], bool] = is_retryable,
               events: EventLog = EVENTS) -> T:
    """Call `fn` through `breaker`, retrying transient failures with
    exponential backoff + jitter. Raises CircuitOpenError if the breaker is
    OPEN, or the last error once retries are exhausted."""
    call_id = next(_call_ids)
    if not breaker.allow():
        events.record("CIRCUIT_REJECTED", call=call_id, breaker=breaker.name)
        raise CircuitOpenError(f"{breaker.name} circuit is open")

    attempt = 0
    while True:
        attempt += 1
        try:
            result = fn()
        except Exception as exc:
            error = type(exc).__name__
            if not retryable(exc) or attempt > retries:
                if retryable(exc):
                    events.record("RETRIES_EXHAUSTED", call=call_id, attempts=attempt, error=error)
                breaker.record_failure(error)
                raise
            if breaker.state == OPEN:  # tripped by other workers mid-retry: stop hammering
                events.record("CIRCUIT_REJECTED", call=call_id, breaker=breaker.name, attempt=attempt + 1)
                raise CircuitOpenError(f"{breaker.name} circuit is open") from exc
            delay = min(max_delay_s, base_delay_s * 2 ** (attempt - 1)) * random.uniform(0.5, 1.0)
            events.record("RETRY_SCHEDULED", call=call_id, attempt=attempt, error=error,
                          backoff_ms=round(delay * 1000))
            time.sleep(delay)
            continue
        breaker.record_success()
        if attempt > 1:
            events.record("RETRY_ABSORBED", call=call_id, attempts=attempt)
        return result


class FaultInjector:
    """Deterministic chaos for the resilience drill.

    The first `flaky_calls` calls fail on their first attempt only (a blip the
    retry absorbs). The next `outage_calls` calls hit a sustained outage and
    fail on every attempt. Calls after that are healthy (provider recovered).
    """

    def __init__(self, flaky_calls: int = 5, outage_calls: int = 15):
        self.flaky_calls = flaky_calls
        self.outage_calls = outage_calls
        self._calls = itertools.count(1)
        self._lock = threading.Lock()

    def next_call(self) -> Callable[[], None]:
        """Return a hook to run before each attempt of one logical call."""
        with self._lock:
            n = next(self._calls)
        attempts = itertools.count(1)

        def before_attempt() -> None:
            attempt = next(attempts)
            if n <= self.flaky_calls and attempt == 1:
                raise TransientProviderError("injected 503 (transient blip)")
            if self.flaky_calls < n <= self.flaky_calls + self.outage_calls:
                time.sleep(0.05)  # a dead provider still costs a round-trip
                raise TransientProviderError("injected 503 (provider outage)")

        return before_attempt


if __name__ == "__main__":
    # Self-test: full lifecycle against a fake provider (no LLM call).
    breaker = CircuitBreaker("selftest", failure_threshold=3, recovery_timeout_s=0.5)
    faults = FaultInjector(flaky_calls=2, outage_calls=3)

    def fake_call() -> str:
        hook = faults.next_call()
        return retry_call(lambda: (hook(), "ok")[1], breaker=breaker, base_delay_s=0.02)

    for _ in range(6):
        try:
            fake_call()
        except (TransientProviderError, CircuitOpenError):
            pass
    time.sleep(0.6)
    fake_call()  # half-open probe -> provider healthy -> CLOSED
    counts = EVENTS.counts()
    print("counts:", counts)
    print("lifecycle ok:", all(counts.get(e) for e in
          ("RETRY_ABSORBED", "CIRCUIT_OPENED", "CIRCUIT_REJECTED", "CIRCUIT_HALF_OPEN", "CIRCUIT_CLOSED")))
