"""
Reference implementation — Project 4 fraud engine controls.

Not imported by the engine. Read this alongside PROMPT_LIBRARY.md if you get
stuck on an activity; the shape here is what each stub's docstring expects,
but naming/order of internal helpers is yours to change.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterator

# ---------------------------------------------------------------------------
# Activity 1 — common/batch.py
# ---------------------------------------------------------------------------


def chunk_transactions_ref(transactions: list[dict], batch_size: int = 25) -> Iterator[list[dict]]:
    for i in range(0, len(transactions), batch_size):
        yield transactions[i : i + batch_size]


def process_in_batches_ref(
    transactions: list[dict],
    worker_fn: Callable[[list[dict]], list[dict]],
    batch_size: int = 25,
    max_workers: int = 8,
) -> list[dict]:
    batches = list(chunk_transactions_ref(transactions, batch_size))
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(worker_fn, batch) for batch in batches]
        for future in futures:
            results.extend(future.result())
    return results


# ---------------------------------------------------------------------------
# Activity 2 — common/patterns.py
# ---------------------------------------------------------------------------

AMOUNT_THRESHOLD_INR = 100_000
ODD_HOURS = {0, 1, 2, 3, 4, 23}
HIGH_RISK_MERCHANTS = {"jewellery", "electronics", "wallet_topup"}


def prefilter_candidates_ref(transactions: list[dict]) -> list[dict]:
    return [
        t for t in transactions
        if t["amount_inr"] > AMOUNT_THRESHOLD_INR
        or t["hour_of_day"] in ODD_HOURS
        or t["merchant_category"] in HIGH_RISK_MERCHANTS
        or "NEW" in t.get("device_id", "")
    ]


def classify_with_claude_ref(candidates: list[dict], client, model: str) -> dict[str, dict]:
    if not candidates:
        return {}
    payload = json.dumps([
        {k: t[k] for k in (
            "txn_id", "amount_inr", "merchant_category", "channel",
            "city", "device_id", "hour_of_day",
        )} for t in candidates
    ])
    response = client.messages.create(
        model=model,
        max_tokens=2000,
        system="... CLASSIFY_SYSTEM_PROMPT from common/patterns.py ...",
        messages=[{"role": "user", "content": payload}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    out: dict[str, dict] = {}
    for row in parsed:
        txn_id = row.get("txn_id")
        if not txn_id:
            continue
        out[txn_id] = {
            "fraud_score": int(row.get("fraud_score", 0)),
            "matched_patterns": list(row.get("matched_patterns", [])),
        }
    return out


def detect_fraud_signals_ref(transactions: list[dict], classify_fn) -> list[dict]:
    candidates = prefilter_candidates_ref(transactions)
    scores = classify_fn(candidates)
    out = []
    for t in transactions:
        row = dict(t)
        hit = scores.get(t["txn_id"], {"fraud_score": 0, "matched_patterns": []})
        row["fraud_score"] = hit["fraud_score"]
        row["matched_patterns"] = hit["matched_patterns"]
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Activity 3 — common/risk.py
# ---------------------------------------------------------------------------

HIGH_THRESHOLD = 70
MEDIUM_THRESHOLD = 40


def assign_risk_tier_ref(fraud_score: int, matched_patterns: list[str]) -> str:
    if fraud_score >= HIGH_THRESHOLD or len(matched_patterns) >= 2:
        return "HIGH"
    if fraud_score >= MEDIUM_THRESHOLD or len(matched_patterns) == 1:
        return "MEDIUM"
    return "LOW"


def prioritize_queue_ref(scored_transactions: list[dict]) -> dict:
    tiers: dict[str, list[dict]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for t in scored_transactions:
        tier = assign_risk_tier_ref(t["fraud_score"], t["matched_patterns"])
        tiers[tier].append(t)
    tiers["HIGH"].sort(key=lambda t: t["fraud_score"], reverse=True)
    return {
        **tiers,
        "counts": {k: len(v) for k, v in tiers.items()},
    }


# ---------------------------------------------------------------------------
# Activity 5 — common/reporting.py
# ---------------------------------------------------------------------------


def generate_daily_summary_ref(prioritized: dict, benchmark: dict) -> dict:
    from collections import Counter

    pattern_counts: Counter = Counter()
    for t in prioritized["HIGH"] + prioritized["MEDIUM"]:
        pattern_counts.update(t.get("matched_patterns", []))

    amount_at_risk = sum(t["amount_inr"] for t in prioritized["HIGH"])
    total = sum(prioritized["counts"].values())

    return {
        "total_transactions": total,
        "tier_counts": prioritized["counts"],
        "top_patterns": pattern_counts.most_common(),
        "amount_at_risk_inr": amount_at_risk,
        "benchmark": benchmark,
    }
