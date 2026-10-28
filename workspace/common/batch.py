"""
common.batch — batch transaction processing for throughput (Activity 1).

Implemented in Activity 1. Reference pattern:
starter_files/resources/pattern_reference.py.

Design intent:
- The engine must process 1,000 transactions without blocking on each one
  in turn — chunk the feed and process chunks concurrently.
- chunk_transactions splits the full feed into fixed-size batches.
- process_in_batches runs `worker_fn` over every batch using a thread pool
  (I/O-bound work — pattern matching calls an LLM, so threads are the right
  concurrency primitive, not processes) and flattens the results back into
  one list in original order.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterator


def chunk_transactions(transactions: list[dict], batch_size: int = 25) -> Iterator[list[dict]]:
    """Yield successive `batch_size`-sized chunks of `transactions`.

    The last chunk may be smaller than batch_size. Must not drop or duplicate
    any transaction.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    for i in range(0, len(transactions), batch_size):
        yield transactions[i : i + batch_size]


def process_in_batches(
    transactions: list[dict],
    worker_fn: Callable[[list[dict]], list[dict]],
    batch_size: int = 25,
    max_workers: int = 8,
) -> list[dict]:
    """Run `worker_fn` over every batch concurrently and flatten the results.

    - Use chunk_transactions() to build the batches.
    - Use ThreadPoolExecutor(max_workers=max_workers) to run worker_fn on each
      batch concurrently.
    - Preserve overall transaction order in the returned list (submit in order,
      then extend results in the same order you submitted).
    """
    batches = list(chunk_transactions(transactions, batch_size))
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(worker_fn, batch) for batch in batches]
        for future in futures:
            results.extend(future.result())
    return results


if __name__ == "__main__":
    demo = [{"txn_id": f"TXN-{i:03d}"} for i in range(7)]
    batches = list(chunk_transactions(demo, batch_size=3))
    print(f"{len(batches)} batches:", [len(b) for b in batches])
