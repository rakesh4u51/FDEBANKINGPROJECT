"""
common.patterns — ML-style fraud pattern matching using Claude (Activity 2).

STUB: implement the three functions during Activity 2.

Design intent — keep it fast AND accurate:
- prefilter_candidates() is a cheap, deterministic rule pass over ALL
  transactions (no LLM call). It flags anything worth a closer look:
  high amount, odd hour, high-risk merchant, unfamiliar device.
- classify_with_claude() is the expensive step. It only ever receives the
  pre-filtered candidates (a small fraction of the 1,000), sends them to
  Claude as one structured batch prompt, and parses back a fraud_score
  (0-100) and a list of matched pattern codes per transaction.
- detect_fraud_signals() is the entry point the engine calls: run the
  prefilter, classify only the candidates, and merge scores back onto the
  full transaction list (score 0 / no patterns for anything not flagged).

Pattern taxonomy (use these codes, matches PROMPT_LIBRARY.md and the
reference implementation):
    VELOCITY_ABUSE   — many transactions on one account in a short span
    AMOUNT_ANOMALY   — amount far above the account's/category's norm
    ODD_HOUR         — transaction outside typical active hours
    NEW_DEVICE       — device/channel not seen before on this account
    MERCHANT_RISK    — high-risk merchant category (jewellery, electronics, wallet_topup)
    GEO_MISMATCH     — location inconsistent with recent activity
"""

from __future__ import annotations

import json

from llm_client import get_llm_client, resolve_model

PATTERN_CODES = (
    "VELOCITY_ABUSE", "AMOUNT_ANOMALY", "ODD_HOUR",
    "NEW_DEVICE", "MERCHANT_RISK", "GEO_MISMATCH",
)

HIGH_RISK_MERCHANTS = {"jewellery", "electronics", "wallet_topup"}
AMOUNT_THRESHOLD_INR = 100_000
ODD_HOURS = {0, 1, 2, 3, 4, 23}
HIGH_RISK_MERCHANT_MIN_AMOUNT_INR = 40_000

CLASSIFY_SYSTEM_PROMPT = f"""You are a BFSI fraud-analysis model. Given a JSON array of
candidate bank transactions, return ONLY a JSON array (no prose) where each element is:
{{"txn_id": "...", "fraud_score": <0-100 int>, "matched_patterns": [subset of {list(PATTERN_CODES)}]}}
Score conservatively: only flag patterns that are actually evidenced by the fields given."""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text.strip("`")
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    start, end = text.find("["), text.rfind("]")
    return text[start : end + 1] if start != -1 and end > start else text


def _rule_hits(txn: dict) -> list[str]:
    """Pattern codes the cheap rules can evidence on their own."""
    hits = []
    amount = txn.get("amount_inr", 0)
    if amount > AMOUNT_THRESHOLD_INR:
        hits.append("AMOUNT_ANOMALY")
    if txn.get("hour_of_day") in ODD_HOURS:
        hits.append("ODD_HOUR")
    if txn.get("merchant_category") in HIGH_RISK_MERCHANTS and amount > HIGH_RISK_MERCHANT_MIN_AMOUNT_INR:
        hits.append("MERCHANT_RISK")
    if "NEW" in str(txn.get("device_id", "")):
        hits.append("NEW_DEVICE")
    return hits


def _rule_fallback(txn: dict) -> dict:
    """Fail-safe score when Claude is unavailable or omits a candidate."""
    hits = _rule_hits(txn)
    return {"fraud_score": min(100, 25 * len(hits)), "matched_patterns": hits}


def prefilter_candidates(transactions: list[dict]) -> list[dict]:
    """Cheap rule pass over ALL transactions — no LLM call. Return the subset
    worth sending to Claude: high amount, odd hour, or high-risk merchant,
    or a device_id containing 'NEW'.
    """
    return [
        t for t in transactions
        if (
            t.get("amount_inr", 0) > AMOUNT_THRESHOLD_INR
            or t.get("hour_of_day") in ODD_HOURS
            or (
                t.get("merchant_category") in HIGH_RISK_MERCHANTS
                and t.get("amount_inr", 0) > HIGH_RISK_MERCHANT_MIN_AMOUNT_INR
            )
            or "NEW" in str(t.get("device_id", ""))
        )
    ]


def classify_with_claude(candidates: list[dict], model: str = "claude-haiku-4-5") -> dict[str, dict]:
    """Send `candidates` (already pre-filtered) to Claude in one batch prompt.

    Return {txn_id: {"fraud_score": int, "matched_patterns": [str, ...]}}.
    Parse the model's JSON response defensively — strip markdown code fences
    if present, and skip/ignore any entry that doesn't parse.
    """
    if not candidates:
        return {}

    payload = json.dumps([
        {k: t.get(k) for k in ("txn_id", "amount_inr", "merchant_category", "channel", "city", "device_id", "hour_of_day")}
        for t in candidates
    ])

    client = get_llm_client().with_options(max_retries=0)
    response = client.messages.create(
        model=resolve_model(model),
        max_tokens=max(512, 120 * len(candidates)),
        system=CLASSIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": payload}],
    )

    text = "".join(getattr(block, "text", "") for block in response.content)
    try:
        parsed = json.loads(_strip_fences(text))
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, list):
        return {}

    candidate_ids = {t["txn_id"] for t in candidates}
    out: dict[str, dict] = {}
    for row in parsed:
        if not isinstance(row, dict):
            continue
        txn_id = row.get("txn_id")
        if txn_id not in candidate_ids:
            continue
        try:
            score = max(0, min(100, int(row.get("fraud_score", 0))))
        except (TypeError, ValueError):
            continue
        patterns = [p for p in row.get("matched_patterns") or [] if p in PATTERN_CODES]
        out[txn_id] = {"fraud_score": score, "matched_patterns": patterns}
    return out


def detect_fraud_signals(transactions: list[dict]) -> list[dict]:
    """Entry point: prefilter, classify only the candidates, merge scores back
    onto the full transaction list. Every transaction gets fraud_score (int,
    default 0) and matched_patterns (list, default []) added.
    """
    candidates = prefilter_candidates(transactions)
    try:
        scores = classify_with_claude(candidates)
    except Exception:
        scores = {}

    for t in candidates:
        scores.setdefault(t["txn_id"], _rule_fallback(t))

    out = []
    for t in transactions:
        row = dict(t)
        hit = scores.get(t["txn_id"], {"fraud_score": 0, "matched_patterns": []})
        row["fraud_score"] = int(hit["fraud_score"])
        row["matched_patterns"] = list(hit["matched_patterns"])
        out.append(row)
    return out


if __name__ == "__main__":
    from common.generator import generate_transactions

    sample = generate_transactions(count=20, seed=7)
    candidates = prefilter_candidates(sample)
    print(f"{len(candidates)}/{len(sample)} flagged for Claude review")
