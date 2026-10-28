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

CLASSIFY_SYSTEM_PROMPT = f"""You are a BFSI fraud-analysis model. Given a JSON array of
candidate bank transactions, return ONLY a JSON array (no prose) where each element is:
{{"txn_id": "...", "fraud_score": <0-100 int>, "matched_patterns": [subset of {list(PATTERN_CODES)}]}}
Score conservatively: only flag patterns that are actually evidenced by the fields given."""


def prefilter_candidates(transactions: list[dict]) -> list[dict]:
    """Cheap rule pass over ALL transactions — no LLM call. Return the subset
    worth sending to Claude: high amount, odd hour, or high-risk merchant,
    or a device_id containing 'NEW'.
    """
    # TODO(P4): filter using AMOUNT_THRESHOLD_INR, ODD_HOURS, HIGH_RISK_MERCHANTS,
    #           and "NEW" in device_id. Return the matching transactions.
    raise NotImplementedError("Activity 2: implement prefilter_candidates()")


def classify_with_claude(candidates: list[dict], model: str = "claude-haiku-4-5") -> dict[str, dict]:
    """Send `candidates` (already pre-filtered) to Claude in one batch prompt.

    Return {txn_id: {"fraud_score": int, "matched_patterns": [str, ...]}}.
    Parse the model's JSON response defensively — strip markdown code fences
    if present, and skip/ignore any entry that doesn't parse.
    """
    # TODO(P4): build the user message from `candidates`, call
    #           get_llm_client().messages.create(model=resolve_model(model), ...),
    #           parse the JSON array response into the return shape above.
    raise NotImplementedError("Activity 2: implement classify_with_claude()")


def detect_fraud_signals(transactions: list[dict]) -> list[dict]:
    """Entry point: prefilter, classify only the candidates, merge scores back
    onto the full transaction list. Every transaction gets fraud_score (int,
    default 0) and matched_patterns (list, default []) added.
    """
    # TODO(P4): candidates = prefilter_candidates(transactions);
    #           scores = classify_with_claude(candidates);
    #           annotate every transaction (default score 0 / [] if not a candidate).
    raise NotImplementedError("Activity 2: implement detect_fraud_signals()")


if __name__ == "__main__":
    from common.generator import generate_transactions

    sample = generate_transactions(count=20, seed=7)
    candidates = prefilter_candidates(sample)
    print(f"{len(candidates)}/{len(sample)} flagged for Claude review")
